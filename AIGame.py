from builtins import int
import numpy as np
import utils as ut
import os

from utils import get_card_cell
from MCTS import MCTSHanabiNode, MCTS
from game import Card
from AIPlayer import AI_Player
from action import Action


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

    def remaining_cards(self, player_request=""):
        remaining = self.startMatrix - self.tableMatrix - self.discardedMatrix
        for player in self.players:
            if (player.name != self.current_player) and (player.name != player_request):
                remaining = remaining - player.get_hand_matrix()
        return remaining

    def get_points(self, probs=None):
        # @probs: MATRIX WITH PROBABILITIES OF LOSING A CARD
        if probs is None:
            probs = np.zeros((ut.NUM_VALUES, ut.NUM_COLORS))
        point_matrix = np.ones((ut.NUM_VALUES, ut.NUM_COLORS))
        # REMAINING CARDS IN GAME: WE MULTIPLY PER 0.8 TO LOWER THE CONFIDENCE OF DISCARDING ("POTENTIAL VALUE")
        remaining_cards = 0.8 * (self.startMatrix - self.discardedMatrix - probs) / self.startMatrix
        for col in range(ut.NUM_COLORS):
            fact_col = 1.0
            for val in range(ut.NUM_VALUES):
                if self.tableMatrix[val][col] == 1:
                    # POINTS MADE FOR SURE
                    fact_col = 1.0
                    point_matrix[val][col] = 1.0
                else:
                    point_matrix[val][col] = fact_col * remaining_cards[val][col]
                    if remaining_cards[val][col] > 1:
                        # IT'S NOT SO TERRIBLE IF IT'S NOT THE LAST REMAINING CARDS...
                        fact_col = point_matrix[val][col] * 2.3
                    else:
                        fact_col = point_matrix[val][col]
                    if fact_col > 1:
                        fact_col = 1
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
        return v, c

    def usefl_cards(self):
        next_usefull = np.sum(self.tableMatrix, axis=0)
        next_usefull_cards = np.zeros((ut.NUM_VALUES, ut.NUM_COLORS), dtype=int)

        for i in range(ut.NUM_COLORS):
            if next_usefull[i] != 5:
                next_usefull_cards[next_usefull[i]][i] = 1

        return next_usefull_cards

    def get_player(self, player_name) -> AI_Player:
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

    def eval(self):
        _, score = self.is_game_over()
        return score

    def execute_action(self, action: Action):
        current_player = self.get_current_player()

        if action.action == 'play':
            card = current_player.hand[action.value]
            self.play(card)
            current_player.throw_card(action.value)

            if not self.is_last_round():
                v, c = self.extract_card()
                if v != -1:
                    current_player.give_card(Card(-1, v + 1, ut.inv_colors[c]))
                    
        elif action.action == 'discard':
            card = current_player.hand[action.value]
            self.discard(card)
            current_player.throw_card(action.value)

            if not self.is_last_round():
                v, c = self.extract_card()
                if v != -1:
                    current_player.give_card(Card(-1, v + 1, ut.inv_colors[c]))

        elif action.action == 'hint':
            self.hint(action.type, action.value, action.dest)
        
        self.next_turn()


def MCTS_algo(game, root_player, time_limit):
    root = MCTSHanabiNode(None, game, root_player)
    mcts = MCTS(root, time_limit)
    return mcts.best_action()
