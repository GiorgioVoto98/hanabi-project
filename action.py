class Action:
    def __init__(self, action, value, type=None, dest=None):
        self.action = action
        self.type = type
        self.value = value
        self.dest = dest

    def toCommandString(self):
        if self.action == 'play' or self.action == 'discard':
            return f'{self.action} {self.value}'
        elif self.action == 'hint':
            return f'{self.action} {self.type} {self.dest} {self.value}'
        else:
            raise NameError("Action name not correct")



