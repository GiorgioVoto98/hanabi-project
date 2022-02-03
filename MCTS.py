import math
from copy import deepcopy


class MCTS:
    def __init__(self, state, iterations=400):
        self.startState = state
        self.iterations = iterations

    def execute(self, state):
        if state.nexp == 0:
            state.chosen()
            res = state.eval()
            state.totalVal += res
            return res
        else:
            state.chosen()
            if len(state.children) == 0:
                self.expand(state)
            child_chosen = self.choose(state)
            if child_chosen is not None:
                res = self.execute(child_chosen)
                state.totalVal += res
                return res
            else:
                res = state.eval()
                state.totalVal += res
                return res

    def expand(self, state):
        av_actions = state.available_actions()
        for new_states in av_actions:
            state.children.append(new_states)

    def choose(self, state):
        child_chosen = None
        UCB_chosen = -1
        if len(state.children) > 0:
            for child_state in state.children:
                UCB = 1e6
                if child_state.nexp != 0:
                    UCB = (child_state.totalVal / child_state.nexp) + 0.1 * math.sqrt(math.log(state.nexp) / child_state.nexp)
                if UCB > UCB_chosen:
                    UCB_chosen = UCB
                    child_chosen = child_state
            return child_chosen
        return None

    def best_action(self):
        for _ in range(self.iterations):            
            if not self.startState.game.get_current_player().redeterminize(self.startState.game):
                break
            self.execute(self.startState)
        
        child_chosen = None
        best_res = -1
        for child in self.startState.children:
            avg_res = child.totalVal/child.nexp
            if avg_res > best_res:
                best_res = avg_res
                child_chosen = child
        return child_chosen.parent_action


class MCTSHanabiNode:
    def __init__(self, parent_action, game, root_player):
        self.parent_action = parent_action
        self.game = deepcopy(game)
        self.root_player = root_player
        self.children = []
        self.totalVal = 0
        self.nexp = 0

    def chosen(self):
        self.nexp += 1

    def available_actions(self):
        player = self.game.get_current_player()
        self.exit_node(player)
        actions = player.best_actions(self.game)
        self.enter_node(player)
        av_actions = []
        for action in actions:
            av_actions.append(self.execute_action(action))
        return av_actions

    def eval(self):
        return self.game.eval()

    def execute_action(self, action):
        new_game = deepcopy(self.game)
        new_game.execute_action(action)
        return MCTSHanabiNode(action, new_game, self.root_player)

    def enter_node(self, player):
        if self.root_player != player.name:
            player.hand = player.real_hand

    def exit_node(self, player):
        if self.root_player != player.name:
            player.redeterminize(self.game)
