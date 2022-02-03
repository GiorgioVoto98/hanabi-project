from __future__ import annotations
from copy import deepcopy
import os
import numpy as np
import random
import time

from action import Action


def MCTS2(game, num_iterations=400, seconds=1):
    print("CANDIDATES:")
    candidates = game.get_current_player().best_actions(game)
    for c in candidates:
        print('\t', c.cmd_string())

    root_player = game.current_player
    root = Hanabi_Node(game, root_player, parent_action=None, parent=None)

    if len(root.actions_to_try) == 1:
        return root.actions_to_try[0]

    # start_t = time.time()
    iterations = 0
    # while True:
    for _ in range(num_iterations):
        if not root.game.get_current_player().redeterminize(root.game):
            print("weird")
            os._exit(2)

        node = root

        # SELECTION (tree traversal)
        # until terminal or not fully expanded node
        while len(node.children) != 0 and len(node.actions_to_try) == 0:
            node = node.selection()

        # EXPANSION        
        if len(node.actions_to_try) > 0:
            node = node.expand()

        # SIMULATION (ROLLOUT)
        score = node.simulate()

        # BACKPROPAGATION
        node.backpropagate(score)

        # duration = time.time() - start_t
        iterations += 1
        # if duration > seconds:
            # break    
    print("Number of iterations:", iterations)

    # Return most promising move from root (highest score)
    best_node = max(root.children, key=lambda x: x.total_score/x.num_visits)

    print("CHOSEN:", best_node.parent_action.cmd_string())

    # stats(root)

    return best_node.parent_action


class Hanabi_Node():
    def __init__(self, game, root_player, parent_action: Action, parent: Hanabi_Node):
        self.game = deepcopy(game)
        self.root_player = root_player
        self.parent_action = parent_action
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
            # C = np.sqrt(2)
            C = 2
            exploitation = node.total_score / node.num_visits
            exploration = C * np.sqrt(np.log(node.parent.num_visits) / node.num_visits)
            return exploitation + exploration
        
        return max(self.children, key=UCB1)

    def expand(self):
        # idx = random.randrange(len(self.actions_to_try))
        idx = 0
        action = self.actions_to_try.pop(idx)
        new_game = deepcopy(self.game)
        new_game.execute_action(action)

        child = Hanabi_Node(new_game, self.root_player, action, self)
        self.children.append(child)

        return child

    def simulate(self):
        # return np.random.randint(0, 26)
        # return self.game.eval()

        temp_game = deepcopy(self.game)

        # start = time.time()
        # num_play = 0
        for _ in range(0):
        # while True:
        # while num_play <= 4:
            end, score = temp_game.is_game_over()
            if end:
                # end = time.time()
                # print("Sim time:", end-start)
                return temp_game.eval() / 25
            player = temp_game.get_current_player()
            best_action = player.action(temp_game)
            temp_game.execute_action(best_action)
            
            # if best_action.action == "play":
                # num_play += 1
        return temp_game.eval() / 25

    def backpropagate(self, score):
        node = self
        while node is not None:
            node.total_score += score      
            node.num_visits += 1
            node = node.parent


def stats(node: Hanabi_Node):
    def UCB1(node):
        # C = np.sqrt(2)
        C = 0.1
        exploitation = node.total_score / node.num_visits
        exploration = C * np.sqrt(np.log(node.parent.num_visits) / node.num_visits)
        return exploitation + exploration

    print(f'LEFT: {len(node.actions_to_try)}, VISITED: {len(node.children)}')
    for c in node.children:
        print(f'{c.parent_action.cmd_string()}-> UCB: {UCB1(c):.2f}, avg_score: {c.total_score/c.num_visits:.2f}, total: {c.total_score:.2f}, num_visits: {c.num_visits}')
        print(f'\tLEFT: {len(c.actions_to_try)}, VISITED: {len(c.children)}')
        for cc in c.children:
            print(f'\t{cc.parent_action.cmd_string()}\t\t-> UCB: {UCB1(cc):.2f}, avg_score: {cc.total_score/cc.num_visits:.2f}, total: {cc.total_score:.2f}, num_visits: {cc.num_visits}')