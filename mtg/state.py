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

from . import carddata
from . import helpers
from .mana import Mana

# ======================================================================

# Most of the hands that don't converge at 2e5 states also don't
# converge at 5e5 states. How much time do you want to burn trying?
MAX_STATES = 5e5
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
            [x.report() for x in self]
        # If we have a ton of states but did not converge, let's take a
        # look at the longest one I guess? The most actions to evaluate.
        else:
            longest_state = max((len(x.notes), x) for x in self)[-1]
            longest_state.report()
            print("Failed to converge after", N_STATES, "states")

    @property
    def performance(self):
        for state in self:
            return state.performance

    @property
    def done(self):
        for state in self:
            return state.turn

    def uses(self, card):
        """Check if the solution we found uses the given card."""
        if card is None:
            return False
        else:
            for state in self:
                return helpers.pretty(card, color=False) in state.notes

    @property
    def notes(self):
        for state in states:
            return state.notes

    @property
    def turn(self):
        for state in self:
            return state.turn

    def next_turn(self):
        """Short-circuit as soon as we find a line."""
        new_states = GameStates()
        for state in self:
            for _state in state.next_turn():
                if _state.done:
                    return GameStates([_state])
                new_states.add(_state)
                # In the event of an overflow, dump the longest state we
                # have. That might give us a sense for the sorts of
                # things that are problematic.
                if N_STATES > MAX_STATES:
                    max((len(x.notes), x) for x in new_states)[-1].report()
                    raise TooManyStates
        return new_states

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
    "hand": (),
    "mana_debt": Mana(),
    "mana_pool": Mana(),
    "notes": "",
    "on_the_play": 0,
    "overflowed": 0,
    "land_drops": 0,
    "spells_cast": 0,
    "suspend": (),
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
        values = [v for k, v in sorted(new_kwargs.items())]
        return GameStateBase.__new__(cls, *values)

    def __hash__(self):
        """Ignore notes when collapsing duplicates."""
        fields = []
        for i, fieldname in enumerate(FIELDS):
            if fieldname == "notes":
                continue
            fields.append(self[i])
        return tuple.__hash__(tuple(fields))

    def __eq__(self, other):
        """Ignore notes when collapsing duplicates."""
        for i, fieldname in enumerate(FIELDS):
            if fieldname == "notes":
                continue
            if self[i] != other[i]:
                return False
        return True

    def clone(self, **kwargs):
        new_kwargs = self._asdict()
        new_kwargs.update(kwargs)
        return GameStates([GameState(**new_kwargs)])

    def next_states(self):
        if self.done:
            return GameStates([self])
        states = self.pass_turn()
        for card in set(self.hand):
            states |= self.cast(card)
            states |= self.cycle(card)
            states |= self.play(card)
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
    def summary(self):
        """Generate CSV output to show what turn we went off, whether we
        were on the play, and whether it's a "fast" win via Amulet or
        Breach. For hands that don't converge, also show whether or not
        it overflowed.
        """
        fast = 1 if "Amulet of Vigor" in self.battlefield else 0
        return ",".join([
            str(self.turn),
            str(self.on_the_play),
            str(fast),
            str(self.overflowed),
        ])

    @property
    def performance(self):
        dt = time.time() - START_TIME
        return "%4.0fk states / %3.0f s = %4.0fk states/s" % (
            N_STATES/1000,
            dt,
            N_STATES/1000/dt,
        )

    # ------------------------------------------------------------------

    def add_mana(self, m, note=""):
        pool = self.mana_pool + m
        if not note:
            note = ", " + str(pool) + " in pool"
        return self.clone(
            mana_pool=pool,
            notes=self.notes + note
        )

    def bounce_land(self):
        states = GameStates()
        # For fetching and cantrips, some lands are better than others.
        # Choices for what to bounce are trickier.
        for card in carddata.lands(self.battlefield):
            states |= self.clone(
                notes=self.notes + ", bounce " + helpers.pretty(card),
                battlefield=helpers.tup_sub(self.battlefield, card),
                hand=helpers.tup_add(self.hand, card),
            )
        return states

    def cast(self, card):
        cost = carddata.cost(card)
        if card not in self.hand or cost is None or not self.mana_pool >= cost:
            return GameStates()
        states = self.clone(
            hand=helpers.tup_sub(self.hand, card),
            notes=self.notes + "\ncast " + helpers.pretty(card),
            spells_cast=self.spells_cast + 1,
        ).pay(cost)
        # Don't use the safety wrapper. If casting is a no-op, we
        # shouldn't be casting. And something is probably wrong.
        return getattr(states, "cast_" + helpers.slug(card))()

    def cast_from_suspend(self, card):
        states = self.clone(
            notes=self.notes + ", cast " + helpers.pretty(card) + " from suspend",
            spells_cast=self.spells_cast + 1,
        )
        return getattr(states, "cast_" + helpers.slug(card))()

    def check_tron(self):
        tron = {
            "Urza's Mine",
            "Urza's Power Plant",
            "Urza's Tower",
        }
        tron_have = set(self.battlefield) & tron
        tron_need = tron - tron_have
        if len(tron_have) == 3:
            return self.clone(done=True)
        elif len(tron_have) == 2 and self.land_drops and tron_need <= set(self.hand):
            return self.clone(
                done=True,
                battlefield=helpers.tup_add(self.battlefield, "Amulet of Vigor"),
            ).play(tron_need.pop(), silent=True)
        else:
            return GameStates([self])

    def cycle(self, card):
        cost = carddata.cycle_cost(card)
        if card not in self.hand or cost is None or not self.mana_pool >= cost:
            return GameStates()
        verb = carddata.cycle_verb(card)
        states = self.clone(
            hand=helpers.tup_sub(self.hand, card),
            notes=self.notes + "\n" + verb + " " + helpers.pretty(card),
        ).pay(cost)
        return states.safe_getattr("cycle_" + helpers.slug(card))

    def draw(self, n):
        return self.clone(
            deck_index=self.deck_index + n,
            hand=helpers.tup_add(self.hand, *self.top(n)),
            notes=self.notes + ", draw " + helpers.pretty(*self.top(n)),
        )

    def fetch(self, card, sacrifice=None, tapped=None):
        if card not in self.deck_list:
            return GameStates()
        battlefield = self.battlefield
        if sacrifice:
            battlefield = helpers.tup_sub(battlefield, sacrifice)
        state = self.clone(
            notes=self.notes + ", fetch " + helpers.pretty(card),
            battlefield=battlefield,
            hand=helpers.tup_add(self.hand, card),
        )
        if tapped or carddata.enters_tapped(card):
            return state.play_tapped(card)
        else:
            return state.play_untapped(card)

    def grab(self, card=None, mill=0, note=None):
        notes = self.notes
        hand = self.hand
        if mill > 0:
            notes = self.notes + ", mill " + helpers.pretty(*self.top(mill))
        if card:
            hand = helpers.tup_add(self.hand, card)
            notes += ", grab " + helpers.pretty(card)
        if note:
            notes += note
        return self.clone(
            deck_index=self.deck_index + mill,
            hand=hand,
            notes=notes,
        )

    def tron_choices(self, cards):
        # The computer has superhuman "instincts" about the order of the
        # deck. Force it to choose arbitrarily.
        tron = {
            "Urza's Mine",
            "Urza's Power Plant",
            "Urza's Tower",
        }
        tron_have = tron & set(self.battlefield + self.hand)
        non_tron = cards - tron
        tron_options = (set(cards) & tron) - tron_have
        if tron_options:
            return set([sorted(tron_options)[0]]) | non_tron
        else:
            return non_tron

    def grab_from_top(self, card_filter, n, **kwargs):
        states = GameStates()
        if card_filter:
            cards = card_filter(self.top(n), **kwargs)
        else:
            cards = set(self.top(n))
        # The computer has superhuman "instincts" about the order of the
        # deck. Force it to choose arbitrarily.
        for card in self.tron_choices(cards):
            states |= self.grab(card, mill=n)
        return states or self.grab(mill=n, note=", whiff")

    def pass_turn(self):
        # Optimizations go here. If we played a pact on turn 1, bail. If
        # we passed the turn with no lands, bail. And so on.
        if self.turn and not self.battlefield:
            return GameStates()
        if self.turn < 2 and self.mana_debt:
            return GameStates()
        mana_debt = self.mana_debt
        land_drops = 1 + self.battlefield.count("Sakura-Tribe Scout")
        if "Azusa, Lost but Seeking" in self.battlefield:
            land_drops += 2
        states = self.clone(
            land_drops=land_drops,
            mana_debt=Mana(),
            mana_pool=Mana(),
            notes=self.notes + "\n---- turn " + str(self.turn+1),
            turn=self.turn+1,
        ).tap_out()
        # Chancellor of the Tangle
        if self.turn == 0 and "Chancellor of the Tangle" in self.hand:
            chancellors = [x for x in self.hand if x == "Chancellor of the Tangle"]
            states = states.add_mana(
                len(chancellors)*"G",
                note=", reveal " + helpers.pretty(*chancellors),
            )
        # Handle suspended spells
        states = states.tick_down()
        if mana_debt:
            states = states.pay(mana_debt, note=", pay " + str(mana_debt) + " for pact")
        if self.on_the_play and self.turn == 0:
            return states
        else:
            return states.draw(1).check_tron()

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
                hand=helpers.tup_sub(self.hand, *cards),
                notes=self.notes + ", discard " + helpers.pretty(*cards),
            )
        return states

    def play(self, card, **kwargs):
        if not self.land_drops or not carddata.is_land(card) or not card in self.hand:
            return GameStates()
        states = self.clone(
            notes=self.notes + "\nplay " + helpers.pretty(card),
            land_drops=self.land_drops - 1,
        )
        if carddata.enters_tapped(card):
            return states.play_tapped(card, **kwargs)
        else:
            return states.play_untapped(card, **kwargs)

    def play_tapped(self, card, note="", **kwargs):
        states = self.clone(
            battlefield=helpers.tup_add(self.battlefield, card),
            hand=helpers.tup_sub(self.hand, card),
            notes=self.notes + note,
        )
        for _ in range(self.battlefield.count("Amulet of Vigor")):
            states = states.tap(card, **kwargs)
        return states.safe_getattr("play_" + helpers.slug(card))

    def play_untapped(self, card, **kwargs):
        states = self.clone(
            hand=helpers.tup_sub(self.hand, card),
            battlefield=helpers.tup_add(self.battlefield, card),
        ).tap(card, **kwargs)
        return states.safe_getattr("play_" + helpers.slug(card))

    def report(self):
        print(self.notes.lstrip(", \n"))

    def sacrifice(self, card):
        cost = carddata.sacrifice_cost(card)
        if card not in self.battlefield or cost is None or not self.mana_pool >= cost:
            return GameStates()
        states = self.clone(
            battlefield=helpers.tup_sub(self.battlefield, card),
            notes=self.notes + "\nsacrifice " + helpers.pretty(card),
        ).pay(cost)
        return getattr(states, "sacrifice_" + helpers.slug(card))()

    def scry(self, n):
        if n == 1:
            return self.grab(None, mill=1) | self.clone(
                notes=self.notes + ", leave " + helpers.pretty(*self.top(1)),
            )
        elif n == 2:
            states = GameStates()
            before = self.deck_list[:self.deck_index]
            limbo = self.top(2)
            after = self.deck_list[self.deck_index+2:]
            # Top top
            states |= self.clone(
                notes=self.notes + ", leave " + helpers.pretty(*limbo),
            )
            # Bottom top
            states |= self.clone(
                deck_index=self.deck_index+1,
                notes=self.notes + ", mill " + helpers.pretty(limbo[0]) + ", leave " + helpers.pretty(limbo[1]),
            )
            # Bottom bottom
            states |= self.clone(
                deck_index=self.deck_index+2,
                notes=self.notes + ", mill " + helpers.pretty(*limbo),
            )
            # Top top (flipped order)
            flipped_deck = before + limbo[::-1] + after
            states |= self.clone(
                deck_list=flipped_deck,
                notes=self.notes + ", leave " + helpers.pretty(*limbo[::-1]),
            )
            # Top bottom
            flipped_deck = before + limbo[::-1] + after
            states |= self.clone(
                deck_index=self.deck_index+1,
                deck_list=flipped_deck,
                notes=self.notes + ", mill " + helpers.pretty(limbo[1]) + ", leave " + helpers.pretty(limbo[0]),
            )
            return states
        else:
            raise ValueError("Scrying 3+ cards is not supported")

    def safe_getattr(self, attr):
        try:
            func = getattr(states, "cast_" + helpers.slug(card))
        except AttributeError:
            return GameStates([self])
        return func()

    def tap(self, card, silent=False):
        states = GameStates()
        for m in carddata.taps_for(card):
            mana_pool = self.mana_pool + m
            if m and not silent:
                mana_note = ", " + str(mana_pool) + " in pool" if mana_pool else ""
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
            if not carddata.taps_for(card):
                continue
            for m in carddata.taps_for(card):
                new_pools |= {pool+m for pool in pools}
            pools, new_pools = new_pools, set()
        states = GameStates()
        for pool in pools:
            mana_note = ", " + str(pool) + " in pool" if pool else ""
            states |= self.clone(
                mana_pool=pool,
                notes=self.notes + mana_note,
            )
        return states

    def tick_down(self):
        if not self.suspend:
            return GameStates([self])
        suspend = []
        to_cast = []
        for card in self.suspend:
            card = card.replace(".", "", 1)
            if "." in card:
                suspend.append(card)
            else:
                to_cast.append(card)
        if suspend:
            states = self.clone(
                suspend=helpers.tup(suspend),
                notes=self.notes + ", " + helpers.pretty(*suspend) + " ticking down",
            )
        else:
            states = self
        for card in to_cast:
            states = states.cast_from_suspend(card)
        return states

    def top(self, n):
        return self.deck_list[self.deck_index:self.deck_index + n]

    # ------------------------------------------------------------------

    def cast_allosaurus_rider(self):
        return self.clone(
            spells_cast=self.spells_cast+1,
            battlefield=helpers.tup_add(self.battlefield, "Allosaurus Rider"),
        )

    def cast_amulet_of_vigor(self):
        return self.clone(
            battlefield=helpers.tup_add(self.battlefield, "Amulet of Vigor"),
        )

    def cast_ancient_stirrings(self):
        return self.grab_from_top(carddata.colorless, 5, best=True)

    def cast_arboreal_grazer(self):
        states = GameStates()
        for card in carddata.lands(self.hand):
            states |= self.play_tapped(card, note=", play " + helpers.pretty(card))
        # If we have no lands in hand, there's no reason to cast Grazer.
        return states

    def cast_azusa_lost_but_seeking(self):
        if "Azusa, Lost but Seeking" in self.battlefield:
            return GameStates()
        return self.clone(
            battlefield=helpers.tup_add(self.battlefield, "Azusa, Lost but Seeking"),
            land_drops=self.land_drops + 2,
        )

    def cast_bond_of_flourishing(self):
        return self.grab_from_top(carddata.permanents, 3, best=True)

    def cast_chancellor_of_the_tangle(self):
        return GameStates([self])

    def cast_chromatic_star(self):
        return self.clone(
            battlefield=helpers.tup_add(self.battlefield, "Chromatic Star"),
        )

    def cast_eldrich_evolution(self):
        return self.cast_neoform()

    def cast_expedition_map(self):
        return self.clone(
            battlefield=helpers.tup_add(self.battlefield, "Expedition Map"),
        )

    def cast_explore(self):
        return self.clone(land_drops=self.land_drops+1).draw(1)

    def cast_manamorphose(self):
        states = GameStates()
        for m in {"GG", "GU", "UU"}:
            states |= self.add_mana(m)
        return states

    def cast_neoform(self):
        if "Allosaurus Rider" not in self.battlefield:
            return GameStates()
        return self.clone(done=True)

    def cast_oath_of_nissa(self):
        return self.grab_from_top(carddata.creatures_lands, 3, best=True)

    def cast_once_upon_a_time(self):
        return self.grab_from_top(carddata.creatures_lands, 5, best=True)

    def cast_opt(self):
        states = GameStates()
        for i in range(2):
            states |= self.grab(card=None, mill=i).draw(1)
        return states

    def cast_primeval_titan(self):
        return self.clone(done=True)

    def cast_pyretic_ritual(self):
        return self.add_mana("3")

    def cast_sakura_tribe_elder(self):
        states = GameStates()
        for card in {"Forest", "Mountain"}:
            states |= self.fetch(card, tapped=True)
        return states

    def cast_sakura_tribe_scout(self):
        return self.clone(
            battlefield=helpers.tup_add(self.battlefield, "Sakura-Tribe Scout"),
        )

    def cast_search_for_tomorrow(self):
        states = GameStates()
        for card in {"Forest", "Mountain"}:
            states |= self.fetch(card)
        return states

    def cast_serum_visions(self):
        return self.draw(1).scry(2)

    def cast_sleight_of_hand(self):
        return self.grab_from_top(None, 2, best=True)

    def cast_summer_bloom(self):
        return self.clone(land_drops=self.land_drops + 3)

    def cast_summoners_pact(self):
        states = GameStates()
        for card in carddata.green_creatures(self.deck_list, best=True):
            # You never need to Pact for a card that's in your hand.
            # Even if you need multiple Grazers, you can grab the second
            # after you play the first.
            if card in self.hand:
                continue
            if card == "Azusa, Lost but Seeking" and "Azusa, Lost but Seeking" in self.battlefield:
                continue
            states |= self.grab(card)
        return states.clone(mana_debt=self.mana_debt + Mana("2GG"))

    def cast_sylvan_scrying(self):
        # The computer has superhuman "instincts" about the order of the
        # deck. It knows what we're about to draw. Force it to make the
        # choice arbitrarily.
        cards = carddata.lands(self.deck_list)
        states = GameStates()
        for card in self.tron_choices(cards):
            states |= self.grab(card)
        return states

    def cast_through_the_breach(self):
        if "Primeval Titan" not in self.hand:
            return GameStates()
        # Add a dummy Amulet of Vigor to the battlefield to indicate a
        # "fast" win
        return self.clone(
            done=True,
            battlefield=helpers.tup_add(self.battlefield, "Amulet of Vigor"),
        )

    def cast_tragic_lesson(self):
        return self.draw(2).pitch(1) | self.draw(2).bounce_land()

    def cast_trinket_mage(self):
        states = GameStates()
        for card in carddata.trinkets(self.deck_list, best=True):
            states |= self.grab(card)
        return states

    def cast_wild_cantor(self):
        return self.clone(
            battlefield=helpers.tup_add(self.battlefield, "Wild Cantor"),
        )

    def cycle_allosaurus_rider(self):
        cards = [x for x in self.hand if carddata.is_green(x)]
        return self.pitch(2, options=cards).cast_allosaurus_rider()

    def cycle_once_upon_a_time(self):
        # Only allowed if this is the first spell we have cast all game.
        if self.spells_cast:
            return GameStates()
        return self.clone(spells_cast=self.spells_cast+1).cast_once_upon_a_time()

    def cycle_search_for_tomorrow(self):
        return self.clone(
            suspend=helpers.tup_add(self.suspend, "Search for Tomorrow.."),
        )

    def cycle_simian_spirit_guide(self):
        return self.add_mana("1")

    def cycle_tolaria_west(self):
        states = GameStates()
        for card in carddata.zeros(self.deck_list, best=True):
            states |= self.grab(card)
        return states

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

    def play_urzas_mine(self):
        return self.check_tron()

    def play_urzas_power_plant(self):
        return self.check_tron()

    def play_urzas_tower(self):
        return self.check_tron()

    def play_wooded_foothills(self):
        states = GameStates()
        for card in {"Forest", "Mountain", "Stomping Ground"}:
            states |= self.fetch(card)
        return states

    def play_zhalfirin_void(self):
        return self.scry(1)

    def sacrifice_chromatic_star(self):
        return self.add_mana("G").draw(1)

    def sacrifice_expedition_map(self):
        return self.cast_sylvan_scrying()

    def sacrifice_wild_cantor(self):
        return self.add_mana("G") | self.add_mana("U")
