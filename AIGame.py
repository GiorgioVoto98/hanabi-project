# coding=utf-8
from builtins import int
from copy import deepcopy
import numpy as np
import utils as ut
from utils import get_card_cell
from MCTS import State, MCTS
from game import Card

class AI_Player:
    def __init__(self, name, max_hand_size):
        self.name = name
        self.hand = []
        self.max_hand_size = max_hand_size
        self.hintMatrix = max_hand_size * [np.ones((ut.NUM_COLORS, ut.NUM_VALUES))]

    def give_card(self, card):
        self.hand.append(card)
        if len(self.hintMatrix) != self.max_hand_size:
            self.hintMatrix.append(np.ones((ut.NUM_COLORS, ut.NUM_VALUES)))

    def throw_card(self, position):
        if len(self.hand) != 0:
            self.hand.pop(position)
        self.hintMatrix.pop(position)

    def update_hintMatrix(self, handSize):
        while len(self.hintMatrix) != handSize:
            self.hintMatrix.append(np.ones((ut.NUM_COLORS, ut.NUM_VALUES)))

    def get_hint_positions(self, type, value):
        positions = []
        pos = 0
        if type == 'value':
            for card in self.hand:
                if card.value == value:
                    positions.append(pos)
                pos += 1
        elif type == 'color':
            for card in self.hand:
                if card.color == value:
                    positions.append(pos)
                pos += 1
        return positions

    def hint(self, type, value, positions):
        # mental representation of your hand.
        if type == 'value':
            for pos in range(len(self.hintMatrix)):
                if pos in positions:
                    self.hintMatrix[pos] = self.hintMatrix[pos] * ut.selRow(value-1)
                else:
                    self.hintMatrix[pos] = self.hintMatrix[pos] * ut.delRow(value-1)
        elif type == 'color':
            value = ut.colors[value]
            for pos in range(len(self.hintMatrix)):
                if pos in positions:
                    self.hintMatrix[pos] = self.hintMatrix[pos] * ut.selCol(value)
                else:
                    self.hintMatrix[pos] = self.hintMatrix[pos] * ut.delCol(value)

    def get_hand_martix(self):
        # get the Handd Matrix of the others player
        handMatrix = np.zeros((ut.NUM_VALUES, ut.NUM_COLORS))
        for card in self.hand:
            val, col = get_card_cell(card)
            handMatrix[val][col] += 1
        return handMatrix

    def __get_hand_probs(self, game):
        hand_probability = []
        remaining_cards = game.remaining_cards(self.name)

        for i in range(len(self.hintMatrix)):
            mat = remaining_cards * self.hintMatrix[i]
            hand_probability.append(mat / np.sum(mat))
        return hand_probability

    def __play_or_discard_vector(self, game):
        useful_probs = []
        useless_probs = []
        usefull_cards, useless_cards = game.usefl_cards()
        hand_probability = self.__get_hand_probs(game)
        for i in range(len(hand_probability)):
            mat = hand_probability[i] * usefull_cards
            useful_probs.append(np.sum(mat))

        for i in range(len(hand_probability)):
            mat = hand_probability[i] * useless_cards
            useless_probs.append(np.sum(mat))
        return useful_probs, useless_probs

    def redeterminize(self, game):
        self.real_hand = self.hand
        self.hand = []
        card_avoided = np.zeros((ut.NUM_VALUES, ut.NUM_COLORS))
        for i in range(self.max_hand_size):
            v, c = game.extract_card(self.hintMatrix[i], card_avoided)
            if v == -1:
                return False
            card_avoided[v,c] += 1
            card = Card(-1, v + 1, color=ut.inv_colors[c])
            self.hand.append(card)
        return True

    def action(self, old_game):
        best_actions = []
        best_scores = []

        def update_best_actions(action, score):
            MAX_ACTIONS = 5
            if len(best_actions) < MAX_ACTIONS:
                best_scores.append(score)
                best_actions.append(action)
            elif len(best_actions) == MAX_ACTIONS:
                worst_score = min(best_scores)
                if score > worst_score:
                    for i in range(MAX_ACTIONS):
                        if best_scores[i] == worst_score:
                            best_actions.pop(i)
                            best_scores.pop(i)
                            best_actions.append(action)
                            best_scores.append(score)
                            break

        useful_prob, useless_prob = self.__play_or_discard_vector(old_game)
        for i in range(len(useful_prob)):
            if (useful_prob[i]>=0.6) and (old_game.storm_tokens < 2):
                action = ['play', i]
                res = useful_prob[i] #old_game.eval_action(action, useful_prob[i])
                update_best_actions([res, 'play', i], res)
            elif (useful_prob[i]>=0.9) :
                action = ['play', i]
                res = useful_prob[i] #old_game.eval_action(action, useful_prob[i])
                update_best_actions([res, 'play', i], res)

        if old_game.note_tokens > 0:
            for i in range(len(useless_prob)):
                action = ['discard', i]
                res = useless_prob[i]/3 #old_game.eval_action(action, useless_prob[i])
                update_best_actions([res, 'discard', i], res)

        if old_game.note_tokens < 8:
            for player in old_game.players:
                if player.name == self.name:
                    continue
                useful_prob, _ = player.__play_or_discard_vector(old_game)
                confidence = np.max(useful_prob)
                hinted_values = []
                hinted_colors = []

                for card in player.hand:
                    # if old_game.is_playable(card):
                        if card.value not in hinted_values:
                            hinted_values.append(card.value)
                            new_player = deepcopy(player)
                            positions = new_player.get_hint_positions('value', card.value)
                            new_player.hint('value', card.value, positions)
                            new_useful_prob, _ = new_player.__play_or_discard_vector(old_game)
                            new_confidence = np.max(new_useful_prob)
                            action = ['hint', 'value', card.value, player.name]
                            res = new_confidence - confidence # old_game.eval_action(action, new_confidence - confidence)
                            update_best_actions([res, 'hint', 'value', card.value, player.name], res)
                        if card.color not in hinted_colors:
                            hinted_colors.append(card.color)
                            new_player = deepcopy(player)
                            positions = new_player.get_hint_positions('color', card.color)
                            new_player.hint('color', card.color, positions)
                            new_useful_prob, _ = new_player.__play_or_discard_vector(old_game)
                            new_confidence = np.max(new_useful_prob)
                            action = ['hint', 'color', card.color, player.name]
                            res = new_confidence - confidence # old_game.eval_action(action, new_confidence - confidence)
                            update_best_actions([res, 'hint', 'color', card.color, player.name], res)
        # Sort best_action based on score
        best_actions = [action for _, action in sorted(zip(best_scores, best_actions), reverse=True)]
        return best_actions


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
        self.last_turn = self.is_last_turn()

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

    def is_last_turn(self):
        remaining_cards = self.remaining_cards()
        if np.count_nonzero(remaining_cards) == 0:
            return True
        else:
            return False

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
            new_game.next_turn()
        elif action[1] == 'discard':
            # questo più o meno. In realtà io non so che carta ho in mano. Come la gioco?
            card = current_player.hand[action[2]]
            new_game.discard(card)
            current_player.throw_card(action[2])
            # questo più o meno. In realtà io non dovrei dare una carta se sono me stesso?
            v, c = new_game.extract_card()
            if v != -1:
                current_player.give_card(Card(-1, v + 1, ut.inv_colors[c]))
            new_game.next_turn()
        elif action[1] == 'hint':
            pos = new_game.get_player(action[4]).get_hint_positions(action[2],action[3])
            new_game.get_player(action[4]).hint(action[2],action[3], pos)
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



