import numpy as np

colors = {'red': 0, 'blue': 1, 'yellow': 2, 'green': 3, 'white': 4}
NUM_COLORS = 5
NUM_VALUES = 5
RISK_FACTOR = 3

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
