"""
The GameState object is where functions should be defined to handle the
behaviors of specific carddata. For example, in order to cast Ancient
Stirrings, we need a function called cast_ancient_stirrings. It returns
a list of clones -- all possible game states at the end of the spell's
resolution. Similarly, a function play_simic_growth_chamber is needed to
handle playing Simic Growth Chamber as our land for the turn. Finally,
functions like activate_tolaria_west handle activated abilities (or
alternate costs).

If you try to run a deck before adding functions for those cards, it'll
yell at you. Or, depending on what you forgot to put in carddata.yaml, it
might just treat them as blanks. For that reason it's good to test out
new cards by creating a deck with lots of copies, then looking at output
from some games to make sure the behavor is as expected.
"""


import itertools

from . import basestate, carddata, mana


class GameState(basestate.BaseState):

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
        lands = {c for c in self.board if carddata.is_land(c)}
        clones = []
        if len(lands) < 2:
            self.lines[-1] += ", lose " + " and ".join(carddata.display(c) for c in self.board)
            self.board = []
            return [self]
        for pair in itertools.combinations(lands, 2):
            clone = self.clone()
            [clone.board.remove(c) for c in pair]
            clone.lines[-1] += ", lose " + carddata.display(pair[0]) + " and " + carddata.display(pair[1])
            clones.append(clone)
        return clones

    def play_mountain(self):
        return [self]

    def play_radiant_fountain(self):
        return [self]

    def play_selesnya_sanctuary(self):
        return self.bounce_land()

    def play_sheltered_thicket(self):
        return [self]

    def play_simic_growth_chamber(self):
        return self.bounce_land()

    def play_stomping_ground(self):
        return [self]

    def play_tolaria_west(self):
        return [self]

    def play_valakut_the_molten_pinnacle(self):
        return [self]

    def play_wooded_foothills(self):
        self.board.remove("Wooded Foothills")
        self.hand.append("Forest")
        return self.play_untapped("Forest")

    def cast_amulet_of_vigor(self):
        self.board.append("Amulet of Vigor")
        return [self]

    def cast_ancient_stirrings(self):
        cards = self.deck[:5]
        # Put everything on the bottom, create a new card for the hand
        self.deck = self.deck[5:] + cards
        cards = {c for c in cards if carddata.is_colorless(c)}
        if not cards:
            clone = self.clone()
            clone.lines[-1] += ", whiff"
            return [clone]
        clones = []
        for c in cards:
            clone = self.clone()
            clone.lines[-1] += ", take " + carddata.display(c)
            clone.hand.append(c)
            clones.append(clone)
        return clones

    def cast_arboreal_grazer(self):
        lands = {c for c in self.hand if carddata.is_land(c)}
        if not lands:
            self.lines[-1] += ", whiff"
            return [self]
        clones = []
        for land in lands:
            clone = self.clone()
            clone.lines[-1] += ", play " + carddata.display(land)
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
        cards = {c for c in cards if carddata.is_permanent(c)}
        if not cards:
            clone = self.clone()
            clone.lines[-1] += ", whiff"
            return [clone]
        clones = []
        for c in cards:
            clone = self.clone()
            clone.lines[-1] += ", take " + carddata.display(c)
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
        cards = {c for c in cards if carddata.is_land(c)}
        if not cards:
            clone = self.clone()
            clone.lines[-1] += ", whiff"
            return [clone]
        clones = []
        for c in cards:
            clone = self.clone()
            clone.lines[-1] += ", take " + carddata.display(c)
            clone.hand.append(c)
            clones += clone.play_tapped(c)
        return clones

    def cast_explore(self):
        self.lines[-1] += ", draw %s" % carddata.display(self.deck[0])
        self.draw(silent=True)
        self.drops += 1
        return [self]

    def cast_growth_spiral(self):
        self.lines[-1] += ", draw %s" % carddata.display(self.deck[0])
        self.draw(silent=True)
        self.drops += 1
        return [self]

    def cast_manamorphose(self):
        clones = []
        for m in ["UU", "UG", "GG"]:
            clone = self.clone()
            clone.pool += mana.Mana(m)
            clone.lines[-1] += ", " + str(clone.pool) + " in pool"
            clone.lines[-1] += ", draw " + carddata.display(clone.deck[0])
            clone.draw(silent=True)
            clones.append(clone)
        return clones

    def cast_oath_of_nissa(self):
        cards = self.deck[:3]
        # Put everything on the bottom, create a new card for the hand
        self.deck = self.deck[3:] + cards
        cards = {c for c in cards if carddata.is_creature(c) or carddata.is_land(c)}
        if not cards:
            clone = self.clone()
            clone.lines[-1] += ", whiff"
            return [clone]
        clones = []
        for c in cards:
            clone = self.clone()
            clone.lines[-1] += ", take " + carddata.display(c)
            clone.hand.append(c)
            clones.append(clone)
        return clones

    def cast_opt(self):
        cards = self.deck[:2]
        self.deck = self.deck[2:] + cards
        clones = []
        for c in cards:
            clone = self.clone()
            clone.lines[-1] += ", take " + carddata.display(c)
            clone.hand.append(c)
            clones.append(clone)
        return clones

    def cast_primeval_titan(self):
        self.done = True
        return [self]

    def cast_sakura_tribe_scout(self):
        self.board.append("Sakura-Tribe Scout")
        return [self]

    def cast_sakura_tribe_elder(self):
        cards = {x for x in set(self.deck) if carddata.is_basic_land(x)}
        clones = []
        for card in cards:
            clone = self.clone()
            clone.lines[-1] += ", grab " + carddata.display(card)
            clone.hand.append(card)
            clone.play_tapped(card)
            clones.append(clone)
        return clones

    def cast_search_for_tomorrow(self):
        cards = {x for x in set(self.deck) if carddata.is_basic_land(x)}
        clones = []
        for card in cards:
            clone = self.clone()
            clone.lines[-1] += ", grab " + carddata.display(card)
            clone.hand.append(card)
            clone.play_untapped(card)
            clones.append(clone)
        return clones

    def cast_simian_spirit_guide(self):
        return [self]

    def cast_summoners_pact(self):
        clones = []
        for c in set(self.deck):
            if not carddata.is_creature(c) or not carddata.is_green(c):
                continue
            clone = self.clone()
            clone.lines[-1] += ", get " + carddata.display(c)
            clone.hand.append(c)
            clone.debt += mana.Mana("2GG")
            clones.append(clone)
        return clones

    def cast_through_the_breach(self):
        if "Primeval Titan" not in self.hand:
            return []
        # Stick a dummy Amulet in play to signal a "fast" win
        self.board.append("Amulet of Vigor")
        self.done = True
        return [self]

    def cast_trinket_mage(self):
        clones = []
        for card in set(self.deck):
            if not carddata.is_artifact(card) or carddata.get_cmc(card) > 1:
                continue
            clone = self.clone()
            clone.lines[-1] += ", grab " + carddata.display(card)
            clone.hand.append(card)
            clones.append(clone)
        return clones

    def activate_search_for_tomorrow(self):
        self.suspend.append("Search for Tomorrow..")
        return [self]

    def activate_sheltered_thicket(self):
        self.lines[-1] += ", draw " + carddata.display(self.deck[0])
        self.draw(silent=True)
        self.lines.pop(-1)
        return [self]

    def activate_simian_spirit_guide(self):
        self.pool += mana.Mana("1")
        self.lines[-1] += ", " + str(self.pool) + " in pool"
        return [self]

    def activate_tolaria_west(self):
        clones = []
        for card in set(self.deck):
            if carddata.get_cmc(card) != 0:
                continue
            clone = self.clone()
            clone.lines[-1] += ", grab " + carddata.display(card)
            clone.hand.append(card)
            clones.append(clone)
        return clones
