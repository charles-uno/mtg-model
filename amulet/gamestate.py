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
        lands = [c for c in self.board if carddata.is_land(c)]
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

    def play_temple_of_mystery(self):
        return self.clone_scry(1)

    def play_tolaria_west(self):
        return [self]

    def play_tranquil_thicket(self):
        return [self]

    def play_valakut_the_molten_pinnacle(self):
        return [self]

    def play_wooded_foothills(self):
        self.board.remove("Wooded Foothills")
        self.hand.append("Forest")
        return self.play_untapped("Forest")

    def play_zhalfirin_void(self):
        return self.clone_scry(1)

    def cast_amulet_of_vigor(self):
        self.board.append("Amulet of Vigor")
        return [self]

    def cast_ancient_stirrings(self):
        cards = self.deck[:5]
        # Put everything on the bottom, create a new card for the hand
        self.deck = self.deck[5:] + cards
        cards = carddata.colorless(cards)
        if not cards:
            clone = self.clone()
            clone.lines[-1] += ", whiff"
            return [clone]
        clones = []
        for c in cards:
            clones.append(self.clone_grab(c))
        return clones

    def cast_arboreal_grazer(self):
        lands = carddata.lands(self.hand)
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
        cards = carddata.permanents(cards)
        if not cards:
            clone = self.clone()
            clone.lines[-1] += ", whiff"
            return [clone]
        clones = []
        for c in cards:
            clones.append(self.clone_grab(c))
        return clones

    def cast_cantrip(self):
        self.draw(1)
        return [self]

    def cast_chromatic_star(self):
        self.board.append("Expedition Map")
        return [self]

    def cast_elvish_rejuvenator(self):
        # Put everything on the bottom, create a new card for the hand
        cards = carddata.lands(self.deck[:5])
        self.deck = self.deck[5:] + self.deck[:5]
        if not cards:
            clone = self.clone()
            clone.lines[-1] += ", whiff"
            return [clone]
        clones = []
        for c in cards:
            clone = self.clone_grab(c)
            clones += clone.play_tapped(c)
        return clones

    def cast_expedition_map(self):
        self.board.append("Expedition Map")
        return [self]

    def cast_explore(self):
        self.draw(1)
        self.drops += 1
        return [self]

    def cast_growth_spiral(self):
        self.draw(1)
        self.drops += 1
        return [self]

    def cast_manamorphose(self):
        clones = []
        for m in ["UU", "UG", "GG"]:
            clone = self.clone()
            clone.pool += mana.Mana(m)
            clone.note_pool()
            clone.draw(1)
            clones.append(clone)
        return clones

    def cast_oath_of_nissa(self):
        # Put everything on the bottom, create a new card for the hand
        cards = carddata.creatures(self.deck[:3]) | carddata.lands(self.deck[:3])
        self.deck = self.deck[3:] + self.deck[:3]
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
        cards, self.deck = self.deck[:2], self.deck[2:] + self.deck[:2]
        clones = []
        for c in cards:
            clones.append(self.clone_grab(c))
        return clones

    def cast_primeval_titan(self):
        self.done = True
        return [self]

    def cast_sakura_tribe_scout(self):
        self.board.append("Sakura-Tribe Scout")
        return [self]

    def cast_sakura_tribe_elder(self):
        clones = []
        for card in carddata.basic_lands(self.deck):
            clone = self.clone_grab(card)
            clone.play_tapped(card)
            clones.append(clone)
        return clones

    def cast_search_for_tomorrow(self):
        clones = []
        for card in carddata.basic_lands(self.deck):
            clone = self.clone_grab(card)
            clone.play_untapped(card)
            clones.append(clone)
        return clones

    def cast_silhana_wayfinder(self):
        # Put everything on the bottom, create a new card for the hand
        cards = carddata.creatures(self.deck[:4]) | carddata.lands(self.deck[:4])
        self.deck = self.deck[4:] + self.deck[:4]
        if not cards:
            clone = self.clone()
            clone.lines[-1] += ", whiff"
            return [clone]
        clones = []
        for c in cards:
            clone = self.clone()
            clone.lines[-1] += ", take " + carddata.display(c)
            clone.deck = [c] + clone.deck
            clones.append(clone)
        # We can choose not to put anything on top.
        clone = self.clone()
        clone.lines[-1] += ", pass on " + carddata.display(*cards)
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

    def cast_sylvan_scrying(self):
        clones = []
        for card in carddata.lands(self.deck):
            clone = self.clone_grab(card)
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
            if not carddata.is_artifact(card) or carddata.cmc(card) > 1:
                continue
            clone = self.clone_grab(card)
            clones.append(clone)
        return clones

    def activate_chromatic_star(self):
        if "Chromatic Star" not in self.board:
            return []
        clones = []
        for m in "GU":
            clone = self.clone()
            clone.pool += mana.Mana(m)
            clone.note_pool()
            clone.draw(1)
            clones.append(clone)
        return clones

    def activate_expedition_map(self):
        if "Expedition Map" not in self.board:
            return []
        clones = []
        for card in carddata.lands(self.deck):
            clones.append(self.clone_grab(card))
        return clones

    def activate_search_for_tomorrow(self):
        self.suspend.append("Search for Tomorrow..")
        return [self]

    def activate_sheltered_thicket(self):
        self.draw(1)
        return [self]

    def activate_simian_spirit_guide(self):
        self.pool += mana.Mana("1")
        self.note_pool()
        return [self]

    def activate_tranquil_thicket(self):
        self.draw(1)
        return [self]

    def activate_tolaria_west(self):
        clones = []
        for card in set(self.deck):
            if carddata.cmc(card) != 0:
                continue
            clones.append(self.clone_grab(card))
        return clones
