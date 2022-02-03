# Hanabi AI

Exam of Computational Intelligence 2021/2022. It requires teaching the client to play the 
game of Hanabi ([rules here](https://www.spillehulen.dk/media/102616/hanabi-card-game-rules.pdf)).

## GROUP 
*s287899* Francesco Torta

*s288179* Giorgio Voto

## Server

The server accepts passing objects provided in GameData.py back and forth to the clients.
Each object has a ```serialize()``` and a ```deserialize(data: str)``` method that must be 
used to pass the data between server and client.

Server closes when no client is connected.

To start the server:

```bash
python server.py <minNumPlayers>
```

Arguments:

+ minNumPlayers: __Optional__, default = 2


Commands for server:

+ exit: exit from the server

## Client

To start the client:

```bash
python client.py [-h] [--ip IP] [--port PORT] --name NAME [--time TIME] (--ai | --human)
```

Arguments:
+ ip: IP address of the server (default: 127.0.0.1 (localhost))
+ port: server TCP port (default: 1024)
+ name: name of the player (REQUIRED)
+ time: maximum time per move in seconds (default: 1.0)
+ ai: play in AI mode (REQUIRED if not --human)
+ human: play manually (REQUIRED if not --ai)

If playing in manual mode, commands for client:
+ exit: exit from the game
+ ready: set your status to ready (lobby only)
+ show: show cards
+ hint \<type> \<destinatary>:
  + type: 'color' or 'value'
  + destinatary: name of the person you want to ask the hint to
+ discard \<num>: discard the card *num* (\[0-4]) from your hand

## Strategy for the client in AI mode

### RIS-MCTS 
The strategy is inspired from the paper: 
[Re-determinizing Information Set Monte Carlo-Tree Search in Hanabi](https://arxiv.org/abs/1902.06075). 

Vanilla Information Set Monte Carlo Tree Search (IS-MCTS) performs 
very poorly in Hanabi. This happens due to hidden informations in Hanabi: 
for example if the current player is A, and B has a playable Red Two (R2) 
in their hand, then regardless of what player A chooses to do, when we reach
player B in the search tree a positive reward will always be received for playing
that card, despite the fact that player B cannot possibly know this.
This renders any hints that player A gives meaningless, as they
have no impact either on the available actions or the action
consequences for the player receiving the hint. 

They address this problem with a new variant called Re-determinizing IS-MCTS
(RIS-MCTS). This is done by re-determinizing hidden information from the perspective
of the *acting player* at each node in the tree search (to be distinguished from the 
*active player* in the game, who is always the root player in the tree). The re-determinize 
function shuffles the player’s hand and deck in line with their current information set.

We tried RIS-MCTS algorithm with some variations:

- To limit the branching factor, we used a **custom heuristic** (explained [below](#Custom-Heuristic)) 
which produces a set of possible good actions.
We found that on average a **branching factor of 7** actions was the best performing. 

- The selection uses the classic UCB (Upper Confidence Bounds) with **C = 0.1** 

- We also didn't simulate an entire game on a terminal node, because a simulation with 
the custom heuristic policy at every move takes lot of time (as a consequence, given 
a time limit the MCTS algorithm performs less global iterations). 
We tried also a very fast random policy, but that was not accurate enough to be useful.
To address this problem, we directly produce a **potential score** (from 0 to 50) that evaluate how 
potentially good the current state will be at the end of the game. 
The score is then normalized between 0 and 1.

- We did different benchmark from fixed number of MCTS iterations (400) to a time-based MCTS 
(1 and 2 seconds maximum per move). As expected the average score increases as the time increases. 
Results [here](#Performance).


### Custom Heuristic

#### 1. Play

The agent computes the probability of its hand by taking the remaining cards and the hint given from the other players on its cards.
Based on these probabilities, he can choose to play if 
- The game has 3 storm tokens left and the probability of be a good card is greater or equal than 0.6
- The game has 2 storm tokens left and the probability of be a good card is greater or equal than 0.7
- The game has 1 storm tokens left and the probability of be a good card is greater or equal than 0.9
   
#### 2. Discard

If the card is not played, then the agent check if can be discardable.
First of all, the agent checks the potential value of the state `old_value`, which is the potential final result by considering the current state of the table and the discarded pile.

The player that discards the card and then it evaluates again the potential value of the state `new_value`.
The probability of discarding a card is the computed as `(old_value - new_value) / old_value`
If discarding a card does not change the potential final result (e.g. discarding a card already on the table or a card of a color that cannot be reached), it has a very high probability to be discarded.

#### 3. Hint

For each card of each player in the game the agent evaluates the probability for the player to play a card (`confidence`).
This is made by using the hints given to that player during the game and using the table information, the discarded pile and 
all the other visible player cards except himself (and obviously the current_player).

Having the probability that is seen by that player, the agent gives a value hint and the evaluates the new probability of playing for that player `new_confidence`.

The probability of giving a hint is obtained with the formula: `new_confidence - confidence`.
The same procedure is applied to the color hint. 

#### 4. Best Actions

All the possible actions are sorted by decreasing probability. 
Depending on the branching factor `BF` we want to use, we select only the top `BF` actions. 



## Performance:

Algorithm | Time | 2 players | 3 players | 4 players | 5 players
--- | --- | --- | --- | --- |--- 
Custom RIS-MCTS | 400 iterations | 16.55 | 17.4 | 17.8 | 17.25
Custom RIS-MCTS | 1 second | 16.86 | 17.46 | 18.06 | 17.53 |
Custom RIS-MCTS | 2 seconds | 17.14 | 18.2 | 17.93 | 18.33 |

