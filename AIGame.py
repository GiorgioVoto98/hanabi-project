# coding=utf-8
from builtins import int
from copy import deepcopy
import numpy as np
import utils as ut
from utils import get_card_cell
from MCTS import State, MCTS
from game import Card
from AIPlayer import AI_Player

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
        next_usefull_cards, _ = self.usefl_cards()
        if next_usefull_cards[val, col] != 1:
            self.discardedMatrix[val, col] += 1
            self.storm_tokens += 1
        else:
            self.tableMatrix[val, col] = 1

    def is_playable(self, card):
        val, col = get_card_cell(card)
        next_usefull_cards, _ = self.usefl_cards()
        if next_usefull_cards[val, col] != 1:
            return False
        else:
            return True

    def discard(self, card):
        val, col = get_card_cell(card)
        self.discardedMatrix[val, col] += 1
        self.note_tokens -= 1
    
    def hint(self, type, value, dest):
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

    def extract_card(self, hint_matrix = None, card_avoided = None, player_request = ""):
        remaining_cards = self.remaining_cards(player_request)
        if card_avoided is not None:
            remaining_cards = remaining_cards - card_avoided
        if hint_matrix is not None:
            remaining_cards = remaining_cards * hint_matrix
        if np.sum(remaining_cards)==0:
            return -1, -1
        id_v, id_c = np.nonzero(remaining_cards)
        v = np.random.choice(id_v)
        c = np.random.choice(id_c)
        return v, c

    def is_last_round(self):
        # remaining_cards = self.remaining_cards()
        # if np.count_nonzero(remaining_cards) == 0:
        #     return True
        # else:
        #     return False
        return None

    def usefl_cards(self):
        next_usefull = np.sum(self.tableMatrix, axis=0)
        next_usefull_cards = np.zeros((ut.NUM_VALUES, ut.NUM_COLORS), dtype=int)
        next_useless_cards = np.zeros((ut.NUM_VALUES, ut.NUM_COLORS), dtype=int)

        for i in range(ut.NUM_COLORS):
            if next_usefull[i] != 5:
                next_usefull_cards[next_usefull[i]][i] = 1

        for i in range(ut.NUM_COLORS):
            for j in range(next_usefull[i]):
                next_useless_cards[j][i] = 1

        return next_usefull_cards, next_useless_cards

    def eval(self):
        if self.storm_tokens >= 3:
            return 0
        else:
            return np.sum(self.tableMatrix)

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

    def eval_action(self, action, prob):
        current_points = np.sum(self.tableMatrix)

        def eval_state(ok):
            if action[0] == 'play':
                if ok:
                    return current_points+1
                else:
                    return current_points
            elif action[0] == 'discard':
                if self.note_tokens == 0:
                    return -1
                elif ok:
                    return current_points+0.3
                else:
                    return current_points-0.3
            elif action[0] == 'hint':
                if self.note_tokens == 8:
                    return -1
                elif ok:
                    return current_points+0.1
                else:
                    return current_points

        return prob*eval_state(True)+(1-prob)*eval_state(False)


class MCTS_Hanabi_Node(State):
    def __init__(self, parent_action, game, root_player):
        super().__init__(parent_action)
        self.game = deepcopy(game)
        self.root_player = root_player

    def available_actions(self):
        player = self.game.get_current_player()
        self.exit_node(player)
        actions = player.action(self.game)
        self.enter_node(player)
        av_actions = []
        for action in actions:
            av_actions.append(self.execute_action(action))
        return av_actions

    def eval(self):
        return self.game.eval()

    def execute_action(self,action):
        new_game = deepcopy(self.game)
        current_player = new_game.get_current_player()

        if action[1] == 'play':
            # questo più o meno. In realtà io non so che carta ho in mano. Come la gioco?
            card = current_player.hand[action[2]]
            new_game.play(card)
            current_player.throw_card(action[2])

            # questo più o meno. In realtà io non dovrei dare una carta se sono me stesso?
            v, c = new_game.extract_card()
            if v != -1:
                current_player.give_card(Card(-1, v + 1, ut.inv_colors[c]))
        elif action[1] == 'discard':
            # questo più o meno. In realtà io non so che carta ho in mano. Come la gioco?
            card = current_player.hand[action[2]]
            new_game.discard(card)
            current_player.throw_card(action[2])
            # questo più o meno. In realtà io non dovrei dare una carta se sono me stesso?
            v, c = new_game.extract_card()
            if v != -1:
                current_player.give_card(Card(-1, v + 1, ut.inv_colors[c]))
        elif action[1] == 'hint':
            new_game.hint(action[2], action[3], action[4])

        new_game.next_turn()
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
    return False



