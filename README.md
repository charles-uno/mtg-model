# Modeling Amulet Titan

The script `driver.py` models games of Amulet Titan by exhaustive search. It's not particularly efficient (a few seconds per game) but if there's a way to get Titan on the table by turn this model is guaranteed to find it. You can read [here](http://charles.uno/valakut-simulation/) about my work on Valakut with a similar model.


# Usage

Default usage is simply:

```
$ ./driver.py
```

This tells the model to goldfish hands on loop until it's killed with `Ctrl-C`. Deck lists will be chosen at random from those available in `decks/`. To limit the run to certain deck lists, give the names of those lists as sequential arguments:

```
$ ./driver.py amulet-00 amulet-03
```

To see what's going on under the hood, use the `--debug` flag. This will cause the model to stop as soon as it finds a hand that can get Primeval Titan on the table, and print the line-by-line choices it used to get there. Output will look something like:

```
$ ./driver.py --debug
   1      amulet-00 3,1,1,0

Draw AmuletofVigor 2*AncientStirrings Forest 2*PrimevalTitan SimicGrowthChamber
---- turn 1
Play Forest, G in pool
Cast AncientStirrings, mill 2*AmuletofVigor ArborealGrazer 2*PrimevalTitan, grab AmuletofVigor
---- turn 2, G in pool, draw AncientStirrings
Cast AmuletofVigor
Play SimicGrowthChamber, GU in pool, bounce SimicGrowthChamber
Cast AmuletofVigor
Cast AncientStirrings, mill Forest GemstoneMine 2*PrimevalTitan SimicGrowthChamber, grab GemstoneMine
---- turn 3, G in pool, draw AmuletofVigor
Cast AmuletofVigor
Play SimicGrowthChamber, GU in pool, GGUU in pool, GGGUUU in pool, bounce Forest
Cast PrimevalTitan
```


# Results

The result of each run gets stored in `output/`. It keeps track of what turn Titan hit the table, play/draw, whether it's a "fast" Titan via Amulet of Vigor or Through the Breach. For hands that fail to converge, we also track whether we found no solution or abandoned the hand due to overflow. To see the numbers, use:

```
$ ./driver.py --results
name             turn 2      turn 3      turn 4
amulet-00      2% ±  0%   27% ±  1%   63% ±  1%
amulet-01      4% ±  0%   26% ±  1%   60% ±  1%
amulet-02      2% ±  0%   30% ±  1%   67% ±  1%
amulet-03      4% ±  0%   33% ±  1%   72% ±  1%
```

Uncertainties are based on a [normal approximation](https://alexgude.com/blog/fate-dice-intervals/).


# Implementation

The model starts out with a full hand and an empty board. Each time it's faced with a choice, it clones the game state and tries all possible options. Most of its plays are terrible. For example, the model will try to play Summoner's Pact on turn one then pass without making a land drop. But by trying all possible lines, we ensure that we won't miss any winning lines. With slight tweaks, the model could pursue Tron or Hogaak just as single-mindedly.

There are a few simplifying assumptions, especially surrounding Pact triggers. Everything is handled at sorcery speed, so we don't consider the possibility of activating Sakura-Tribe Scout on our upkeep. We also don't empty the mana pool until the end of the turn. So if we have to pay for a Pact trigger with Simic Growth Chamber, Forest, and Boros Garrison, we may (incorrectly) spend the last mana on our main phase.

The most expensive consideration is mana. We care about both green and blue mana, so there's a combinatorial explosion every time we have lands on the board that can tap for both. To mitigate this, we keep game state objects in sets to automatically collapse duplicates. This means that game states themselves must be immutable. In essence, each game state is a `namedtuple` object. Operations like drawing a card or playing a land create a new game state rather than changing the old one.


# Adding Decks and Cards

To look at a different list, create a new file under `decks/` and put your list in it. Blank lines and comments (starting with `#`) are ignored by the parser. If the deck uses new cards, fill in their color, types, etc in `carddata.yaml`.

If a land does something interesting when played, create a function to explain it. See `GameState.play_simic_growth_chamber` in `mtg/state.py` for reference. Similarly, casting a spell will look for something like `GameState.cast_ancient_stirrings`, and activating an ability from hand will look for something like `GameState.discard_tolaria_west`.

This model is well-suited to quantify goldfishing impacts of...

- Trinket Mage vs Coalition Relic vs Elvish Rejuvenator
- Arboreal Grazer vs Sakura-Tribe Scout
- Explore vs Growth Spiral
- Opt, Serum Visions, Oath of Nissa, Bond of Flourishing, Manamorphose, Street Wraith, etc
- Lotus Field vs Simian Spirit Guide
- Tranquil Thicket vs Zhalfirin Void vs Temple of Mystery vs Sheltered Thicket


# Backlog

Parallelism! Game states are immutable and they don't look at any shared variables. Could readily make use of multithreading or multiprocessing. This could significantly improve performance since the model is CPU-bound.

Add verbose logging to keep track of the complete lines from many games. Would be good to have the ability to grep through them to see (for example) what the best turn one play tends to be.

Add handling for Vesuva and Cavern of Souls. At the moment, they're just counted as colorless lands. Also Aether Hub and/or Gemstone Mine. At the moment, they just tap for whatever we want.

Update command line to accept globs for deck names.
