from __future__ import annotations
from copy import deepcopy
import os
import numpy as np

from action import Action
import utils as ut

def MCTS2(game, num_iterations=200):
    # the player in the node is the one who did the previous move
    root_player = game.current_player
    root = Hanabi_Node(game, root_player, parent_action=None, parent=None)
        
    for _ in range(num_iterations):
        node = root

        # SELECTION (tree traversal)
        while len(node.children) != 0 and len(node.states_to_try) == 0:  # until terminal or not fully expanded node
            node = node.selection()

        # EXPANSION        
        if len(node.states_to_try) > 0:
            node = node.expand()

        # SIMULATION (ROLLOUT)
        score = node.simulate()

        # BACKPROPAGATION
        node.backpropagate(score)
            
    # Return most promising move from root (highest score)
    best_node = max(root.children, key=lambda x: x.total_score/x.num_visits)
    return best_node.parent_action


class Hanabi_Node():
    def __init__(self, game, root_player, parent_action: Action, parent: Hanabi_Node):
        self.game = deepcopy(game)
        self.root_player = root_player
        self.parent_action = parent_action
        self.parent = parent
        self.total_score = 0
        self.num_visits = 0
        self.states_to_try = self.next_states()
        self.children = []

    def next_states(self):
        end, _ = self.game.is_game_over()
        if end:
            print("game over")
            return []

        next_states = []
        player = self.game.get_current_player()
        
        self.exit_node(player)
        
        actions = player.best_actions(self.game)
        # for action in actions:
        #     new_game = deepcopy(self.game)
        #     new_game.execute_action(action)
        #     next_states.append((new_game, action))

        self.enter_node(player)

        # return next_states
        return actions

    def enter_node(self, player):
        if self.root_player != player.name:
            player.hand = player.real_hand

    def exit_node(self, player):
        if self.root_player != player.name:
            player.redeterminize(self.game)

    def score(self):
        return self.game.eval()

    def selection(self):
        def UCB1(node):
            c = np.sqrt(2)
            exploitation = node.total_score / node.num_visits
            exploration = c * np.sqrt(np.log(node.parent.num_visits) / node.num_visits)
            return exploitation + exploration
        
        return max(self.children, key=UCB1)

    def expand(self):
        idx = np.random.choice(list(range(len(self.states_to_try))))
        # new_game, action = self.states_to_try[idx]

        action = deepcopy(self.states_to_try[idx])
        new_game = deepcopy(self.game)
        new_game.execute_action(action)
        
        child = Hanabi_Node(new_game, self.root_player, action, self)
        self.children.append(child)

        self.states_to_try.pop(idx)

        return child

    def simulate(self):
        temp_game = deepcopy(self.game)
        
        # return np.random.randint(0, 25)

        while True:
            end, score = temp_game.is_game_over()
            if end:
                return score
            player = temp_game.get_current_player()
            actions = player.best_actions(temp_game)
            random_action = np.random.choice(actions)
            temp_game.execute_action(random_action)


    def backpropagate(self, score):
        node = self
        while node is not None:
            node.total_score += score      
            node.num_visits += 1
            node = node.parent

