import itertools

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
        self.on_the_draw = kwargs.pop("draw")
        self.drops = kwargs.pop("drops", 0)
        self.hand = kwargs.pop("hand")
        self.lines = kwargs.pop("lines", [])
        self.pool = kwargs.pop("pool", mana.Mana())
        self.turn = kwargs.pop("turn", 0)
        # First line is opening hand
        if not self.lines:
            self.note("Draw", io.display(*self.hand))
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
            draw=self.on_the_draw,
            pool=self.pool,
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
            str(self.turn),
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
        # Tap everything at the first opportunity. This is not
        # deterministic because some lands can tap for different colors.
        clones = clone.clone_tap_out()
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
            if clone.turn > 1 or clone.on_the_draw:
                clone.lines[-1] += ", draw " + io.display(self.deck[0])
                clone.draw(silent=True)
        return clones

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
            new_clones += getattr(clone, "play_" + io.slug(card))()
        return new_clones

    def play_untapped(self, card):
        self.hand.remove(card)
        self.board.append(card)
        clones = []
        for clone in self.clone_tap(card):
            clones += getattr(clone, "play_" + io.slug(card))()
        for clone in clones:
            clone.lines[-1] += ", " + str(clone.pool) + " in pool"
        return clones

    def play_bojuka_bog(self):
        return [self]

    def play_boros_garrison(self):
        return self.bounce_land()

    def play_forest(self):
        return [self]

    def play_gemstone_mine(self):
        return [self]

    def play_khalni_garden(self):
        return [self]

    def play_lotus_field(self):
        lands = { c for c in self.board if io.is_land(c) }
        clones = []
        if len(lands) < 2:
            self.lines[-1] += ", lose " + " and ".join( io.display(c) for c in self.board )
            self.board = []
            return [self]
        for pair in itertools.combinations(lands, 2):
            clone = self.clone()
            [ clone.board.remove(c) for c in pair ]
            clone.lines[-1] += ", lose " + io.display(pair[0]) + " and " + io.display(pair[1])
            clones.append(clone)
        return clones

    def play_radiant_fountain(self):
        return [self]

    def play_selesnya_sanctuary(self):
        return self.bounce_land()

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
        self.test("clone_cast", card)
        if card in self.hand and self.can_pay(io.get_cost(card)):
            clones = []
            for clone in self.clone_pay(io.get_cost(card)):
                clone.note("Cast", io.display(card))
                clone.hand.remove(card)
                clones += getattr(clone, "cast_" + io.slug(card))()
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

    def cast_bond_of_flourishing(self):
        cards = self.deck[:3]
        # Put everything on the bottom, create a new card for the hand
        self.deck = self.deck[3:] + cards
        cards = { c for c in cards if io.is_permanent(c) }
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

    def cast_cantrip(self):
        self.draw()
        return [self]

    def cast_elvish_rejuvenator(self):
        cards = self.deck[:5]
        # Put everything on the bottom, create a new card for the hand
        self.deck = self.deck[5:] + cards
        cards = { c for c in cards if io.is_land(c) }
        if not cards:
            clone = self.clone()
            clone.lines[-1] += ", whiff"
            return [clone]
        clones = []
        for c in cards:
            clone = self.clone()
            clone.lines[-1] += ", take " + io.display(c)
            clone.hand.append(c)
            clones += clone.play_tapped(c)
        return clones

    def cast_explore(self):
        self.lines[-1] += ", draw %s" % io.display(self.deck[0])
        self.draw(silent=True)
        self.drops += 1
        return [self]

    def cast_growth_spiral(self):
        self.lines[-1] += ", draw %s" % io.display(self.deck[0])
        self.draw(silent=True)
        self.drops += 1
        return [self]

    def cast_manamorphose(self):
        clones = []
        for m in ["UU", "UG", "GG"]:
            clone = self.clone()
            clone.pool += mana.Mana(m)
            clone.lines[-1] += ", " + str(clone.pool) + " in pool"
            clone.lines[-1] += ", draw " + io.display(clone.deck[0])
            clone.draw(silent=True)
            clones.append(clone)
        return clones

    def cast_oath_of_nissa(self):
        cards = self.deck[:3]
        # Put everything on the bottom, create a new card for the hand
        self.deck = self.deck[3:] + cards
        cards = { c for c in cards if io.is_creature(c) or io.is_land(c) }
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

    def cast_opt(self):
        cards = self.deck[:2]
        self.deck = self.deck[2:] + cards
        clones = []
        for c in cards:
            clone = self.clone()
            clone.lines[-1] += ", take " + io.display(c)
            clone.hand.append(c)
            clones.append(clone)
        return clones

    def cast_primeval_titan(self):
        self.done = True
        return [self]

    def cast_sakura_tribe_scout(self):
        self.board.append("Sakura-Tribe Scout")
        return [self]

    def cast_simian_spirit_guide(self):
        self.pool += mana.Mana("1")
        self.lines.pop(-1)
        self.note("Exile", io.display("Simian Spirit Guide") + ", " + str(self.pool) + " in pool")
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

    def cast_trinket_mage(self):
        clones = []
        for card in set(self.deck):
            if not io.is_artifact(card) or io.get_cmc(card) > 1:
                continue
            clone = self.clone()
            clone.lines[-1] += ", grab " + io.display(card)
            clone.hand.append(card)
            clones.append(clone)
        return clones

    # ------------------------------------------------------------------

    def __hash__(self):
        return hash(self.uid())

    def __eq__(self, other):
        return self.uid() == other.uid()

    # ------------------------------------------------------------------

    def clone_tap(self, card):

        before = self.pool

        clones = []
        for m in io.taps_for(card):
            clone = self.clone()
            clone.pool += m
            clones.append(clone)

        after = clones[0].pool

        if card == "Selesnya Sanctuary" and "Elvish Rejuvenator" in self.board:
            print(before, "->", after)

        return clones

    def clone_tap_out(self):
        clones, new_clones = [self], []
        for card in self.board:
            if not io.is_land(card):
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

    def summary(self):
        # Are we on the play or the draw?
        draw = 1 if self.on_the_draw else 0
        if self.done:
            # What turn did we play Titan?
            turn = self.turn
            # Do we have Amulet in play?
            fast = 1 if "Amulet of Vigor" in self.board else 0
        else:
            turn, fast = 0, 0
        return ",".join( [ str(x) for x in (turn, draw, fast) ] )
