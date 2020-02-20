"""
A GameState is an immutable object that keeps track of a single frozen
point in time during a game. All operations (drawing a card, casting a
spell, playing a land) are handled by creating new objects. By using the
GameState.next_states and GameState.next_turn, we iterate through all
possible sequences of plays until we find a winning line.

GameStates (plural) is a set of GameState objects. It forwards method
calls to its members and collects their results -- in general, you don't
have to worry about whether you're working with an individual GameState
or a set of them. By virtue of being a set, the GameStates container
also automatically collapses duplicate game states to cut down on wasted
computation time.
"""

import collections
import itertools
import time

from .mana import Mana
from .card import Card, Cards

# ======================================================================

# Most of the hands that don't converge at 2e5 states also don't
# converge at 5e5 states. How much time do you want to burn trying?
MAX_STATES = 1e5
N_STATES = 0
START_TIME = None


class TooManyStates(Exception):
    pass


class GameStates(set):
    """A set of GameState objects. Passes method calls on to its
    elements and aggregates the results.
    """

    def __getattr__(self, attr):
        def func(*args, **kwargs):
            new_states = GameStates()
            for state in self:
                new_states |= getattr(state, attr)(*args, **kwargs)
            return new_states
        return func

    def safe_getattr(self, attr):
        if not all(hasattr(x, attr) for x in self):
            return self
        return getattr(self, attr)()

    def report(self):
        if len(self) == 1:
            for state in self:
                return state.report()
        # If we have a ton of states but did not converge, let's take a
        # look at the longest one I guess? The most actions to evaluate.
        else:
            longest_state = max(self, key=len)
            return longest_state.report() + f"\nFailed to converge after {N_STATES} states"

    @property
    def performance(self):
        for state in self:
            return state.performance

    @property
    def done(self):
        for state in self:
            return state.turn

    @property
    def notes(self):
        for state in states:
            return state.notes

    @property
    def turn(self):
        for state in self:
            return state.turn

    def next_turn(self):
        next_states = GameStates()
        done_states = GameStates()
        for state in self:
            for _state in state.next_turn():
                # If we find a line that gives us a hasty titan, short-circuit
                # the rest.
                if _state.fast and _state.done:
                    return GameStates([_state])
                # If we find a line that gets there, but without haste, hold
                # out for a better solution.
                elif _state.done:
                    done_states.add(state)
                else:
                    next_states.add(_state)
                # In the event of an overflow, bail. If we've got a solution,
                # report it. Otherwise, dump the longest state we have. That
                # might give us a sense for what's problematic.
                if N_STATES > MAX_STATES:
                    if done_states:
                        return min(done_states, key=len)
                    else:
                        max(next_states, key=len).report()
                        raise TooManyStates
        # In the event of multiple matches, go for the one with the fewest
        # steps -- avoid casting unnecessary Pacts, for example.
        if done_states:
            return min(done_states, key=len)
        else:
            return next_states

    @property
    def summary(self):
        if len(self) != 1:
            raise TypeError("Can only summarize a single state, not %d" % len(self))
        for state in self:
            return state.summary


# ======================================================================


GAME_STATE_DEFAULTS = {
    # No need to distinguish tapped from untapped since we tap
    # everything immediately
    "battlefield": (),
    "deck_list": (),
    "deck_index": 0,
    "done": False,
    "fast": False,
    "hand": (),
    "mana_debt": Mana(),
    "mana_pool": Mana(),
    "notes": "",
    "on_the_play": 0,
    "overflowed": 0,
    "land_drops": 0,
    "spells_cast": 0,
    "suspended": (),
    "turn": 0,
}


FIELDS = sorted(GAME_STATE_DEFAULTS.keys())


GameStateBase = collections.namedtuple("GameStateBase", " ".join(FIELDS))


class GameState(GameStateBase):

    def __new__(cls, reset_clock=False, **kwargs):
        global N_STATES, START_TIME
        if reset_clock:
            N_STATES = 0
            START_TIME = time.time()
        else:
            N_STATES += 1
        new_kwargs = GAME_STATE_DEFAULTS.copy()
        new_kwargs.update(kwargs)
        for key in ("hand", "deck_list", "battlefield"):
            if not isinstance(new_kwargs[key], Cards):
                new_kwargs[key] = Cards(new_kwargs[key])
        values = [v for k, v in sorted(new_kwargs.items())]
        return GameStateBase.__new__(cls, *values)

    def __hash__(self):
        """Ignore notes when collapsing duplicates."""
        fields = []
        for i, fieldname in enumerate(FIELDS):
            if fieldname in ("notes", "deck_list"):
                continue
            fields.append(self[i])
        return tuple.__hash__(tuple(fields))

    def __eq__(self, other):
        """Ignore notes when collapsing duplicates."""
        for i, fieldname in enumerate(FIELDS):
            if fieldname in ("notes", "deck_list"):
                continue
            if self[i] != other[i]:
                return False
        return True

    def __len__(self):
        return self.notes.count("\n")

    def clone(self, **kwargs):
        new_kwargs = self._asdict()
        new_kwargs.update(kwargs)
        return GameStates([GameState(**new_kwargs)])

    def next_states(self):
        if self.done:
            return GameStates([self])
        states = self.pass_turn()
        for card in set(self.hand.lands()):
            states |= self.play(card)
        for card in set(self.hand):
            states |= self.cast(card)
            states |= self.cycle(card)
        for card in set(self.battlefield):
            states |= self.sacrifice(card)
        return states

    def next_turn(self):
        old_states, new_states = GameStates([self]), GameStates()
        while old_states:
            for state in old_states.pop().next_states():
                if state.done:
                    return GameStates([state])
                elif state.turn > self.turn:
                    new_states.add(state)
                else:
                    old_states.add(state)
        return new_states

    def overflow(self):
        return self.clone(overflowed=1, done=1)

    @property
    def performance(self):
        dt = time.time() - START_TIME
        return "%4.0fk states / %3.0f s = %4.0fk states/s" % (
            N_STATES/1000,
            dt,
            N_STATES/1000/dt,
        )

    def report(self):
        return self.notes.lstrip(", \n")

    @property
    def summary(self):
        """Generate CSV output to show what turn we went off, whether we
        were on the play, and whether it's a "fast" win via Amulet or
        Breach. For hands that don't converge, also show whether or not
        it overflowed.
        """
        return f"{self.turn},{self.on_the_play},{int(self.fast)},{self.overflowed}"

    # ------------------------------------------------------------------

    def add_mana(self, m, note=""):
        pool = self.mana_pool + m
        note += f", {pool} in pool"
        return self.clone(
            mana_pool=pool,
            notes=self.notes + note
        )

    def bounce_land(self):
        states = GameStates()
        # For fetching and cantrips, some lands are better than others.
        # Choices for what to bounce are trickier.
        for card in self.battlefield.lands():
            states |= self.clone(
                notes=self.notes + f", bounce {card}",
                battlefield=self.battlefield - card,
                hand=self.hand + card,
            )
        return states

    def cast(self, card):
        cost = card.cost
        if card not in self.hand or cost is None or not self.mana_pool >= cost:
            return GameStates()
        states = self.clone(
            hand=self.hand - card,
            notes=self.notes + f"\ncast {card}",
            spells_cast=self.spells_cast + 1,
        ).pay(cost)
        # Don't use the safety wrapper. If casting is a no-op, we
        # shouldn't be casting. And something is probably wrong.
        return getattr(states, "cast_" + card.slug)()

    def cast_from_suspend(self, card):
        states = self.clone(
            notes=self.notes + f", cast {card} from suspend",
            spells_cast=self.spells_cast + 1,
        )
        return getattr(states, "cast_" + card.slug)()

    def cycle(self, card):
        cost = card.cycle_cost
        if card not in self.hand or cost is None or not self.mana_pool >= cost:
            return GameStates()
        states = self.clone(
            hand=self.hand - card,
            notes=self.notes + f"\n{card.cycle_verb} {card}",
        ).pay(cost)
        return states.safe_getattr("cycle_" + card.slug)

    def draw(self, n):
        return self.clone(
            deck_index=self.deck_index + n,
            hand=self.hand + self.top(n),
            notes=self.notes + f", draw {self.top(n)}",
        )

    def fetch(self, card, tapped=None):
        card = Card(card)
        state = self.clone(
            notes=self.notes + f", fetch {card}",
            battlefield=self.battlefield,
            hand=self.hand + card,
        )
        if tapped or card.enters_tapped:
            return state.play_tapped(card)
        else:
            return state.play_untapped(card)

    def grab(self, card):
        return self.clone(
            hand=self.hand + card,
            notes=self.notes + f", grab {card}",
        )

    def grabs(self, cards):
        states = GameStates()
        for card in cards:
            states |= self.note(f", considering {cards}").grab(card)
        return states

    def mill(self, n):
        return self.clone(
            deck_index=self.deck_index + n,
            notes=self.notes + f", mill {self.top(n)}",
        )

    def note(self, note):
        return self.clone(
            notes=self.notes + note,
        )

    def pass_turn(self):
        # Optimizations go here. If we played a pact on turn 1, bail. If
        # we passed the turn with no lands, bail. And so on.
        if self.turn and not self.battlefield:
            return GameStates()
        if self.turn < 2 and self.mana_debt:
            return GameStates()
        mana_debt = self.mana_debt
        land_drops = (
            1 +
            2*self.battlefield.count("Azusa, Lost but Seeking") +
            self.battlefield.count("Dryad of the Ilysian Grove") +
            self.battlefield.count("Sakura-Tribe Scout")
        )
        states = self.clone(
            land_drops=land_drops,
            mana_debt=Mana(),
            mana_pool=Mana(),
            notes=self.notes + f"\n---- turn {self.turn+1}",
            turn=self.turn+1,
        ).tap_out()
        # Watch out for pre-game actions, like Gemstone Caverns and Chancellor
        # of the Tangle
        if self.turn == 0:
            states = states.pre_game_actions()
        # Handle suspended spells
        states = states.tick_down()
        if mana_debt:
            states = states.pay(mana_debt, note=f", pay {mana_debt} for pact")
        if self.on_the_play and self.turn == 0:
            return states
        else:
            return states.draw(1)

    def pay(self, cost, note=""):
        states = GameStates()
        for m in self.mana_pool.minus(cost):
            states |= self.clone(
                mana_pool=m,
                notes=self.notes + note,
            )
        return states

    def pitch(self, n, options=None):
        """GameStates is a set, so there's already a discard function."""
        if options is None:
            options = self.hand
        states = GameStates()
        for cards in itertools.combinations(options, n):
            states |= self.clone(
                hand=self.hand - cards,
                notes=self.notes + f", discard {Cards(cards)}",
            )
        return states

    def play(self, card, **kwargs):
        if "land" not in card.types:
            raise ValueError(f"cannot play nonland {card} as land")
        if not self.land_drops or not card in self.hand:
            return GameStates()
        states = self.clone(
            notes=self.notes + f"\nplay {card}",
            land_drops=self.land_drops - 1,
        )
        enters_tapped = card.enters_tapped
        if enters_tapped == "check":
            enters_tapped = getattr(self, "check_" + card.slug)()
        if enters_tapped:
            return states.play_tapped(card, **kwargs)
        else:
            return states.play_untapped(card, **kwargs)

    def play_tapped(self, card, note="", **kwargs):
        states = self.clone(
            battlefield=self.battlefield + card,
            hand=self.hand - card,
            notes=self.notes + note,
        )
        for _ in range(self.battlefield.count("Amulet of Vigor")):
            states = states.tap(card, **kwargs)
        return states.safe_getattr("play_" + card.slug)

    def play_untapped(self, card, **kwargs):
        states = self.clone(
            hand=self.hand - card,
            battlefield=self.battlefield + card,
        ).tap(card, **kwargs)
        return states.safe_getattr("play_" + card.slug)

    def pre_game_actions(self):
        # Gemstone Caverns. Keep in mind that exiling nothing is allowed.
        if Card("Gemstone Caverns") in self.hand and not self.on_the_play:
            states = self.note(f", ignore {Card('Gemstone Caverns')}")
            for card in self.hand - "Gemstone Caverns":
                states |= self.clone(
                    hand=self.hand - Cards(["Gemstone Caverns", card]),
                    battlefield=self.battlefield + Card("Gemstone Mine"),
                    notes=self.notes + f", cheat out {Card('Gemstone Caverns')} with {card}",
                )
            return states
        else:
            return self.note(", no pre-game actions")

    def sacrifice(self, card):
        cost = card.sacrifice_cost
        if card not in self.battlefield or cost is None or not self.mana_pool >= cost:
            return GameStates()
        states = self.clone(
            battlefield=self.battlefield - card,
            notes=self.notes + f"\nsacrifice {card}",
        ).pay(cost)
        return getattr(states, "sacrifice_" + card.slug)()

    def scry(self, n):
        if n == 1:
            return self.mill(1) | self.clone(
                notes=self.notes + f", leave {self.top(1)}",
            )
        else:
            raise ValueError("Scrying 2+ cards is not supported")

    def safe_getattr(self, attr):
        try:
            func = getattr(states, "cast_" + card.slug)
        except AttributeError:
            return GameStates([self])
        return func()

    def suspend(self, card, n):
        return self.clone(
            suspended=self.suspended + ((Card(card), n),),
        )

    def tap(self, card, silent=False):
        states = GameStates()
        for m in card.taps_for:
            mana_pool = self.mana_pool + m
            if m and not silent:
                mana_note = f", {mana_pool} in pool" if mana_pool else ""
            else:
                mana_note = ""
            states |= self.clone(
                mana_pool=mana_pool,
                notes=self.notes + mana_note,
            )
        return states or GameStates([self])

    def tap_out(self):
        pools, new_pools = {self.mana_pool}, set()
        for card in self.battlefield:
            if not card.taps_for:
                continue
            for m in card.taps_for:
                new_pools |= {pool+m for pool in pools}
            pools, new_pools = new_pools, set()
        states = GameStates()
        for pool in pools:
            mana_note = f", {pool} in pool" if pool else ""
            states |= self.clone(
                mana_pool=pool,
                notes=self.notes + mana_note,
            )
        return states

    def tick_down(self):
        if not self.suspended:
            return GameStates([self])
        suspended = []
        to_cast = []
        tick_notes = Cards([])
        for card, n in self.suspended:
            if n > 0:
                tick_notes += card
                suspended.append((card, n-1))
            else:
                to_cast.append(card)
        if suspended:
            states = self.clone(
                suspended=tuple(sorted(suspended)),
                notes=self.notes + f", {tick_notes} ticking down",
            )
        else:
            states = self
        for card in to_cast:
            states = states.cast_from_suspend(card)
        return states

    def top(self, n):
        return Cards(self.deck_list[self.deck_index:self.deck_index + n])

    # ------------------------------------------------------------------

    def cast_amulet_of_vigor(self):
        return self.clone(
            battlefield=self.battlefield + "Amulet of Vigor",
            fast=True,
        )

    def cast_ancient_stirrings(self):
        return self.mill(5).grabs(self.top(5).colorless())

    def cast_arboreal_grazer(self):
        states = GameStates()
        for card in self.hand.lands():
            states |= self.play_tapped(card, note=f", play {card}")
        # If we have no lands in hand, there's no reason to cast Grazer.
        return states

    def cast_azusa_lost_but_seeking(self):
        if "Azusa, Lost but Seeking" in self.battlefield:
            return GameStates()
        return self.clone(
            battlefield=self.battlefield + "Azusa, Lost but Seeking",
            land_drops=self.land_drops + 2,
        )

    def cast_bond_of_flourishing(self):
        return self.mill(3).grabs(self.top(3).permanents())

    def cast_dryad_of_the_ilysian_grove(self):
        return self.clone(
            battlefield=self.battlefield + "Dryad of the Ilysian Grove",
            land_drops=self.land_drops + 1,
        )

    def cast_elvish_rejuvenator(self):
        states = GameStates()
        for land in self.top(5).lands():
            states |= self.mill(5).grab(land).play_tapped(land)
        return states

    def cast_explore(self):
        return self.clone(land_drops=self.land_drops+1).draw(1)

    def cast_oath_of_nissa(self):
        return self.mill(3).grabs(self.top(3).creatures_lands())

    def cast_once_upon_a_time(self):
        return self.mill(5).grabs(self.top(5).creatures_lands())

    def cast_opt(self):
        return self.scry(1).draw(1)

    def cast_primeval_titan(self):
        return self.clone(done=True)

    def cast_pyretic_ritual(self):
        return self.add_mana("RRR")

    def cast_sakura_tribe_elder(self):
        return self.fetch("Forest", tapped=True)

    def cast_sakura_tribe_scout(self):
        return self.clone(
            battlefield=self.battlefield + "Sakura-Tribe Scout",
        )

    def cast_search_for_tomorrow(self):
        return self.fetch("Forest")

    def cast_summer_bloom(self):
        return self.clone(land_drops=self.land_drops + 3)

    def cast_summoners_pact(self):
        states = GameStates()
        for card in self.deck_list.green_creatures():
            # You never need to Pact for a card that's in your hand.
            # Even if you need multiple Grazers, you can grab the second
            # after you play the first.
            if card in self.hand:
                continue
            if card == "Azusa, Lost but Seeking" and "Azusa, Lost but Seeking" in self.battlefield:
                continue
            states |= self.grab(card)
        return states.clone(mana_debt=self.mana_debt + "2GG")

    def cast_through_the_breach(self):
        if "Primeval Titan" not in self.hand:
            return GameStates()
        # Add a dummy Amulet of Vigor to the battlefield to indicate a
        # "fast" win
        return self.clone(
            done=True,
            battlefield=self.battlefield + "Amulet of Vigor",
        )

    def cast_trinket_mage(self):
        return self.grabs(self.deck_list.trinkets())

    def check_castle_garenbrig(self):
        if self.battlefield.forests():
            return False
        else:
            return Card("Dryad of the Ilysian Grove") not in self.battlefield

    def cycle_once_upon_a_time(self):
        # Only allowed if this is the first spell we have cast all game.
        if self.spells_cast:
            return GameStates()
        return self.clone(spells_cast=self.spells_cast+1).cast_once_upon_a_time()

    def cycle_search_for_tomorrow(self):
        return self.suspend("Search for Tomorrow", 2)

    def cycle_simian_spirit_guide(self):
        return self.add_mana("R")

    def cycle_tolaria_west(self):
        # Never transmute Tolaria West for another copy of itself.
        return self.grabs(self.deck_list.zeros() - "Tolaria West")

    def cycle_tranquil_thicket(self):
        return self.draw(1)

    def play_boros_garrison(self):
        return self.bounce_land()

    def play_selesnya_sanctuary(self):
        return self.bounce_land()

    def play_simic_growth_chamber(self):
        return self.bounce_land()

    def play_temple_of_mystery(self):
        return self.scry(1)

    def play_zhalfirin_void(self):
        return self.scry(1)

    def sacrifice_castle_garenbrig(self):
        return self.add_mana("GGGGGG")
