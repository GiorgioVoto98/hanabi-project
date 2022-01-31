import numpy as np

colors = {'red': 0, 'blue': 1, 'yellow': 2, 'green': 3, 'white': 4}
inv_colors = {0: 'red', 1: 'blue', 2: 'yellow', 3: 'green', 4: 'white'}
NUM_COLORS = 5
NUM_VALUES = 5
TOT_CARDS = 50


def selRow(row):
    matrix = np.zeros((NUM_VALUES, NUM_COLORS))
    matrix[row, :] = np.ones((1, NUM_COLORS))
    return matrix


def selCol(col):
    matrix = np.zeros((NUM_VALUES, NUM_COLORS))
    matrix[:, col] = np.ones((1, NUM_VALUES))
    return matrix


def delRow(row):
    matrix = np.ones((NUM_VALUES, NUM_COLORS))
    matrix[row, :] = np.zeros((1, NUM_COLORS))
    return matrix


def delCol(col):
    matrix = np.ones((NUM_VALUES, NUM_COLORS))
    matrix[:, col] = np.zeros((1, NUM_VALUES))
    return matrix


def max_hand_size(num_players: int):
    if num_players in [2, 3]:
        return 5
    elif num_players in [4, 5]:
        return 4
    else:
        raise NameError("Incorrect number of players: must be between 2 and 5)")


def get_card_cell(card):
    return card.value-1, colors[card.color]


def get_startMatrix():
    CARD_VALUES = np.array([3, 2, 2, 2, 1], dtype=np.int32).reshape((NUM_VALUES, 1))
    startMatrix = np.ones((NUM_VALUES, NUM_COLORS), dtype=np.int32)
    startMatrix *= CARD_VALUES
    return startMatrix

def get_pointMatrix():
    CARD_VALUES = np.array([5, 4, 3, 2, 1], dtype=np.int32).reshape((NUM_VALUES, 1))
    point_matrix = np.ones((NUM_VALUES, NUM_COLORS), dtype=np.int32)
    point_matrix *= CARD_VALUES
    return point_matrix


def get_tableMatrix(table):
    tableMatrix = np.zeros((NUM_VALUES, NUM_COLORS), dtype=np.int32)
    for color in table:
        for card in table[color]:
            val, col = get_card_cell(card)
            tableMatrix[val, col] = 1

    return tableMatrix


def get_discardedMatrix(discarded):
    discardedMatrix = np.zeros((NUM_VALUES, NUM_COLORS), dtype=np.int32)
    for card in discarded:
        val, col = get_card_cell(card)
        discardedMatrix[val, col] += 1
    
    return discardedMatrix