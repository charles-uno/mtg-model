"""
The BaseState object keeps track of base operations: moving cards
between zones, keeping a log, cloning, etc. It knows as little as
possible about specific cards or their interactions. That stuff should
all go in the GameState object, which inherits directly from BaseState.
The difference is cosmetic, really, but it makes the bookkeeping easier. 
"""


from . import carddata, mana


class BaseState(object):

    def test(self, *notes):
        if isinstance(self.debt, int):
            print("BAD DEBT:", *notes)
            self.report()
            raise RuntimeError

    def __init__(self, **kwargs):
        self.board = kwargs.pop("board", [])
        self.debt = kwargs.pop("debt", mana.Mana())
        self.deck = kwargs.pop("deck")
        self.done = kwargs.pop("done", False)
        self.drops = kwargs.pop("drops", 0)
        self.hand = kwargs.pop("hand")
        self.lines = kwargs.pop("lines", [])
        self.play = kwargs.pop("play")
        self.pool = kwargs.pop("pool", mana.Mana())
        self.suspend = kwargs.pop("suspend", [])
        self.turn = kwargs.pop("turn", 0)
        # First line is opening hand
        if not self.lines:
            self.note("Draw", carddata.display(*self.hand))
        self.test("__init__")
        return

    def clone(self, *notes):
        self.test("clone")
        # Pretty sure we're supposed to be using `super` here?
        clone = type(self)(
            board=sorted(self.board),
            debt=self.debt,
            deck=self.deck[:],
            done=self.done,
            drops=self.drops,
            hand=sorted(self.hand),
            lines=self.lines[:],
            play=self.play,
            pool=self.pool,
            suspend=self.suspend[:],
            turn=self.turn,
        )
        if notes:
            clone.note(*notes)
        return clone

    def uid(self):
        return "|".join([
            ";".join(sorted(self.board)),
            str(self.debt),
            ";".join(self.deck),
            str(self.done),
            str(self.drops),
            ";".join(sorted(self.hand)),
            str(self.pool),
            ";".join(sorted(self.suspend)),
            str(self.turn),
        ])

    def next_states(self):
        self.test("next_states")
        clones = self.clone_pass()
        for card in set(self.hand):
            clones += self.clone_play(card)
            clones += self.clone_cast(card)
            clones += self.clone_activate(card)
        return clones

    def clone_pass(self):
        self.test("clone_pass")
        clone = self.clone("---- turn", self.turn+1)
        clone.turn += 1
        if "Azusa, Lost but Seeking" in self.board:
            clone.drops = 3
        else:
            clone.drops = 1
        clone.drops += clone.board.count("Sakura-Tribe Scout")
        clone.pool = mana.Mana()
        clones = clone.handle_suspend()
        # Tap everything at the first opportunity. This is not
        # deterministic because some lands can tap for different colors.
        new_clones = []
        for clone in clones:
            new_clones += clone.clone_tap_out()
        clones = new_clones
        # Pay for any pacts. This is also non-deterministic
        if self.debt:
            new_clones = []
            for clone in clones:
                clone.lines[-1] += ", pay " + str(clone.debt) + " for pact"
                new_clones += clone.clone_pay(clone.debt)
            clones = new_clones
        # Finish up the start of turn stuff
        for clone in clones:
            clone.debt = mana.Mana()
            if clone.turn > 1 or not clone.play:
                clone.lines[-1] += ", draw " + carddata.display(self.deck[0])
                clone.draw(silent=True)
        return clones

    def handle_suspend(self):
        for card in self.suspend:
            if card.count(".") > 1:
                self.lines[-1] += ", " + carddata.display(card) + " ticking down"
        new_suspend = [x.replace(".", "", 1) for x in self.suspend]
        to_resolve = [x for x in new_suspend if "." not in x]
        clone = self.clone()
        clone.suspend = [x for x in new_suspend if "." in x]
        clones = [clone]
        for card in to_resolve:
            new_clones = []
            for clone in clones:
                clone.lines[-1] += ", cast " + carddata.display(card) + " from exile"
                new_clones += getattr(clone, "cast_" + carddata.slug(card))()
            clones = new_clones
        return clones

    def clone_play(self, card):
        self.test("playing", card)
        if self.drops and carddata.is_land(card) and card in self.hand:
            self.test("cloning to play", card)
            clone = self.clone("Play", carddata.display(card))
            clone.test("cloned to play", card)
            clone.drops -= 1
            if carddata.enters_tapped(card):
                return clone.play_tapped(card)
            else:
                return clone.play_untapped(card)
        else:
            return []

    def play_tapped(self, card):
        self.hand.remove(card)
        self.board.append(card)
        n_amulets = self.board.count("Amulet of Vigor")
        clones, new_clones = [self.clone()], []
        for _ in range(n_amulets):
            # Handle each amulet untap independently
            for clone in clones:
                new_clones += clone.clone_tap(card)
            clones, new_clones = new_clones, []
            for clone in clones:
                clone.lines[-1] += ", " + str(clone.pool) + " in pool"
        # Now figure out any other consequences, like bouncing
        for clone in clones:
            new_clones += getattr(clone, "play_" + carddata.slug(card))()
        return new_clones

    def play_untapped(self, card):
        self.hand.remove(card)
        self.board.append(card)
        clones = []
        for clone in self.clone_tap(card):
            clones += getattr(clone, "play_" + carddata.slug(card))()
        for clone in clones:
            clone.lines[-1] += ", " + str(clone.pool) + " in pool"
        return clones

    def bounce_land(self):
        clones = []
        for card in set(self.board):
            if not carddata.is_land(card):
                continue
            c = self.clone()
            c.lines[-1] += ", bounce " + carddata.display(card)
            c.board.remove(card)
            c.hand.append(card)
            clones.append(c)
        return clones

    def clone_cast(self, card):
        self.test("clone_cast", card)
        if card in self.hand and self.can_pay(carddata.cost(card)):
            clones = []
            for clone in self.clone_pay(carddata.cost(card)):
                clone.note("Cast", carddata.display(card))
                clone.hand.remove(card)
                clones += getattr(clone, "cast_" + carddata.slug(card))()
            return clones
        else:
            return []

    def clone_activate(self, card):
        self.test("clone_activate", card)
        if card in self.hand and self.can_pay(carddata.activation_cost(card)):
            clones = []
            for clone in self.clone_pay(carddata.activation_cost(card)):
                clone.note("Activate", carddata.display(card))
                clone.hand.remove(card)
                clones += getattr(clone, "activate_" + carddata.slug(card))()
            return clones
        else:
            return []

    def __hash__(self):
        return hash(self.uid())

    def __eq__(self, other):
        return self.uid() == other.uid()

    def clone_tap(self, card):
        clones = []
        for m in carddata.taps_for(card):
            clone = self.clone()
            clone.pool += m
            clones.append(clone)
        return clones

    def clone_tap_out(self):
        clones, new_clones = [self], []
        for card in self.board:
            if not carddata.is_land(card):
                continue
            for clone in clones:
                new_clones += clone.clone_tap(card)
            clones, new_clones = new_clones, []
        for clone in clones:
            clone.lines[-1] += ", " + str(clone.pool) + " in pool"
        return clones

    def can_pay(self, cost):
        if cost is None:
            return False
        return cost <= self.pool

    def clone_pay(self, cost):
        if not self.pool >= cost:
            return []
        clones = []
        for pool in self.pool.minus(cost):
            clone = self.clone()
            clone.pool = pool
            clones.append(clone)
        return clones

    def draw(self, n=1, silent=False):
        if not silent:
            self.note("Draw", carddata.display(*self.deck[:n]))
        self.hand, self.deck = self.hand + self.deck[:n], self.deck[n:]

    def scry(self, n):
        if n > 1:
            raise RuntimeError("Scry > 1 is not yet supported")
        top = self.clone()
        top.lines[-1] += ", scry " + carddata.display(self.deck[0]) + " to top"
        bot = self.clone()
        bot.lines[-1] += ", scry " + carddata.display(self.deck[0]) + " to bottom"
        bot.deck = bot.deck[1:] + bot.deck[:1]
        return top, bot

    def note(self, *args):
        self.lines.append(" ".join(str(x) for x in args))

    def __str__(self):
        if "turn" in self.lines[-1].lower():
            self.lines.pop(-1)
        return "\n".join(self.lines)

    def __contains__(self, card):
        """See if this game state used a certain card."""
        if card is None:
            return False
        elif card == "":
            return True
        log = str(self)
        look_for = (
            "Activate " + carddata.display(card),
            "Cast " + carddata.display(card),
            "Play " + carddata.display(card),
        )
        return any(x in log for x in look_for)

    def summary(self):
        # Are we on the play or the draw?
        draw = 0 if self.play else 1
        if self.done:
            # What turn did we play Titan?
            turn = self.turn
            # Do we have Amulet in play?
            fast = 1 if "Amulet of Vigor" in self.board else 0
        else:
            turn, fast = 0, 0
        return ",".join([str(x) for x in (turn, draw, fast)])
