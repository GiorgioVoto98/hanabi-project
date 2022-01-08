import numpy as np 

'''constant definition'''
NUM_PLAYERS = 2
CARD_PER_PLAYER = 5
NUM_COLOR = 5
NUM_VALUES = 5
RISK_FACTOR = 5

CARD_VALUES = [3,2,2,2,1]

blue = 0
red = 1
green = 2
yellow = 3
white = 4

'''riga vuol dire numero'''
'''colonna vuol dire colore'''
def getColor(color):
    if color=='blue':
        return 0
    elif color=='red':
        return 1
    elif color=='green':
        return 2
    elif color=='yellow':
        return 3
    elif color=='white':
        return 4
   

def __selRow(matrix, row):
        temp = np.zeros((NUM_VALUES,NUM_COLOR))        
        temp[row,:] = np.ones((1,NUM_COLOR))
        return matrix * temp

def __selCol(matrix, col):
        temp = np.zeros((NUM_VALUES,NUM_COLOR))        
        temp[:,col] = np.ones((1,NUM_VALUES))
        return matrix * temp    

def __delRow(matrix, row):
        temp = np.ones((NUM_VALUES,NUM_COLOR))        
        temp[row,:] = np.zeros((1,NUM_COLOR))
        return matrix * temp

def __delCol(matrix, col):        
        temp = np.ones((NUM_VALUES,NUM_COLOR))        
        temp[:,col] = np.zeros((1,NUM_VALUES))
        return matrix * temp    

def signalColor(hand, color, position):
    for i in range(CARD_PER_PLAYER):
        if i in position:
            hand[i]=__selCol(hand[i],color)
        else:
            hand[i]=__delCol(hand[i],color)

def signalNumber(hand, number, position):
    for i in range(CARD_PER_PLAYER):
        if i in position:
            hand[i]=__selRow(hand[i],number)
        else:
            hand[i]=__delRow(hand[i],number)      

def getProbabilities(hand):
    probability = np.zeros((CARD_PER_PLAYER,NUM_VALUES,NUM_COLOR))    
    for i in range(CARD_PER_PLAYER):
        probability[i] = hand[i]/np.sum(hand[i])        
    return probability                 

def obtainTableMatrix(table): 
    nextUsefulCards = np.sum(table, axis=0, dtype=np.int)                
    playMatrix=np.zeros((NUM_VALUES,NUM_COLOR))        
    for i in range(NUM_COLOR):              
        playMatrix[nextUsefulCards[i]][i]=nextUsefulCards[i]+1                        
        
    discardMatrix = np.zeros(playMatrix.shape)    
    for i in range(NUM_COLOR):              
        for j in range(nextUsefulCards[i]):
            discardMatrix[j][i]=1    
    
    return playMatrix, discardMatrix



class NoobPlayer():

    __playerId = 0

    def setPlayerId(self,id):
       self.__playerId=id

    def updateHand(self):
        self.remainings = self.__remainMatrix()
        self.hand = self.hand * (self.remainings>0)

    def __play(self, prob): 
        if self.blue_tokens==0:
            return -20           
        risultato=  prob*3
        risultato-= (1-prob)*RISK_FACTOR+(self.red_tokens*RISK_FACTOR)
        return risultato

    def __discard(self, prob):        
        if self.blue_tokens==8:
            return -20
        risultato=  prob
        risultato-= (1-prob)
        return risultato

    def __checkHintForNum(self, nPlayer, num, playMatrix):        
        result = 0
        if self.blue_tokens == 0:
            return -20
        for card in range(CARD_PER_PLAYER):
            if self.players[nPlayer][card][0] == num:            
                colPlayer = self.players[nPlayer][card][1]                        
                result = result + self.players[nPlayer][card][2]*.2
                result = result + self.players[nPlayer][card][2]*(playMatrix[num][colPlayer]>0)*.5
        return result-0.3

    def __checkHintForCol(self, nPlayer, col, playMatrix):            
        result = 0
        for card in range(CARD_PER_PLAYER):        
            if self.players[nPlayer][card][1] == col:
                numPlayer = self.players[nPlayer][card][0]            
                result = result + self.players[nPlayer][card][3]*.2
                result = result + self.players[nPlayer][card][3]*(playMatrix[numPlayer][col]>0)*.5
        return result-0.3    

    def __resetHandCard(self, card):
        for i in range(CARD_PER_PLAYER-1):        
            if i>=card:
                self.hand[i]=self.hand[i+1]                
        self.hand[CARD_PER_PLAYER-1]=self.remainings                

    def __remainMatrix(self): 
        total = np.ones([NUM_VALUES,NUM_COLOR], dtype=np.int)
        total *= CARD_VALUES
        total = np.transpose(total)   
        playerSparse = np.zeros((NUM_PLAYERS,NUM_VALUES,NUM_COLOR), dtype=np.int)      
        for player in range(NUM_PLAYERS):        
            for card in range(CARD_PER_PLAYER):                            
                playerSparse[player, self.players[player, card, 0], self.players[player, card, 1]] = 1
        return np.array(total-self.table-self.discarded-np.sum(playerSparse, axis=0), dtype=np.int)   


    def __addDiscarded(self, num, col):        
        self.blue_tokens+=1
        self.discarded[num,col]+=1
        self.remainings = self.__remainMatrix()
        self.hand = self.hand * (self.remainings>0)

    def __changePlayerCard(self, p, oldCard, newCard):
        for i in range(CARD_PER_PLAYER-1):
            if i>=oldCard:
                self.players[p][i]=self.players[p][i+1]
        self.players[p][CARD_PER_PLAYER-1]=newCard        
        self.remainings = self.__remainMatrix()
        self.hand = self.hand * (self.remainings>0)

    def __insertInTable(self, num, col):
        self.table[num][col]=1
        self.remainings = self.__remainMatrix()
        self.hand = self.hand * (self.remainings>0)

    def __init__(self):
        self.table = np.zeros((NUM_VALUES,NUM_COLOR))        
        self.blue_tokens = 8
        self.red_tokens = 0
        self.discarded = np.zeros((NUM_VALUES,NUM_COLOR))
        self.players = np.zeros((NUM_PLAYERS,CARD_PER_PLAYER,4), dtype=np.int)
        self.remainings = self.__remainMatrix()
        self.hand = 5*[self.remainings]

    def execute_add(self, player, card, num, col, newNum, newCol):
        if (player==self.__playerId): #me
            self.__insertInTable(num,col)        
            self.__resetHandCard(card)
        else:
            self.__insertInTable(num,col)
            self.__changePlayerCard(player,card,[newNum, newCol, True, True])

    def execute_discard(self, player, card, num, col, newNum, newCol):
        if (player==self.__playerId): #me
            self.__addDiscarded(num,col)
            self.__resetHandCard(card)
        else:
            self.__addDiscarded(num,col)
            self.__changePlayerCard(player,card, [newNum, newCol, True, True])

    def execute_hint(self, player, type, value, position):
        self.blue_tokens=-1
        if (player==self.__playerId): #me
            if (type=='color'):
                signalColor(self.hand,value,position)
            else:
                signalNumber(self.hand,value,position)
        else:        
            for pos in position:
                if (type=='color'):                        
                    self.players[player][pos][1]=value
                    self.players[player][pos][3]=False
                else:                
                    self.players[player][pos][0]=value
                    self.players[player][pos][2]=False    
    
    def bestOption(self):
        playMatrix, discardMatrix = obtainTableMatrix(self.table)
        probability = getProbabilities(self.hand)

        best_result = -100
        best_card = -1
        gioco = np.sum(probability*playMatrix, axis=2) 
        for i in range(CARD_PER_PLAYER):
            mostProbValue = np.argmax(gioco[i])
            probabValue = gioco[i][mostProbValue]
            result = self.__play(probabValue)
            if best_result<result:
                best_card=i
                best_result=result
                print(f"<playing> Found new best result! {best_result} for card {best_card}")        

        gioco =  np.sum(probability*discardMatrix, axis=2) 
        for i in range(CARD_PER_PLAYER):
            mostProbValue = np.argmax(gioco[i])
            probabValue = gioco[i][mostProbValue]    
            result = self.__discard(probabValue)                
            if best_result<result:
                best_card=i
                best_result=result
                print(f"<discarding> Found new best result! {best_result} for card {best_card}")                
        
        for player in range(NUM_PLAYERS):
            if player!=0:
                for num in range(NUM_VALUES):
                    result = self.__checkHintForNum(player, num, playMatrix)
                    if best_result<result:                
                        best_result=result
                        print(f"<sending> Found new best result! {best_result} for player {player}, number {num}")                                
                for col in range(NUM_COLOR):
                    result = self.__checkHintForCol(player, col, playMatrix)
                    if best_result<result:                
                        best_result=result
                        print(f"<sending> Found new best result! {best_result} for player {player}, color {col}")