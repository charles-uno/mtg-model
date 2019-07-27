import random

from . import io, state

class GameStateManager(object):

    def __init__(self, name, draw=False):
        deck = io.load(name)
        print(io.display(*deck))
        self.turn = 1
        initial_state = state.GameState(deck=deck, turn=1)
        initial_state.draw(8 if draw else 7)
        self.states = [initial_state]

    def next_turn(self):
        self.turn += 1
        print("Turn", self.turn)
        if any( x.done for x in states ):
            return
        old_states, new_states = self.states, []
        while old_states:
            print(len(old_states), "old states,", len(new_states), "new states")
            for state in old_states.pop().next_states():
                if state.turn < self.turn:
                    old_states.append(state)
                else:
                    new_states.append(state)
        self.states = new_states

    def done(self):
        done_states = [ x for x in self.states if x.done ]
        if done_states:
            return done_states.pop()
        else:
            return None

    def peek(self):
        state = sorted( (len(x.lines), x) for x in self.states )[-1][-1]
        state.report()
