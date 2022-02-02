#!/usr/bin/env python3

from sys import argv, stdout
from threading import Thread
from time import sleep
import os
import socket
import argparse
import numpy as np

import GameData
from constants import *
from game import Player
from AIGame import AI_Game, MCTS_algo
from AIPlayer import AI_Player
import utils as ut

AUTOMATIC = True
MCTS = True
NUM_GAMES = 5

parser = argparse.ArgumentParser(prog='client.py')
parser.add_argument('--ip', type=str, default=HOST, help='IP address of the host')
parser.add_argument('--port', type=int, default=PORT, help='Port of the server')
parser.add_argument('--name', type=str, help='Name of the player', required=True)
parser.add_argument('--time', type=float, default=1.0, help='Maximum time per action')
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--ai', action='store_true', help='AI player')
mode.add_argument('--human', action='store_true', help='Human player')

args = parser.parse_args()

ip = args.ip
port = args.port
playerName = args.name
time_limit = args.time
if args.ai:
    AI = True
else:
    AI = False

run = True
statuses = ["Lobby", "Game"]
status = statuses[0]

ai_game = None
ai_players = []
current_player = ""


def get_player(name) -> AI_Player:
    for pl in ai_players:
        if pl.name == name:
            return pl


def init_ai_players(players_names):
    max_hand_size = ut.max_hand_size(len(players_names))
    for player_name in players_names:
        ai_players.append(AI_Player(player_name, max_hand_size))


def update_ai_players(players, handSize):
    for pl in players:
        ai_player = get_player(pl.name)
        if ai_player.name == playerName:
            ai_player.update_hintMatrix(handSize)
        else:
            for i, card in enumerate(pl.hand):
                if i >= len(ai_player.hand):
                    ai_player.give_card(card)


def reset_ai_players():
    for ai_player in ai_players:
        ai_player.hand = []
        ai_player.hintMatrix = []


def next_turn():
    # Ask the server to show the data
    s.send(GameData.ClientGetGameStateRequest(playerName).serialize())


def agentHuman():
    global run
    global status

    while run:
        command = input()
        # Choose data to send
        if command == "exit":
            run = False
            os._exit(0)
        elif command == "ready" and status == statuses[0]:
            s.send(GameData.ClientPlayerStartRequest(playerName).serialize())
        elif command == "show" and status == statuses[1]:
            s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
        elif command.split(" ")[0] == "discard" and status == statuses[1]:
            try:
                cardStr = command.split(" ")
                cardOrder = int(cardStr[1])
                s.send(GameData.ClientPlayerDiscardCardRequest(playerName, cardOrder).serialize())
            except:
                print("Maybe you wanted to type 'discard <num>'?")
                continue
        elif command.split(" ")[0] == "play" and status == statuses[1]:
            try:
                cardStr = command.split(" ")
                cardOrder = int(cardStr[1])
                s.send(GameData.ClientPlayerPlayCardRequest(playerName, cardOrder).serialize())
            except:
                print("Maybe you wanted to type 'play <num>'?")
                continue
        elif command.split(" ")[0] == "hint" and status == statuses[1]:
            try:
                destination = command.split(" ")[2]
                t = command.split(" ")[1].lower()
                if t != "colour" and t != "color" and t != "value":
                    print("Error: type can be 'color' or 'value'")
                    continue
                value = command.split(" ")[3].lower()
                if t == "value":
                    value = int(value)
                    if int(value) > 5 or int(value) < 1:
                        print("Error: card values can range from 1 to 5")
                        continue
                else:
                    if value not in ["green", "red", "blue", "yellow", "white"]:
                        print("Error: card color can only be green, red, blue, yellow or white")
                        continue
                s.send(GameData.ClientHintData(playerName, destination, t, value).serialize())
            except:
                print("Maybe you wanted to type 'hint <type> <destinatary> <value>'?")
                continue
        elif command == "":
            print("[" + playerName + " - " + status + "]: ", end="")
        else:
            print("Unknown command: " + command)
            continue
        stdout.flush()


def agentAI():
    global run
    global status
    global ai_game
    global ai_players
    global current_player

    if status == statuses[0]:
        # Send ready message immediately
        s.send(GameData.ClientPlayerStartRequest(playerName).serialize())

    while run:
        if status == statuses[1]:
            if current_player == playerName:
                current_player == ""

                if not MCTS:
                    action = get_player(playerName).action(ai_game)        
                else:
                    action = MCTS_algo(ai_game, playerName)

                if not AUTOMATIC:
                    input()

                ok = action.send(playerName, s)
                if ok:
                    print("[" + playerName + " - " + status + "]: ", end="")
                else:
                    print("Action not valid")
                    os._exit(-1)
                
            sleep(0.01)
        sleep(0.01)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Connect to the server
    s.connect((HOST, PORT))
    request = GameData.ClientPlayerAddData(playerName)
    s.send(request.serialize())

    data = s.recv(DATASIZE)
    data = GameData.GameData.deserialize(data)
    if type(data) is GameData.ServerPlayerConnectionOk:
        print("Connection accepted by the server. Welcome " + playerName)
    print("[" + playerName + " - " + status + "]: ", end="")

    if AI:
        Thread(target=agentAI).start()
    else:
        Thread(target=agentHuman).start()

    game_num = 0
    scores = np.empty(NUM_GAMES, dtype=np.int32)

    while run:
        dataOk = False
        data = s.recv(DATASIZE)
        if not data:
            continue
        data = GameData.GameData.deserialize(data)

        if type(data) is GameData.ServerPlayerStartRequestAccepted:
            dataOk = True
            print("Ready: " + str(data.acceptedStartRequests) + "/" + str(data.connectedPlayers) + " players")
            data = s.recv(DATASIZE)
            data = GameData.GameData.deserialize(data)

        if type(data) is GameData.ServerStartGameData:
            dataOk = True
            print("Game start!")

            if AI:
                # Init empty AI players
                init_ai_players(data.players)

            s.send(GameData.ClientPlayerReadyData(playerName).serialize())
            status = statuses[1]

            if AI:
                next_turn()

        if type(data) is GameData.ServerGameStateData:
            dataOk = True

            print("Current player: " + data.currentPlayer)
            print("Player hands: ")
            for p in data.players:
                print(p.toClientString())
            print("Cards in your hand: " + str(data.handSize))
            print("Table cards: ")
            for pos in data.tableCards:
                print(f'\t{pos}\t->', end="\t")
                for c in data.tableCards[pos]:
                    print(c.value, end="  ")
                print()
            print("Discard pile: ")
            for c in data.discardPile:
                print("\t" + c.toClientString())
            print("Note tokens used: " + str(data.usedNoteTokens) + "/8")
            print("Storm tokens used: " + str(data.usedStormTokens) + "/3")
            
            if AI:
                # Update state of the game
                update_ai_players(data.players, data.handSize)
                ai_game = AI_Game(data.usedStormTokens,
                                data.usedNoteTokens,
                                data.tableCards,
                                data.discardPile,
                                ai_players,
                                data.currentPlayer)
                current_player = data.currentPlayer

        if type(data) is GameData.ServerActionInvalid:
            dataOk = True
            print("Invalid action performed. Reason:")
            print(data.message)

        if type(data) is GameData.ServerActionValid: # discard
            dataOk = True
            print("Action valid!")
            print("Current player: " + data.player)

            if AI:
                player = get_player(data.lastPlayer)
                player.throw_card(data.cardHandIndex)
                next_turn()

        if type(data) is GameData.ServerPlayerMoveOk:
            dataOk = True
            print("Nice move!")
            print("Current player: " + data.player)

            if AI:
                player = get_player(data.lastPlayer)
                player.throw_card(data.cardHandIndex)
                next_turn()

        if type(data) is GameData.ServerPlayerThunderStrike:
            dataOk = True
            print("OH NO! The Gods are unhappy with you!")

            if AI:
                player = get_player(data.lastPlayer)
                player.throw_card(data.cardHandIndex)
                next_turn()

        if type(data) is GameData.ServerHintData:
            dataOk = True
            print("Hint type: " + data.type)
            print("Player " + data.destination + " cards with value " + str(data.value) + " are:")      
            for i in data.positions:
                print("\t" + str(i))

            if AI:                
                player = get_player(data.destination)
                player.hint(data.type, data.value, data.positions)
                next_turn()

        if type(data) is GameData.ServerInvalidDataReceived:
            dataOk = True
            print(data.data)

        if type(data) is GameData.ServerGameOver:
            dataOk = True
            print(data.message)
            print(data.score)
            print(data.scoreMessage)
            stdout.flush()

            scores[game_num] = data.score
            game_num += 1

            if game_num == NUM_GAMES:
                run = False
                break
            
            print("Ready for a new game!")
            if AI:
                current_player = ""
                game_ai = None
                reset_ai_players()
                next_turn()

        if not dataOk:
            print("Unknown or unimplemented data type: " + str(type(data)))
            
        print("[" + playerName + " - " + status + "]: ", end="")
        stdout.flush()

    print("Scores:", scores)
    print("Average score:", np.average(scores))
    print("CLIENT EXIT")
