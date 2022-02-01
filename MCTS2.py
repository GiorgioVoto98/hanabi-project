from __future__ import annotations
from copy import deepcopy
import os
import numpy as np
import time

from action import Action


def MCTS2(game, num_iterations=50):
    root_player = game.current_player
    root = Hanabi_Node(game, root_player, parent_action=None, parent=None)

    for _ in range(num_iterations):
        if not root.game.get_current_player().redeterminize(root.game):
            print("weird")
            os._exit(2)

        node = root

        # SELECTION (tree traversal)
        while len(node.children) != 0 and len(node.actions_to_try) == 0:  # until terminal or not fully expanded node
            node = node.selection()

        # EXPANSION        
        if len(node.actions_to_try) > 0:
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
        self.parent_action = deepcopy(parent_action)
        self.parent = parent
        self.total_score = 0
        self.num_visits = 0
        self.actions_to_try = self.next_actions()
        self.children = []

    def next_actions(self):
        end, _ = self.game.is_game_over()
        if end:
            return []

        player = self.game.get_current_player()
        self.exit_node(player)
        actions = player.best_actions(self.game)
        self.enter_node(player)

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
        idx = np.random.choice(list(range(len(self.actions_to_try))))
        action = deepcopy(self.actions_to_try[idx])
        new_game = deepcopy(self.game)
        new_game.execute_action(action)

        child = Hanabi_Node(new_game, self.root_player, action, self)
        self.children.append(child)
        self.actions_to_try.pop(idx)

        return child

    def simulate(self):
        # return np.random.randint(0, 26)
        
        # start = time.time()
        temp_game = deepcopy(self.game)
        while True:
            end, score = temp_game.is_game_over()
            if end:
                # end = time.time()
                # print("Sim time:", end-start)
                return score
            player = temp_game.get_current_player()
            best_action = player.action(temp_game)
            temp_game.execute_action(best_action)


    def backpropagate(self, score):
        node = self
        while node is not None:
            node.total_score += score      
            node.num_visits += 1
            node = node.parent

