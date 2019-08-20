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
        clones = []
        for card in carddata.colorless(self.tuck(5)):
            clones.append(self.clone_grab(card))
        return clones or [self.clone(", whiff")]

    def cast_arboreal_grazer(self):
        clones = []
        for card in carddata.lands(self.hand):
            clone = self.clone(", play", carddata.display(card))
            clones += clone.play_tapped(card)
        return clones or [self.clone(", whiff")]

    def cast_azusa_lost_but_seeking(self):
        if "Azusa, Lost but Seeking" not in self.board:
            self.drops += 2
            self.board.append("Azusa, Lost but Seeking")
        return [self]

    def cast_bond_of_flourishing(self):
        clones = []
        for card in carddata.permanents(self.tuck(3)):
            clones.append(self.clone_grab(card))
        return clones or [self.clone(", whiff")]

    def cast_cantrip(self):
        self.draw(1)
        return [self]

    def cast_chromatic_star(self):
        self.board.append("Chromatic Star")
        return [self]

    def cast_elvish_rejuvenator(self):
        clones = []
        for card in carddata.lands(self.tuck(5)):
            clone = self.clone_grab(card)
            clones += clone.play_tapped(card)
        return clones or [self.clone(", whiff")]

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
            clone.note_pool(m)
            clone.draw(1)
            clones.append(clone)
        return clones

    def cast_oath_of_nissa(self):
        clones = []
        for card in carddata.creatures_lands(self.tuck(3)):
            clones.append(self.clone_grab(card))
        return clones or [self.clone(", whiff")]

    def cast_opt(self):
        clones = self.clone_scry(1)
        [x.draw(1) for x in clones]
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
            clones += clone.play_tapped(card)
        return clones

    def cast_search_for_tomorrow(self):
        clones = []
        for card in carddata.basic_lands(self.deck):
            clone = self.clone_grab(card)
            clones += clone.play_untapped(card)
        return clones

    def cast_silhana_wayfinder(self):
        clones = []
        for card in carddata.creatures_lands(self.tuck(4)):
            clone = self.clone(", take", carddata.display(card))
            clone.deck = [card] + clone.deck
            clones.append(clone)
        # TODO: we can choose not to put anything on top.
        return clones or [self.clone(", whiff")]

    def cast_simian_spirit_guide(self):
        return [self]

    def cast_summoners_pact(self):
        clones = []
        for card in carddata.green_creatures(self.deck):
            clone = self.clone_grab(card)
            clone.debt += "2GG"
            clones.append(clone)
        return clones

    def cast_sylvan_scrying(self):
        clones = []
        for card in carddata.lands(self.deck):
            clones.append(self.clone_grab(card))
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
        for card in carddata.trinkets(self.deck):
            clones.append(self.clone_grab(card))
        return clones

    def activate_chromatic_star(self):
        if "Chromatic Star" not in self.board:
            return []
        clones = []
        for m in "GU":
            clone = self.clone()
            clone.board.remove("Chromatic Star")
            clone.note_pool(m)
            clone.draw(1)
            clones.append(clone)
        return clones

    def activate_expedition_map(self):
        if "Expedition Map" not in self.board:
            return []
        clones = []
        for card in carddata.lands(self.deck):
            clone = self.clone_grab(card)
            clone.board.remove("Expedition Map")
            clones.append(clone)
        return clones

    def activate_search_for_tomorrow(self):
        self.suspend.append("Search for Tomorrow..")
        return [self]

    def activate_shefet_monitor(self):
        for card in carddata.basic_lands(self.deck):
            clone = self.clone_grab(card)
            clones += clone.play_untapped(card)
        [x.draw(1) for x in clones]
        return clones

    def activate_sheltered_thicket(self):
        self.draw(1)
        return [self]

    def activate_simian_spirit_guide(self):
        self.note_pool("1")
        return [self]

    def activate_tranquil_thicket(self):
        self.draw(1)
        return [self]

    def activate_tolaria_west(self):
        clones = []
        for card in carddata.zeros(self.deck):
            clones.append(self.clone_grab(card))
        return clones
