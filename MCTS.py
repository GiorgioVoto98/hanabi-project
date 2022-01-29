import math
from multiprocessing.managers import State


class MCTS:
    def __init__(self, State, iterations=400):
        self.StartState = State
        self.iterations = iterations

    def execute(self, State):
        if (State.nexp) == 0:
            State.choosen()
            res = State.eval()
            State.totalVal += res
            return res
        else:
            State.choosen()
            if (len(State.childrens) == 0):
                self._expand(State)
            # valutare tra quelli presenti quale mi conviene scegliere
            child_chosen = self._choose(State)
            res = self.execute(child_chosen)
            State.totalVal += res
            return res

    def _expand(self, State):
        av_actions = State.available_actions()
        for new_states in av_actions:
            State.childrens.append(new_states)
            # ho una serie di azioni che mi portano a nuovi stati

    def _choose(self, State):
        child_chosen = None
        UCB_chosen = -1
        for child_state in State.childrens:
            UCB = 1e6
            if child_state.nexp != 0:
                UCB = (child_state.totalVal / child_state.nexp) + 2 * (math.log(self.StartState.nexp) / child_state.nexp)
            if UCB > UCB_chosen:
                UCB_chosen = UCB
                child_chosen = child_state
        return child_chosen

    def best_action(self):
        for i in range(self.iterations):
            if not self.StartState.game.get_current_player().redeterminize(self.StartState.game):
                break
            self.execute(self.StartState)
        child_chosen = None
        best_res = -1
        for child in self.StartState.childrens:
            avg_res = child.totalVal/child.nexp
            if avg_res > best_res:
                best_res = avg_res
                child_chosen = child
        return child_chosen.parent_action

        # best_child = None
        # for child in self.StartState.childrens:

class State:
    def __init__(self, parent_action):
        self.parent_action = parent_action
        self.childrens = []
        self.totalVal = 0
        self.nexp = 0

    def available_actions(self):
        return (State)

    def add_childrens(self, new_state):
        self.childrens.append(new_state)

    def choosen(self):
        self.nexp += 1

