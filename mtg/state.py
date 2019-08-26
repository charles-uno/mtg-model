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
MAX_STATES = 1e6
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
                look_for = (
                    "Discard " + helpers.pretty(card),
                    "Cast " + helpers.pretty(card),
                    "Play " + helpers.pretty(card),
                )
                return any(x in state.notes for x in look_for)

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
    "battlefield_tapped": (),
    "battlefield_untapped": (),
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

    @property
    def battlefield(self):
        return self.battlefield_tapped + self.battlefield_untapped

    def bounce_land(self):
        states = GameStates()
        # For fetching and cantrips, some lands are better than others.
        # Choices for what to bounce are trickier.
        for card in carddata.lands(self.battlefield_tapped):
            states |= self.clone(
                notes=self.notes + ", bounce " + helpers.pretty(card),
                battlefield_tapped=helpers.tup_sub(self.battlefield_tapped, card),
                hand=helpers.tup_add(self.hand, card),
            )
        # If we have two copies of the same land, one tapped and one
        # untapped, we always want to bounce the tapped one.
        cards = set(self.battlefield_untapped) - set(self.battlefield_tapped)
        for card in carddata.lands(cards):
            states |= self.clone(
                notes=self.notes + ", bounce " + helpers.pretty(card),
                battlefield_untapped=helpers.tup_sub(self.battlefield_untapped, card),
                hand=helpers.tup_add(self.hand, card),
            )
        return states

    def cast(self, card):
        cost = carddata.cost(card)
        if card not in self.hand or cost is None or not self.mana_pool >= cost:
            return GameStates()
        states = self.clone(
            hand=helpers.tup_sub(self.hand, card),
            notes=self.notes + "\nCast " + helpers.pretty(card),
        ).pay(cost)
        # Don't use the safety wrapper. If casting is a no-op, we
        # shouldn't be casting. And something is probably wrong.
        return getattr(states, "cast_" + helpers.slug(card))()

    def cycle(self, card):
        cost = carddata.cycle_cost(card)
        if card not in self.hand or cost is None or not self.mana_pool >= cost:
            return GameStates()
        states = self.clone(
            hand=helpers.tup_sub(self.hand, card),
            notes=self.notes + "\nDiscard " + helpers.pretty(card),
        ).pay(cost)
        return states.safe_getattr("cycle_" + helpers.slug(card))

    def pitch(self, n):
        """GameStates is a set, so there's already a discard function."""
        states = GameStates()
        for cards in itertools.combinations(self.hand, n):
            states |= self.clone(
                hand=helpers.tup_sub(self.hand, *cards),
                notes=self.notes + ", discard " + helpers.pretty(*cards),
            )
        return states

    def draw(self, n):
        cards = self.top(n)
        # Opening hand gets its own line
        if not self.notes:
            notes = "\nDraw " + helpers.pretty(*cards)
        else:
            notes = ", draw " + helpers.pretty(*cards)
        return self.clone(
            deck_index=self.deck_index + n,
            hand=tuple(sorted(self.hand + cards)),
            notes=self.notes + notes,
        )

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

    def pass_turn(self):
        # Optimizations go here. If we played a pact on turn 1, bail. If
        # we passed the turn with no lands, bail. And so on.
        if self.turn and not self.battlefield_tapped:
            return GameStates()
        if self.turn < 2 and self.mana_debt:
            return GameStates()
        mana_debt = self.mana_debt
        land_drops = 1 + self.battlefield.count("Sakura-Tribe Scout")
        if "Azusa, Lost but Seeking" in self.battlefield:
            land_drops += 2
        states = self.clone(
            battlefield_tapped=(),
            battlefield_untapped=helpers.tup(self.battlefield_tapped + self.battlefield_untapped),
            land_drops=land_drops,
            mana_debt=Mana(),
            mana_pool=Mana(),
            notes=self.notes + "\n---- turn " + str(self.turn+1),
            turn=self.turn+1,
        ).tap_out()
        if mana_debt:
            states = states.pay(mana_debt, note=", pay " + str(mana_debt) + " for pact")
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

    def play(self, card):
        if not self.land_drops or not carddata.is_land(card) or not card in self.hand:
            return GameStates()
        states = self.clone(
            notes=self.notes + "\nPlay " + helpers.pretty(card),
            land_drops=self.land_drops - 1,
        )
        if carddata.enters_tapped(card):
            return states.play_tapped(card)
        else:
            return states.play_untapped(card)

    def play_tapped(self, card, note=""):
        states = self.clone(
            battlefield_tapped=helpers.tup_add(self.battlefield_tapped, card),
            hand=helpers.tup_sub(self.hand, card),
            notes=self.notes + note,
        )
        for _ in range(self.battlefield_untapped.count("Amulet of Vigor")):
            states = states.untap_tap(card)
        return states.safe_getattr("play_" + helpers.slug(card))

    def play_untapped(self, card):
        states = self.clone(
            hand=helpers.tup_sub(self.hand, card),
            battlefield_untapped=helpers.tup_add(self.battlefield_untapped, card),
        ).tap(card)
        return states.safe_getattr("play_" + helpers.slug(card))

    def report(self):
        print(self.notes)
        if self.overflowed:
            print("OVERFLOW")

    def safe_getattr(self, attr):
        try:
            func = getattr(states, "cast_" + helpers.slug(card))
        except AttributeError:
            return GameStates([self])
        return func()

    def tap(self, card):
        states = GameStates()
        for m in carddata.taps_for(card):
            mana_pool = self.mana_pool + m
            if mana_pool:
                mana_note = ", " + str(mana_pool) + " in pool" if mana_pool else ""
            states |= self.clone(
                mana_pool=mana_pool,
                battlefield_tapped=helpers.tup_add(self.battlefield_tapped, card),
                battlefield_untapped=helpers.tup_sub(self.battlefield_untapped, card),
                notes=self.notes + mana_note,
            )
        return states or GameStates([self])

    def tap_out(self):
        pools, new_pools = {self.mana_pool}, set()
        for card in self.battlefield_untapped:
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

    def top(self, n):
        return self.deck_list[self.deck_index:self.deck_index + n]

    def untap(self, card):
        return self.clone(
            battlefield_tapped=helpers.tup_sub(self.battlefield_tapped, card),
            battlefield_untapped=helpers.tup_add(self.battlefield_untapped, card),
        )

    def untap_tap(self, card):
        states = GameStates()
        for m in carddata.taps_for(card):
            mana_pool = self.mana_pool + m
            if mana_pool:
                mana_note = ", " + str(mana_pool) + " in pool" if mana_pool else ""
            states |= self.clone(
                mana_pool=mana_pool,
                notes=self.notes + mana_note,
            )
        return states or GameStates([self])

    # ------------------------------------------------------------------

    def cast_amulet_of_vigor(self):
        return self.clone(
            battlefield_untapped=helpers.tup_add(self.battlefield_untapped, "Amulet of Vigor"),
        )

    def cast_ancient_stirrings(self):
        states = GameStates()
        for card in carddata.colorless(self.top(5), best=True):
            states |= self.grab(card, mill=5)
        return states or self.grab(mill=5, note=", whiff")

    def cast_arboreal_grazer(self):
        states = GameStates()
        for card in carddata.lands(self.hand):
            states |= self.play_tapped(card, note=", play" + helpers.pretty(card))
        # If we have no lands in hand, there's no reason to cast Grazer.
        return states

    def cast_azusa_lost_but_seeking(self):
        if "Azusa, Lost but Seeking" in self.battlefield:
            return GameStates([self])
        return self.clone(
            battlefield_untapped=helpers.tup_add(self.battlefield_untapped, "Azusa, Lost but Seeking"),
            land_drops=self.land_drops + 2,
        )

    def cast_bond_of_flourishing(self):
        states = GameStates()
        for card in carddata.permanents(self.top(3), best=True):
            states |= self.grab(card, mill=3)
        return states or self.grab(mill=3, note=", whiff")

    def cast_explore(self):
        return self.clone(land_drops=self.land_drops+1).draw(1)

    def cast_oath_of_nissa(self):
        states = GameStates()
        for card in carddata.creatures_lands(self.top(3), best=True):
            states |= self.grab(card, mill=3)
        return states or self.grab(mill=3, note=", whiff")

    def cast_opt(self):
        states = GameStates()
        for i in range(2):
            states |= self.grab(card=None, mill=i).draw(1)
        return states

    def cast_primeval_titan(self):
        return self.clone(done=True)

    def cast_sakura_tribe_scout(self):
        return self.clone(
            battlefield_tapped=helpers.tup_add(self.battlefield_tapped, "Sakura-Tribe Scout"),
        )

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

    def cast_tragic_lesson(self):
        return self.draw(2).pitch(1) | self.draw(2).bounce_land()

    def cycle_tolaria_west(self):
        states = GameStates()
        for card in carddata.zeros(self.deck_list, best=True):
            states |= self.grab(card)
        return states

    def play_boros_garrison(self):
        return self.bounce_land()

    def play_selesnya_sanctuary(self):
        return self.bounce_land()

    def play_simic_growth_chamber(self):
        return self.bounce_land()
