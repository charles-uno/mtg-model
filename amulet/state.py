from . import io, mana

class GameState(object):

    # ------------------------------------------------------------------

    def test(self, *notes):
        if isinstance(self.debt, int):
            print("BAD DEBT:", *notes)
            self.report()
            raise RuntimeError

    # ------------------------------------------------------------------

    def __init__(self, **kwargs):
        self.board = kwargs.pop("board", [])
        self.debt = kwargs.pop("debt", mana.Mana())
        self.deck = kwargs.pop("deck")
        self.done = kwargs.pop("done", False)
        self.drops = kwargs.pop("drops", 1)
        self.hand = kwargs.pop("hand", [])
        self.lines = kwargs.pop("lines", [])
        self.pool = kwargs.pop("pool", mana.Mana())
        self.turn = kwargs.pop("turn", 1)
        if len(self.lines) == 1:
            self.lines.append("---- turn 1")
        self.test("__init__")
        return

    def clone(self, *notes):
        self.test("clone")
        clone = GameState(
            board=sorted(self.board),
            debt=self.debt,
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

    def uid(self):
        return "|".join([
            ";".join(self.deck),
            ";".join(self.hand),
            ";".join(self.board),
            str(self.turn),
            str(self.drops),
            str(self.debt),
            str(self.pool),
        ])

    def __str__(self):
        return "HAND: " + io.display(*self.hand) + "\n" + "BOARD: " + io.display(*self.board)

    def next_states(self):
        self.test("next_states")
        clones = self.clone_pass()
        for card in set(self.hand):
            clones += self.clone_play(card)
            clones += self.clone_cast(card)
        return clones

    # ------------------------------------------------------------------

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
        # Tap everything at the first opportunity. This will eventually
        # return multiple options when we have to consider colors.
        for card in clone.board:
            if io.is_land(card):
                clone.pool = clone.pool + io.taps_for(card)
        clone.lines[-1] += ", " + str(clone.pool) + " in pool"
        # Pay for any pacts
        if not clone.can_pay(clone.debt):
            return []
        if clone.debt:
            clone.lines[-1] += ", pay " + str(clone.debt) + " for pact"
        clone.pay(clone.debt)
        clone.debt = mana.Mana()
        clone.lines[-1] += ", draw " + io.display(self.deck[0])
        clone.draw(silent=True)
        return [clone]

    # ------------------------------------------------------------------

    def clone_play(self, card):
        self.test("playing", card)
        if self.drops and io.is_land(card) and card in self.hand:
            self.test("cloning to play", card)
            clone = self.clone("Play", io.display(card))
            clone.test("cloned to play", card)
            clone.drops -= 1
            if io.enters_tapped(card):
                return clone.play_tapped(card)
            else:
                return clone.play_untapped(card)
        else:
            return []

    def play_tapped(self, card):
        self.hand.remove(card)
        self.board.append(card)
        n_amulets = self.board.count("Amulet of Vigor")
        for _ in range(n_amulets):
            self.pool = self.pool + io.taps_for(card)
            self.lines[-1] += ", " + str(self.pool) + " in pool"
        return getattr(self, "play_" + io.slug(card))()

    def play_untapped(self, card):
        self.hand.remove(card)
        self.board.append(card)
        self.pool = self.pool + io.taps_for(card)
        self.lines[-1] += ", " + str(self.pool) + " in pool"
        return getattr(self, "play_" + io.slug(card))()

    def play_bojuka_bog(self):
        return [self]

    def play_boros_garrison(self):
        return self.bounce_land()

    def play_forest(self):
        return [self]

    def play_khalni_garden(self):
        return [self]

    def play_radiant_fountain(self):
        return [self]

    def play_simic_growth_chamber(self):
        return self.bounce_land()

    def play_tolaria_west(self):
        return [self]

    def bounce_land(self):
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
        self.test("about to cast", card)
        if card in self.hand and self.can_pay(io.get_cost(card)):
            self.test("while casting", card)
            clone = self.clone("Cast", io.display(card))
            clone.pay(io.get_cost(card))
            self.test("after casting", card)
            clone.hand.remove(card)
            clones = getattr(clone, "cast_" + io.slug(card))()
            for clone in clones:
                clone.test("about to return from casting", card)
            return clones
        else:
            return []

    def cast_amulet_of_vigor(self):
        self.board.append("Amulet of Vigor")
        return [self]

    def cast_ancient_stirrings(self):
        cards = self.deck[:5]
        # Put everything on the bottom, create a new card for the hand
        self.deck = self.deck[5:] + cards
        cards = { c for c in cards if io.is_colorless(c) }
        if not cards:
            clone = self.clone()
            clone.lines[-1] += ", whiff"
            return [clone]
        clones = []
        for c in cards:
            clone = self.clone()
            clone.lines[-1] += ", take " + io.display(c)
            clone.hand.append(c)
            clones.append(clone)
        return clones

    def cast_arboreal_grazer(self):
        lands = { c for c in self.hand if io.is_land(c) }
        if not lands:
            self.lines[-1] += ", whiff"
            return [self]
        clones = []
        for land in lands:
            clone = self.clone()
            clone.lines[-1] += ", play " + io.display(land)
            clones += clone.play_tapped(land)
        return clones

    def cast_azusa_lost_but_seeking(self):
        if "Azusa, Lost but Seeking" not in self.board:
            self.drops += 2
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

    def cast_sakura_tribe_scout(self):
        self.board.append("Sakura-Tribe Scout")
        return [self]

    def cast_summoners_pact(self):
        clones = []
        for c in set(self.deck):
            if not io.is_creature(c) or not io.is_green(c):
                continue
            clone = self.clone()
            clone.lines[-1] += ", get " + io.display(c)
            clone.hand.append(c)
            clone.debt += mana.Mana("2GG")
            clones.append(clone)
        return clones


    def cast_tolaria_west(self):
        clones = []
        for card in set(self.deck):
            if io.get_cmc(card) != 0:
                continue
            clone = self.clone()
            clone.lines.pop(-1)
            clone.note("Transmute", io.display("Tolaria West"), "for", io.display(card))
            clone.hand.append(card)
            clones.append(clone)
        return clones

    # ------------------------------------------------------------------

    def __hash__(self):
        return hash(self.uid())

    def __eq__(self, other):
        return self.uid() == other.uid()

    # ------------------------------------------------------------------

    def can_pay(self, cost):
        if cost is None:
            return False
        return cost <= self.pool

    def pay(self, cost):
        self.pool = self.pool - cost

    # ------------------------------------------------------------------

    def draw(self, n=1, silent=False):
        if not silent:
            self.note("Draw", io.display(*self.deck[:n]))
        self.hand, self.deck = self.hand + self.deck[:n], self.deck[n:]

    # ------------------------------------------------------------------

    def note(self, *args):
        self.lines.append(" ".join( str(x) for x in args ))

    def report(self):
        if "turn" in self.lines[-1].lower():
            self.lines.pop(-1)
        [ print(x) for x in self.lines ]

    # ------------------------------------------------------------------
