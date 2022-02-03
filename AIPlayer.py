from copy import deepcopy
import numpy as np
import math

import utils as ut
from utils import get_card_cell
from action import Action
from game import Card


class AI_Player:
    def __init__(self, name, max_hand_size):
        self.name = name
        self.max_hand_size = max_hand_size        
        self.hand = []
        self.hintMatrix = []

    def give_card(self, card):
        assert len(self.hand) <= self.max_hand_size
        self.hand.append(card)

        assert len(self.hintMatrix) <= self.max_hand_size
        self.hintMatrix.append(np.ones((ut.NUM_COLORS, ut.NUM_VALUES)))

    def throw_card(self, position):
        if len(self.hand) > 0:
            self.hand.pop(position)
        
        assert len(self.hintMatrix) > 0
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
        # mental representation of your hand
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

    def get_hand_matrix(self):
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
            if math.isclose(np.sum(mat), 0):
                hand_probability.append(self.hintMatrix[i])
            else:
                hand_probability.append(mat / np.sum(mat))

        return hand_probability

    def __play_vector(self, game):
        useful_probs = []
        usefull_cards = game.usefl_cards()
        hand_probability = self.__get_hand_probs(game)
        for i in range(len(hand_probability)):
            mat = hand_probability[i] * usefull_cards
            useful_probs.append(np.sum(mat))

        return useful_probs

    def redeterminize(self, game):
        self.real_hand = self.hand
        self.hand = []
        card_avoided = np.zeros((ut.NUM_VALUES, ut.NUM_COLORS))
        for i in range(len(self.hintMatrix)):
            v, c = game.extract_card(self.hintMatrix[i], card_avoided)
            if v == -1:
                return False
            card_avoided[v, c] += 1
            card = Card(-1, v + 1, color=ut.inv_colors[c])
            self.hand.append(card)
        return True

    def best_actions(self, old_game):
        best_actions = []
        best_scores = []

        def update_best_actions(action: Action, score):
            if len(best_actions) == 0 or score != 0:
                if len(best_actions) < ut.MAX_ACTIONS:
                    best_scores.append(score)
                    best_actions.append(action)
                elif len(best_actions) == ut.MAX_ACTIONS:
                    idx_worst = np.argmin(best_scores)
                    if score > best_scores[idx_worst]:          
                        best_scores[idx_worst] = score
                        best_actions[idx_worst] = action

        useful_prob = self.__play_vector(old_game)

        # PLAY       
        for i in range(len(useful_prob)):
            res = useful_prob[i]
            action = Action("play", value=i)
            if res >= 0.6 and old_game.storm_tokens == 0:
                update_best_actions(action, res)
            elif res >= 0.7 and old_game.storm_tokens == 1:
                update_best_actions(action, res)
            elif res >= 0.9:
                update_best_actions(action, res)
        
        # DISCARD
        # GETTING HAND PROBABILITY
        hand_prob = self.__get_hand_probs(old_game)
        # GETTING POINTS OF THE CURRENT GAME
        old_card_value = old_game.get_points()                
        if old_game.note_tokens > 0:
            for i in range(len(useful_prob)):
                action = Action('discard', value=i)
                if useful_prob[i] < 0.6 and old_game.storm_tokens == 0:
                    # GETTING POINTS OF THE GAME, WHEN DISCARDING THAT CARD)
                    new_card_value = old_game.get_points(hand_prob[i])
                    res = 1 - np.sum(old_card_value - new_card_value) / np.sum(old_card_value)
                    update_best_actions(action, res)
                elif useful_prob[i] < 0.7 and old_game.storm_tokens == 1:
                    # GETTING POINTS OF THE GAME, WHEN DISCARDING THAT CARD)
                    new_card_value = old_game.get_points(hand_prob[i])
                    res = 1 - np.sum(old_card_value - new_card_value) / np.sum(old_card_value)
                    update_best_actions(action, res)
                elif useful_prob[i] < 0.9:
                    # GETTING POINTS OF THE GAME, WHEN DISCARDING THAT CARD)
                    new_card_value = old_game.get_points(hand_prob[i])
                    res = 1 - np.sum(old_card_value - new_card_value) / np.sum(old_card_value)
                    update_best_actions(action, res)

        # HINT
        if old_game.note_tokens < 8:
            for player in old_game.players:
                if player.name == self.name:
                    continue
                # GETTING THE PROBABILITY OF PLAYING A CARD IN THE CURRENT STATE FOR THAT PLAYER
                useful_prob = player.__play_vector(old_game)
                if len(useful_prob) != 0:
                    confidence = np.max(useful_prob)
                    hinted_values = []
                    hinted_colors = []

                    for card in player.hand:
                        if card.value not in hinted_values:
                            hinted_values.append(card.value)
                            new_player = deepcopy(player)
                            positions = new_player.get_hint_positions('value', card.value)
                            new_player.hint('value', card.value, positions)
                            # GETTING THE PROBABILITY OF PLAYING A CARD IN THE CURRENT STATE FOR THAT PLAYER AFTER HINT VALUE
                            new_useful_prob = new_player.__play_vector(old_game)
                            new_confidence = np.max(new_useful_prob)
                            action = Action('hint', type='value', value=card.value, dest=player.name)
                            res = new_confidence - confidence
                            update_best_actions(action, res)
                        if card.color not in hinted_colors:
                            hinted_colors.append(card.color)
                            new_player = deepcopy(player)
                            positions = new_player.get_hint_positions('color', card.color)
                            new_player.hint('color', card.color, positions)
                            # GETTING THE PROBABILITY OF PLAYING A CARD IN THE CURRENT STATE FOR THAT PLAYER AFTER HINT VALUE
                            new_useful_prob = new_player.__play_vector(old_game)
                            new_confidence = np.max(new_useful_prob)
                            action = Action('hint', type='color', value=card.color, dest=player.name)
                            res = new_confidence - confidence
                            update_best_actions(action, res)
        
        # Sort best_action based on score
        best_actions = [action for _, action in sorted(zip(best_scores, best_actions),
                                                       key=lambda tup: tup[0], reverse=True)]
        
        return best_actions

    def action(self, game):
        return self.best_actions(game)[0]
        