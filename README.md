# Modeling Amulet Titan

The script `amulet.py` models games of Amulet Titan by exhaustive search. It's not particularly efficient (a few seconds per game) but if there's a way to get Titan on the table by turn this model is guaranteed to find it. You can read [here](http://charles.uno/valakut-simulation/) about my work on Valakut with a similar model.

# Usage

Punch in:

```
./amulet.py 1
```

This will model a single game using a randomly-chosen list from `decks/`. It'll also print out the line-by-line actions it took to get Primeval Titan on the table, something like:

```
[0] [ amulet-16] 2,1,1
Draw AmuletofVigor 2*Forest PrimevalTitan RadiantFountain SakuraTribeScout SummonersPact
---- turn 1, 0 in pool, draw AncientStirrings
Play Forest, G in pool
Cast SakuraTribeScout
---- turn 2, G in pool, draw SelesnyaSanctuary
Cast AmuletofVigor
Play SelesnyaSanctuary, 1G in pool, bounce SelesnyaSanctuary
Cast SummonersPact, get AzusaLostbutSeeking
Cast AncientStirrings, take AmuletofVigor
Cast AmuletofVigor
Play SelesnyaSanctuary, 1G in pool, 2GG in pool, bounce SelesnyaSanctuary
Cast AzusaLostbutSeeking
Play SelesnyaSanctuary, 1GG in pool, 2GGG in pool, bounce SelesnyaSanctuary
Play SelesnyaSanctuary, 3GGGG in pool, 4GGGGG in pool, bounce Forest
Cast PrimevalTitan
```

To get a bunch of data for a specific deck, use:

```
./amulet.py 1000 amulet-03
```

This will run the list `decks/amulet-03.in` for a thousand games and store the results in `out/amulet-03.out`. it'll also print the line-by-line choices for the final game it solves.

# Results

The result of each run gets stored in `data/DECKNAME.csv`. It keeps track of what turn Titan hit the table, play/draw, and whether it's a "fast" Titan via Amulet of Vigor or Through the Breach. To see a summary of that data, run with no arguments:

```
./amulet.py
```

Which will output something like:

```
name             turn 2      turn 3      turn 4
amulet-00      2% ±  0%   27% ±  1%   63% ±  2%
amulet-01      4% ±  0%   26% ±  1%   60% ±  2%
amulet-02      2% ±  0%   30% ±  1%   67% ±  2%
amulet-03      4% ±  0%   33% ±  1%   72% ±  2%
```

Uncertainties are based on a [normal approximation](https://alexgude.com/blog/fate-dice-intervals/). 

# Implementation

The model starts out with a full hand and an empty board. Each time it's faced with a choice, it clones the game state and tries all possible options. For example, if it's got one in hand, one clone will cast Summoner's Pact on turn one then pass without making a land drop. This approach isn't particularly efficient -- most of the lines are terrible -- but it guarantees that we'll always find the fastest way to get Primeval Titan on the table, even when faced with non-trivial choices. With slight tweaks, the model could instead try to assemble Tron or cast Hogaak just as single-mindedly.

There are a pair of significant simplifying assumptions:

1. Everything happens at sorcery speed. That means we don't consider the possibility of activating Sakura-Tribe Scout on our upkeep to pay for Pact.
2. We don't have handling for the tricky lands like Cavern of Souls or Vesuva. We use Cavern as a Radiant Fountain and Vesuva as a Bojuka Bog -- it enters tapped and does not produce green or blue.

# Adding Decks and Cards

To look at a different list, create a new file under `decks/` and put your list in it. Blank lines and comments (starting with `#`) are ignored by the parser. If the deck uses new cards, fill in their color, types, etc in `carddata.yaml`. Then:

- For land Foo, create the function `play_foo(self)` in the `GameState` object in `amulet/gamestate.py`
- For spell Foo, create the function `cast_foo(self)`
- For anything with an additional mode (such as cycling on Shefet Monitor, transmute on Tolaria West, suspend on Search for Tomorrow), create the function `activate_foo(self)`

The function should create game state clones as needed, and move cards between zones per the instructions on the card. See the existing functions for examples. If you try to use a card but forget to enter a function, the model will tell you what's missing.

# TODO

Add verbose logging to keep track of the complete lines from many games. Would be good to have the ability to grep through them to see (for example) what the best turn one play tends to be. 

Add handling for Vesuva.

Add handling for Cavern of Souls.

Update the output for hands with no solution to be CSV. We also want to know play/draw data for those games. 
