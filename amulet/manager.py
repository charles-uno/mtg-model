import random

from . import io, state

class GameStateManager(object):

    def __init__(self, name, draw=False):
        deck = io.load(name)
        print(io.display(*deck))
        self.turn = 0
        self.states = [state.GameState(deck=deck)]
        self.states[0].draw( 8 if draw else 7 )





    def next_turn(self):

        self.turn += 1

        old_states, new_states = self.states, []

        print(len(old_states), "old states,", len(new_states), "new states")


        while old_states:

            print(len(old_states), "old states,", len(new_states), "new states")

            for state in old_states.pop().next_states():

                print(state)

                if state.turn < self.turn:
                    old_states.append(state)
                else:
                    new_states.append(state)

        self.states = new_states




    def peek(self):
        random.choice(self.states).report()
