import os
import socket
import GameData


class Action:
    def __init__(self, action, type=None, value=None, dest=None):
        self.action = action
        self.type = type
        self.value = value
        self.dest = dest

    def cmd_string(self):
        if self.action == 'play' or self.action == 'discard':
            return f'{self.action} {self.value}'
        elif self.action == 'hint':
            return f'{self.action} {self.type} {self.dest} {self.value}'
        else:
            raise NameError("Action name not correct")

    def send(self, playerName, s: socket) -> bool:
        command = self.cmd_string()
        print(f"PLAYED: {command}")

        # Choose data to send
        if self.action == "exit":
            os._exit(0)
        elif self.action == "discard":
            if type(self.value) is not int:
                print("Maybe you wanted to type 'discard <num>'?")
                return False
            s.send(GameData.ClientPlayerDiscardCardRequest(playerName, self.value).serialize())
        elif self.action == "play":
            if type(self.value) is not int:
                print("Maybe you wanted to type 'play <num>'?")
                return False
            s.send(GameData.ClientPlayerPlayCardRequest(playerName, self.value).serialize())
        elif self.action == "hint":
            if self.type != "colour" and self.type != "color" and self.type != "value":
                print("Error: type can be 'color' or 'value'")
                return False
            if self.type == "value":
                if self.value > 5 or self.value < 1:
                    print("Error: card values can range from 1 to 5")
                    return False
            elif self.type == "color" or self.type == "colour":
                if self.value not in ["green", "red", "blue", "yellow", "white"]:
                    print("Error: card color can only be green, red, blue, yellow or white")
                    return False
            else:
                print("Maybe you wanted to type 'hint <type> <destinatary> <value>'?")

            s.send(GameData.ClientHintData(playerName, self.dest, self.type, self.value).serialize())
        else:
            print("Unknown command: " + command)
            return False

        return True
