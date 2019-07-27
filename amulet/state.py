from . import io, mana

class GameState(object):

    # ------------------------------------------------------------------

    def __init__(self, **kwargs):
        self.board = kwargs.pop("board", [])
        self.deck = kwargs.pop("deck")
        self.done = kwargs.pop("done", False)
        self.drops = kwargs.pop("drops", 1)
        self.hand = kwargs.pop("hand", [])
        self.lines = kwargs.pop("lines", [])
        self.pool = kwargs.pop("pool", mana.Mana())
        self.turn = kwargs.pop("turn", 0)

    def clone(self, *notes):
        clone = GameState(
            board=sorted(self.board),
            deck=self.deck[:],
            done=self.done,
            drops=self.drops,
            hand=sorted(self.hand),
            lines=self.lines[:],
            pool=self.pool,
            turn=self.turn,
        )
        if notes:
            clone.note(*notes)
        return clone

    def __str__(self):
        return "HAND: " + io.display(*self.hand) + "\n" + "BOARD: " + io.display(*self.board)

    def next_states(self):
        clones = self.clone_pass()
        for card in set(self.hand):
            clones += self.clone_play(card)
            clones += self.clone_cast(card)
        return clones

    # ------------------------------------------------------------------

    def clone_pass(self):
        clone = self.clone("Turn", self.turn+1)
        clone.turn += 1
        if "Azusa, Lost but Seeking" in self.board:
            clone.drops = 3
        else:
            clone.drops = 1
        clone.pool = mana.Mana()
        # Tap everything at the first opportunity. This will eventually
        # return multiple options when we have to consider colors.
        for card in clone.board:
            if io.is_land(card):
                clone.pool += io.taps_for(card)
        clone.lines[-1] += ", %d in pool" % clone.pool
        return [clone]

    # ------------------------------------------------------------------

    def clone_play(self, card):
        if self.drops and io.is_land(card) and card in self.hand:
            clone = self.clone("Play", io.display(card))
            clone.hand.remove(card)
            clone.board.append(card)
            clone.drops -= 1
            if io.enters_tapped(card):
                n_amulets = clone.board.count("Amulet of Vigor")
                if n_amulets:
                    clone.lines[-1] += ", tap for %d" % (n_amulets*io.taps_for(card))
                clone.pool += n_amulets*io.taps_for(card)
            else:
                clone.lines[-1] += ", tap for %d" % io.taps_for(card)
                clone.pool += io.taps_for(card)
            return getattr(clone, "play_" + io.slug(card))()
        else:
            return []

    def play_forest(self):
        return [self]

    def play_simic_growth_chamber(self):
        clones = []
        for card in set(self.board):
            if not io.is_land(card):
                continue
            c = self.clone()
            c.lines[-1] += ", bounce " + io.display(card)
            c.board.remove(card)
            c.hand.append(card)
            clones.append(c)
        return clones

    # ------------------------------------------------------------------

    def clone_cast(self, card):
        if card in self.hand and self.can_pay(io.get_cost(card)):
            clone = self.clone("Cast", io.display(card))
            clone.pay(io.get_cost(card))
            clone.hand.remove(card)
            return getattr(clone, "cast_" + io.slug(card))()
        else:
            return []

    def cast_amulet_of_vigor(self):
        self.board.append("Amulet of Vigor")
        return [self]


    def cast_azusa_lost_but_seeking(self):
        if "Azusa, Lost but Seeking" not in self.board:
            self.board.append("Azusa, Lost but Seeking")
        return [self]

    def cast_cantrip(self):
        self.draw()
        return [self]

    def cast_explore(self):
        self.lines[-1] += ", draw %s" % io.display(self.deck[0])
        self.draw(silent=True)
        self.drops += 1
        return [self]

    def cast_primeval_titan(self):
        self.done = True
        return [self]

    # ------------------------------------------------------------------

    def __hash__(self):
        return hash(self.uid())

    def __eq__(self, other):
        return self.uid() == other.uid()

    def uid(self):
        return "|".join([
            ";".join(self.deck),
            ";".join(self.hand),
            ";".join(self.board),
            str(self.turn),
            str(self.drops),
        ])

    # ------------------------------------------------------------------

    def can_pay(self, cost):
        return cost is not None and cost <= self.pool

    def pay(self, cost):
        self.pool -= cost

    # ------------------------------------------------------------------

    def draw(self, n=1, silent=False):
        if not silent:
            self.note("Drawing", io.display(*self.deck[:n]))
        self.hand, self.deck = self.hand + self.deck[:n], self.deck[n:]

    # ------------------------------------------------------------------

    def note(self, *args):
        self.lines.append(" ".join( str(x) for x in args ))

    def report(self):
        if self.lines[-1].startswith("Turn"):
            self.lines.pop(-1)
        [ print(x) for x in self.lines ]

    # ------------------------------------------------------------------
