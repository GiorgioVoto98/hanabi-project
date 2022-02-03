from builtins import int
from copy import deepcopy
import numpy as np
import utils as ut
from utils import get_card_cell
from MCTS import State, MCTS
from MCTS2 import MCTS2
from game import Card
from AIPlayer import AI_Player
from action import Action
import os

class AI_Game:
    def __init__(self, storm_tokens, note_tokens, table, discarded, players, current_player):
        self.current_player = current_player
        self.storm_tokens = storm_tokens
        self.note_tokens = note_tokens
        self.players = players
        self.startMatrix = ut.get_startMatrix()
        self.tableMatrix = ut.get_tableMatrix(table)
        self.discardedMatrix = ut.get_discardedMatrix(discarded)
        self.max_hand_size = ut.max_hand_size(len(players))
        self.last_round = self.is_last_round()

    def play(self, card):
        val, col = get_card_cell(card)
        next_usefull_cards = self.usefl_cards()
        if next_usefull_cards[val, col] != 1:
            self.discardedMatrix[val, col] += 1
            self.storm_tokens += 1
        else:
            self.tableMatrix[val, col] = 1
            if val == 5 and self.note_tokens > 0:
                self.note_tokens -= 1

    def is_playable(self, card):
        val, col = get_card_cell(card)
        next_usefull_cards = self.usefl_cards()
        if next_usefull_cards[val, col] != 1:
            return False
        else:
            return True

    def discard(self, card):
        assert self.note_tokens > 0
        val, col = get_card_cell(card)
        self.discardedMatrix[val, col] += 1
        self.note_tokens -= 1
    
    def hint(self, type, value, dest):
        assert self.note_tokens < 8
        dest_player = self.get_player(dest)
        positions = dest_player.get_hint_positions(type, value)
        dest_player.hint(type, value, positions)
        self.note_tokens += 1

    def remaining_cards(self, player_request = ""):
        remaining = self.startMatrix - self.tableMatrix - self.discardedMatrix
        for player in self.players:
            if (player.name != self.current_player) and (player.name != player_request):
                remaining = remaining - player.get_hand_martix()
        return remaining

    def get_points(self, probs = None):
        if probs is None:
            probs = np.zeros((ut.NUM_VALUES,ut.NUM_COLORS))
        point_matrix = ut.get_pointMatrix()
        remaining_cards = 0.8 * (self.startMatrix - self.discardedMatrix - probs) / self.startMatrix
        for col in range(ut.NUM_COLORS):
            fatt_col = 1.0
            for val in range(ut.NUM_VALUES):
                if self.tableMatrix[val][col] == 1:
                    fatt_col = 1.0
                    point_matrix[val][col] = 1.0
                else:
                    point_matrix[val][col] = fatt_col * remaining_cards[val][col]
                    if remaining_cards[val][col] > 1 :
                        fatt_col = point_matrix[val][col] * 2.3
                    else:
                        fatt_col = point_matrix[val][col]
                    if fatt_col > 1:
                        fatt_col = 1
        point_matrix[point_matrix > 1] = 1
        point_matrix[point_matrix < 0] = 0
        return point_matrix

    def extract_card(self, hint_matrix=None, card_avoided=None, player_request=""):
        remaining_cards = self.remaining_cards(player_request)
        if card_avoided is not None:
            remaining_cards = remaining_cards - card_avoided
        if hint_matrix is not None:
            remaining_cards = remaining_cards * hint_matrix
        remaining_cards = remaining_cards * (remaining_cards > 0)
        if np.sum(remaining_cards) == 0:
            return -1, -1
        p = remaining_cards
        p = p / np.sum(p)
        p = p.flatten()
        val = np.random.choice(np.arange(0, 25), size=1, replace=False, p=p)
        v = int(val / 5)
        c = int(val % 5)
        # id_v, id_c = np.nonzero(remaining_cards)
        # v = np.random.choice(id_v)
        # c = np.random.choice(id_c)
        return v, c

    '''
    def usefl_cards(self):
        next_usefull = np.sum(self.tableMatrix, axis=0)
        next_usefull_cards = np.zeros((ut.NUM_VALUES, ut.NUM_COLORS), dtype=int)
        next_useless_cards = np.zeros((ut.NUM_VALUES, ut.NUM_COLORS), dtype=int)

        for i in range(ut.NUM_COLORS):
            if next_usefull[i] != 5:
                next_usefull_cards[next_usefull[i]][i] = 1

        for i in range(ut.NUM_COLORS):
            for j in range(next_usefull[i]):
                next_useless_cards[j][i] = 0

        return next_usefull_cards, next_useless_cards
    '''
    def usefl_cards(self):
        next_usefull = np.sum(self.tableMatrix, axis=0)
        next_usefull_cards = np.zeros((ut.NUM_VALUES, ut.NUM_COLORS), dtype=int)
        # next_useless_cards = - np.ones((ut.NUM_VALUES, ut.NUM_COLORS), dtype=int)

        for i in range(ut.NUM_COLORS):
            if next_usefull[i] != 5:
                next_usefull_cards[next_usefull[i]][i] = 1

        return next_usefull_cards

    def eval(self):
        _, score = self.is_game_over()
        return score

    def get_player(self, player_name):
        for player in self.players:
            if player.name == player_name:
                return player

    def next_turn(self):
        for i, player in enumerate(self.players):
            if player.name == self.current_player:
                cur_id = i
        next_id = (cur_id+1) % len(self.players)
        self.current_player = self.players[next_id].name

    def get_current_player(self):
        return self.get_player(self.current_player)


    def is_last_round(self):
        remaining = np.sum(self.startMatrix - self.tableMatrix - self.discardedMatrix)
        for p in self.players:
            remaining -= len(p.hintMatrix)
        if remaining == 0:
            return True
        else:
            return False

    def is_game_over(self):
        if self.storm_tokens == 3:
            return True, 0

        next_useless_cards = np.sum(self.get_points())
        score = (np.sum(self.tableMatrix) * 2 + next_useless_cards / 5) / 50

        if np.sum(self.tableMatrix) == 25:
            return True, score

        num_cards_players = 0
        for p in self.players:
            num_cards_players += len(p.hintMatrix)

        if self.is_last_round() and num_cards_players <= ((self.max_hand_size-1) * len(self.players)):
            return True, score
        else:
            return False, score

    def execute_action(self, action: Action):
        current_player = self.get_current_player()

        if action.action == 'play' or action.action == 'discard':
            if action.value >= len(current_player.hand):
                    print(action.value)
                    print(current_player.hand)
                    os._exit(10)

        if action.action == 'play':
            card = current_player.hand[action.value]
            self.play(card)
            current_player.throw_card(action.value)

            if not self.is_last_round():
                v, c = self.extract_card()
                if v != -1:
                    current_player.give_card(Card(-1, v + 1, ut.inv_colors[c]))
                else:
                    os._exit(3)
                    
        elif action.action == 'discard':
            card = current_player.hand[action.value]
            self.discard(card)
            current_player.throw_card(action.value)

            if not self.is_last_round():
                v, c = self.extract_card()
                if v != -1:
                    current_player.give_card(Card(-1, v + 1, ut.inv_colors[c]))
                else:
                    os._exit(9)

        elif action.action == 'hint':
            self.hint(action.type, action.value, action.dest)
        
        self.next_turn()


class MCTS_Hanabi_Node(State):
    def __init__(self, parent_action, game, root_player):
        super().__init__(parent_action)
        self.game = deepcopy(game)
        self.root_player = root_player

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

    '''
    def eval(self):
        new_game = deepcopy(self.game)
        score = 0

        for i in range(2) :
        #while True
            stop, score = new_game.is_game_over()
            if stop:
                return score
            best_action = new_game.get_current_player().action(new_game)
            new_game.execute_action(best_action)
        score = new_game.eval()
        return score
    '''


    def execute_action(self,action):
        new_game = deepcopy(self.game)
        new_game.execute_action(action)
        return MCTS_Hanabi_Node(action,new_game,self.root_player)

    def enter_node(self, player):
        if self.root_player != player.name:
            player.hand = player.real_hand

    def exit_node(self, player):
        if self.root_player != player.name:
            player.redeterminize(self.game)

def MCTS_algo(game, root_player):
    if root_player == game.current_player:
        mcts = MCTS(MCTS_Hanabi_Node(None,game,root_player))
        return mcts.best_action()
        #return MCTS2(game)
    return False



