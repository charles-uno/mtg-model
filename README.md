# Modeling Amulet Titan

The script `amulet.py` models games of Amulet Titan by exhaustive search. It's not particularly efficient (a few seconds per game) but if there's a way to get Titan on the table by turn this model is guaranteed to find it. I applied a similar model to Valakut [here](http://charles.uno/valakut-simulation/)

# Usage 

```
./amulet.py 1
```

This will model a single game using a randomly-chosen list from `decks/`. It'll also print out the line-by-line actions it took to get Primeval Titan on the table.

> Todo: add sample output

To get a bunch of data for a specific deck, use:

```
./amulet.py 1000 amulet-03
```

This will run the list `decks/amulet-03.in` for a thousand games and store the results in `out/amulet-03.out`. it'll also print the love-by-line choices for the final game it solves.
To see a summary of the data stored in all output file, run with no arguments:

```
./amulet.py
```
 
# Implementation

> This section of a bit of a work in progress.

Basically, the model attempts all sequences of legal plays. It tries thousands of different lines for each hand. Most lines are terrible, like passing the turn without making a land drop, or playing Pact on turn 1, etc.

The most expensive part is handling multiple colors of mana. With Valakut, it was easy -- you have green and "other." But Amulet also needs to track blue for Tolaria West and Trinket Mage. That means a lot of different ways to tap, and a lot of different ways to pay costs.

Notably, everything pretty much happens at sorcery speed. The only place this really matters is paying for Pact. We currently neglect the possibility of activating Sakura-Tribe Scout on upkeep to pay for Pact.

# Adding Cards

Right now, the model includes the cards you need for Titan Breach and Amulet Titan, more or less. We fudge the hard ones, like Cavern of Souls and Vesuva. To add more cards, add them to `data/cards.yaml` and define functions in `amulet/state.py` to explain what the card does. 

> More explanation needed here. It'll yell at you if you try to include a card in a deck but a function is missing.
