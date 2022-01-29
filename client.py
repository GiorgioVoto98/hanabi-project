#!/usr/bin/env python3

from sys import argv, stdout
from threading import Thread
from time import sleep
import os
import socket

import GameData
from constants import *
from game import Player
from AIGame import AI_Game, AI_Player, MCTS_algo
from action import Action
import utils as ut

AUTOMATIC = True

if len(argv) < 4:
    print("You need the player name to start the game.")
    # exit(-1)
    playerName = "Test"  # For debug
    ip = HOST
    port = PORT
else:
    playerName = argv[3]
    ip = argv[1]
    port = int(argv[2])

run = True
statuses = ["Lobby", "Game"]
status = statuses[0]

ai_game = None
ai_players: list[AI_Player] = []
current_player: str = ""


def get_player(name: str) -> AI_Player:
    for pl in ai_players:
        if pl.name == name:
            return pl


def init_ai_players(players_names: list[str]):
    max_hand_size = ut.max_hand_size(len(players_names))
    for player_name in players_names:
        ai_players.append(AI_Player(player_name, max_hand_size))


def update_ai_players(players: list[Player], handSize: int):
    for pl in players:
        ai_player = get_player(pl.name)
        if ai_player.name == playerName:
            ai_player.update_hintMatrix(handSize)
        else:
            for i, card in enumerate(pl.hand):
                if i >= len(ai_player.hand):
                    ai_player.give_card(card)


def next_turn():
    # Ask the server to show the data
    s.send(GameData.ClientGetGameStateRequest(playerName).serialize())


def manageInput():
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

                #actions = get_player(playerName).action(ai_game)
                actions = MCTS_algo(ai_game,playerName)
                print(actions)

                if not AUTOMATIC:
                    input()

                # TO BE DELETED
                def convertToAction(actionBad):
                    if actionBad[1] == "play" or actionBad[1] == "discard":
                        return Action(actionBad[1], value=actionBad[2])
                    elif actionBad[1] == "hint":
                        return Action(actionBad[1], type=actionBad[2], value=actionBad[3], dest=actionBad[4])

                action = convertToAction(actions)

                ok = action.send(playerName, s)
                if ok:
                    print("[" + playerName + " - " + status + "]: ", end="")
                else:
                    print("Action not valid")
                    os._exit(-1)
                
            sleep(0.1)  


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

    # Start HUMAN input agent
    # Thread(target=manageInput).start()

    # Start AI agent
    Thread(target=agentAI).start()
    
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

            # Init empty AI players
            init_ai_players(data.players)

            s.send(GameData.ClientPlayerReadyData(playerName).serialize())
            status = statuses[1]

            # Update state
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
                print(pos + ": [ ")
                for c in data.tableCards[pos]:
                    print(c.toClientString() + " ")
                print("]")
            print("Discard pile: ")
            for c in data.discardPile:
                print("\t" + c.toClientString())
            print("Note tokens used: " + str(data.usedNoteTokens) + "/8")
            print("Storm tokens used: " + str(data.usedStormTokens) + "/3")
            
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

        if type(data) is GameData.ServerActionValid:  # DISCARD
            dataOk = True
            print("Action valid!")
            print("Current player: " + data.player)

            player = get_player(data.lastPlayer)
            player.throw_card(data.cardHandIndex)
            
            # Update state
            next_turn()

        if type(data) is GameData.ServerPlayerMoveOk:
            dataOk = True
            print("Nice move!")
            print("Current player: " + data.player)

            player = get_player(data.lastPlayer)
            player.throw_card(data.cardHandIndex)
            
            # Update state
            next_turn()

        if type(data) is GameData.ServerPlayerThunderStrike:
            dataOk = True
            print("OH NO! The Gods are unhappy with you!")

            player = get_player(data.lastPlayer)
            player.throw_card(data.cardHandIndex)
            
            # Update state
            next_turn()

        if type(data) is GameData.ServerHintData:
            dataOk = True
            print("Hint type: " + data.type)
            print("Player " + data.destination + " cards with value " + str(data.value) + " are:")      
            for i in data.positions:
                print("\t" + str(i))

            # Hint                
            player = get_player(data.destination)
            player.hint(data.type, data.value, data.positions)
            
            # Update state
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

            run = False
            break
            # print("Ready for a new game!")

        if not dataOk:
            print("Unknown or unimplemented data type: " + str(type(data)))
            
        print("[" + playerName + " - " + status + "]: ", end="")
        stdout.flush()

    print("CLIENT EXIT")
