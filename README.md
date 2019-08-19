# Modeling Amulet Titan

The script `amulet.py` models games of Amulet Titan by exhaustive search. It's not particularly efficient (a few seconds per game) but if there's a way to get Titan on the table by turn this model is guaranteed to find it. You can read [here](http://charles.uno/valakut-simulation/) about my work on Valakut with a similar model.

# Usage

Default usage is simply:

```
$ ./amulet.py
```

This tells the model to goldfish hands on loop until it's killed with `Ctrl-C`. Deck lists will be chosen at random from those available in `decks/`. To limit the run to certain deck lists, give the names of those lists as sequential arguments:

```
$ ./amulet.py amulet-00 amulet-03
```

To see what's going on under the hood, use the `--debug` flag. This will cause the model to stop as soon as it finds a hand that can get Primeval Titan on the table, and print the line-by-line choices it used to get there. Output will look something like:

```
$ ./amulet.py --debug
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

# Results

The result of each run gets stored in `data/`. It keeps track of what turn Titan hit the table, play/draw, and whether it's a "fast" Titan via Amulet of Vigor or Through the Breach. To see a summary of that data, use:

```
$ ./amulet.py --report
name             turn 2      turn 3      turn 4
amulet-00      2% ±  0%   27% ±  1%   63% ±  1%
amulet-01      4% ±  0%   26% ±  1%   60% ±  1%
amulet-02      2% ±  0%   30% ±  1%   67% ±  1%
amulet-03      4% ±  0%   33% ±  1%   72% ±  1%
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

The `--debug` flag can be used for validation. For example, 

```
$ ./amulet.py amulet-02 --debug "Oath of Nissa"
```

Will run `amulet-02` on loop until it finds a hand that makes use of Oath of Nissa. 

# TODO

Add verbose logging to keep track of the complete lines from many games. Would be good to have the ability to grep through them to see (for example) what the best turn one play tends to be. 

Add handling for Vesuva.

Add handling for Cavern of Souls.

Update the output for hands with no solution to be CSV. We also want to know play/draw data for those games. 

Update command line to accept globs. 

Update the driver and/or library names. Annoying that we can't tab-complete. Also this doesn't just do Amulet anymore. 
