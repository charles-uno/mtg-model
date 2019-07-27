from . import io

class GameState(object):

    # ------------------------------------------------------------------

    def __init__(self, **kwargs):
        self.board = kwargs.pop("board", [])
        self.deck = kwargs.pop("deck")
        self.done = kwargs.pop("done", False)
        self.drops = kwargs.pop("drops", 0)
        self.hand = kwargs.pop("hand", [])
        self.lines = kwargs.pop("lines", [])
        self.pool = kwargs.pop("pool", 0)
        self.turn = kwargs.pop("turn", 0)

    def clone(self, *notes):
        clone = GameState(
            board=sorted(self.board),
            deck=self.deck,
            done=self.done,
            drops=self.drops,
            hand=sorted(self.hand),
            lines=self.lines,
            pool=self.pool,
            turn=self.turn,
        )
        clone.note(*notes)
        return clone



    def __str__(self):
        return "HAND: " + io.display(*self.hand) + "\n" + "BOARD: " + io.display(*self.board)


    def next_states(self):
        states = self.clone_pass()
        for card in set(self.hand):
            states += self.clone_play(card)
            states += self.clone_cast(card)
        return states

    # ------------------------------------------------------------------

    def clone_pass(self):
        clone = self.clone("Pass the turn")
        clone.turn += 1
        clone.drops = 1
        clone.pool = []
        return [clone]

    # ------------------------------------------------------------------

    def clone_play(self, card):
        if self.drops and io.is_land(card) and card in self.hand:
            clone = self.clone("Playing", card)
            clone.hand.remove(card)
            clone.board.append(card)
            clone.drops -= 1
            return getattr(self, "play_" + io.slug(card))
        else:
            return []



    def play_forest(self):
        return [self]



    # ------------------------------------------------------------------

    def clone_cast(self, card):
        if card in self.hand and self.can_pay(io.get_cost(card)):
            clone = self.clone("Casting", card)
            clone.pay(io.get_cost(card))
            clone.hand.remove(card)
            return getattr(self, "cast_" + io.slug(card))
        else:
            return []

    def cast_explore(self):
        self.draw()
        self.drops += 1
        return [self]

    def cast_primeval_titan(self):
        self.done = True
        return [self]







    def __hash__(self):
        pass

    def __eq__(self, other):
        pass


    def clone_play_forest(self):
        clone = self.clone()



    def can_pay(self, cost):
        return cost is not None and cost <= self.pool

    def pay(self, cost):
        self.pool -= cost

    # ------------------------------------------------------------------

    def draw(self, n=1):
        self.note("Drawing", io.display(*self.deck[:n]))
        self.hand, self.deck = self.hand + self.deck[:n], self.deck[n:]


    # ------------------------------------------------------------------

    def note(self, *args):
        self.lines.append(" ".join( str(x) for x in args ))

    def report(self):
        [ print(x) for x in self.lines ]

    # ------------------------------------------------------------------
