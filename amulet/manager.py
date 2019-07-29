import os
import random

from . import io, state

# ----------------------------------------------------------------------

class NoSolution(Exception):
    pass

class TooManyStates(RuntimeError):
    pass

def simulate(name):
    outfile = "out/%s.out" % name
    deck = io.load(name)
    initial_state = state.GameState(hand=deck[:7], deck=deck[7:], draw=random.randrange(2))
    try:
        final_state = play_turns(initial_state)
        write(final_state.summary(), outfile)
        return final_state
    except NoSolution:
        write("# no solution", outfile)
        return
    except TooManyStates:
        write("# no solution", outfile)
        return

# ----------------------------------------------------------------------

def write(line, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(line)
    with open(path, "a") as handle:
        handle.write(line + "\n")

# ----------------------------------------------------------------------

MAX_TURNS = 4

def play_turns(state):
    states = {state}
    for _ in range(MAX_TURNS+1):
        states = play_turn(states)
    # If we found a solution, that'll be the only state
    if len(states) == 1 and sorted(states)[0].done:
        return states.pop()
    else:
        raise NoSolution

# ----------------------------------------------------------------------

MAX_STATES = 3e4

def play_turn(states):
    # If we finished last time around, short-circuit this one
    if len(states) == 1 and sorted(states)[0].done:
        return states
    # Figure out what turn we're playing to
    turn = min( x.turn for x in states ) + 1
    # Keep iterating over each state until its children hit that turn
    new_states = set()
    while states:
        for state in states.pop().next_states():
            # Once we find a winning line, we're done
            if state.done:
                return {state}
            if state.turn < turn:
                states.add(state)
            else:
                new_states.add(state)
        # If things get out of hand, bail
        if len(states) + len(new_states) > MAX_STATES:
            raise TooManyStates
    return new_states
