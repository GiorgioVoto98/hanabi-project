from copy import deepcopy
import numpy as np

import utils as ut
from utils import get_card_cell
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
            # useless_probs.append(np.sum(mat))
            useless_probs.append(np.sum(mat))
        return useful_probs, useless_probs

    def redeterminize(self, game):
        self.real_hand = self.hand
        self.hand = []
        card_avoided = np.zeros((ut.NUM_VALUES, ut.NUM_COLORS))
        for i in range(len(self.hintMatrix)):
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
        flag_action = False
        for i in range(len(useful_prob)):
            if (useful_prob[i]>=0.6) and (old_game.storm_tokens == 0):
                res = useful_prob[i] #old_game.eval_action(action, useful_prob[i])
                update_best_actions([res, 'play', i], res)
                flag_action = True
            elif (useful_prob[i]>=0.7) and (old_game.storm_tokens == 1):
                res = useful_prob[i] #old_game.eval_action(action, useful_prob[i])
                update_best_actions([res, 'play', i], res)
                flag_action = True
            elif (useful_prob[i]>=0.9) :
                res = useful_prob[i] #old_game.eval_action(action, useful_prob[i])
                update_best_actions([res, 'play', i], res)
                flag_action = True

        if not flag_action:
            if old_game.note_tokens > 0:
                for i in range(len(useless_prob)):
                    res = useless_prob[i] #old_game.eval_action(action, useless_prob[i])
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