import random
import sys

sys.path.append("..")  # so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *
import math
import heapq

from Game import *

MAX_DEPTH = 3
STABILITY_THRESHOLD = 10
ABSOLUTE_CUTOFF = MAX_DEPTH + 3
PRUNE = 0.65
FOOD_CONSTR_PENALTY = 2
TUNNEL_CONSTR_PENALTY = 4
##
# AIPlayer
# Description: The responsbility of this class is to interact with the game by
# deciding a valid move based on a given game state. This class has methods that
# will be implemented by students in Dr. Nuxoll's AI course.
#
# Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    # __init__
    # Description: Creates a new Player
    #
    # Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer, self).__init__(inputPlayerId, "Munchkin")
        self.isFirstTurn = None
        self.foodDist = None
        self.enemyFoodDist = None

        self.bestFoodConstr = None
        self.bestFood = None
        self.anthillCoords = None
        self.moveQueue = []

    ##
    # getPlacement
    #
    # Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    # Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    # Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        self.isFirstTurn = True
        numToPlace = 0
        # implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:  # stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    # Choose any x location
                    x = random.randint(0, 9)
                    # Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    # Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        # Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:  # stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    # Choose any x location
                    x = random.randint(0, 9)
                    # Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    # Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        # Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]

    ##
    # getMove
    # Description: Gets the next move from the Player.
    #
    # Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    # Return: The Move to be made
    ##
    def getMove(self, currentState):
        if self.isFirstTurn:
            self.firstTurn(currentState)
        if len(self.moveQueue) > 0:
            move = self.moveQueue.pop()
            if move.moveType == END:
                self.moveQueue = []
            return move
        self.moveQueue = []
        self.visited = set()
        child, _ = self.getMoveRecursive(MMNode(None, currentState, 0, 1, None), -5000, 5000)
        parent = child
        while parent.depth > 1:
            self.moveQueue.append(parent.move)
            parent = parent.parent
        if parent.move.moveType == END:
            self.moveQueue = []
        return parent.move

    ##
    # getMoveRecursive
    # Description: Uses minimax to find the best move
    # 
    # Parameters:
    #   node: The MMNode to search from
    #   alpha: The lower bound cost of a valid move
    #   beta: The upper bound cost of a valid move
    #
    # Return:
    #   A MMNode, float tuple. If there is a move between alpha and beta, this tuple is the node for the best move
    #   and its cost. Otherwise, any move that is out of bounds is returned.
    ##
    def getMoveRecursive(self, node, alpha, beta):
        canStop = True

        # Fix getNextMove so moves can be cached
        if node.move:
            if node.move.moveType == MOVE_ANT:
                ant = getAntAt(node.state, node.move.coordList[-1])
                if ant:
                    ant.hasMoved = True
                    currentInv = node.state.inventories[node.state.whoseTurn]
                    prevInv = node.parent.state.inventories[node.state.whoseTurn]
                    if currentInv.foodCount > prevInv.foodCount:
                        currentInv.foodCount -= 1
                        ant.carrying = True
            elif node.move.moveType == BUILD:
                ant = getAntAt(node.state, self.anthillCoords)
                if ant:
                    ant.hasMoved = True
                canStop = False
            elif node.move.moveType == END:
                canStop = False
        
        # Base case
        node.h = self.heuristicStepsToGoal(node.state)
        if node.h == 0:
            return (node, 0)
        if node.parent and abs(node.h - node.parent.h) >= STABILITY_THRESHOLD:
            canStop = False
        if node.depth >= MAX_DEPTH and (canStop or node.depth >= ABSOLUTE_CUTOFF):
            return (node, node.h)
        if node in self.visited:
            return (node, None)

        # Recursive case
        self.visited.add(node)
        turn = node.state.whoseTurn
        if turn == self.me:
            return self.getMinMove(node, alpha, beta)
        else:
            return self.getMaxMove(node, alpha, beta)

    ## Finds the move that maximizes the heuristic
    def getMaxMove(self, node, alpha, beta):
        nodes = self.expandNode(node)
        bestNode = None
        nodes.sort()
        nodes = list(reversed(nodes))
        n = len(nodes)
        cap = math.ceil(n*PRUNE)
        for best in nodes[:cap]:
            child, cost = self.getMoveRecursive(best, alpha, beta)
            if cost != None and cost > alpha:
                bestNode = child
                alpha = cost
                if alpha >= beta:
                    return (bestNode, alpha)
        return (bestNode, alpha)

    ## Finds the move that minimizes the heuristic
    def getMinMove(self, node, alpha, beta):
        nodes = self.expandNode(node)
        bestNode = None
        nodes.sort()
        n = len(nodes)
        cap = math.ceil(n*PRUNE)
        for best in nodes[:cap]:
            child, cost = self.getMoveRecursive(best, alpha, beta)
            if cost != None and cost < beta:
                bestNode = child
                beta = cost
                if alpha >= beta:
                    return (bestNode, beta)
        return (bestNode, beta)     

    ##
    # firstTurn
    # Description: inits variables
    #
    # Parameters:
    #   currentState - A clone of the current state (GameState)
    #
    def firstTurn(self, currentState):
        self.me = currentState.whoseTurn
        inventory = getCurrPlayerInventory(currentState)
        tunnel = inventory.getTunnels()[0]
        hill = inventory.getAnthill()
        self.anthillCoords = hill.coords
        foods = getConstrList(currentState, None, (FOOD,))

        minDist = 100000  # arbitrarily large

        for food in foods:
            tunnelDist = self.movesToReach(tunnel.coords, food.coords, WORKER)
            hillDist = self.movesToReach(hill.coords, food.coords, WORKER)
            if tunnelDist < minDist:
                minDist = tunnelDist
                self.bestFood = food
                self.bestFoodConstr = tunnel
            if hillDist < minDist:
                minDist = hillDist
                self.bestFood = food
                self.bestFoodConstr = hill

        self.foodDist = minDist
        self.isFirstTurn = False
        self.moveQueue = []

    ##
    # heuristicStepsToGoal
    # Description: Calculates the number of steps required to get to the goal
    # Most of this function's code is to prevent a stalemate
    # A tiny amount of it actually wins the game
    #
    # Parameters:
    #   currentState - A clone of the current state (GameState)
    #
    #
    def heuristicStepsToGoal(self, currentState):
        # Get common variables
        workers = getAntList(currentState, self.me, (WORKER,))
        inventory = currentState.inventories[self.me]
        otherInv = currentState.inventories[1-self.me]
        otherAnthillCoords = otherInv.getAnthill().coords
        foodLeft = FOOD_GOAL - inventory.foodCount + len(workers)

        # Check if a player has won
        winner = getWinner(currentState)
        if winner == 1:
            if currentState.whoseTurn == self.me:
                return 0
            else:
                return 1000 #infinity
        elif winner == 0:
            if currentState.whoseTurn == self.me:
                return 1000 # infinity
            else:
                return 0
        elif foodLeft == 1 and getAntAt(currentState, self.anthillCoords).carrying:
            return 0


        # Prevent a jam where we have no food or workers but keep killing Booger drones by having all units rush the anthill
        if inventory.foodCount == 0 and len(workers) == 0:
            return sum(map(lambda ant: self.movesToReach(ant.coords, otherAnthillCoords, ant.type),
                           inventory.ants))

        adjustment = 0  # Penalty added for being in a board state likely to lose.

        # Unit variables
        drones = getAntList(currentState, self.me, (DRONE,))
        enemyWorkers = getAntList(currentState, 1 - self.me, (WORKER,))
        enemyFighters = getAntList(currentState, 1 - self.me, (DRONE, SOLDIER, R_SOLDIER))
        scaryFighters = list(filter(lambda fighter: fighter.coords[1] < 5, enemyFighters))
        soldiers = getAntList(currentState, self.me, (SOLDIER,))

        # If the other player is winning, buy a drone
        if otherInv.foodCount >= inventory.foodCount and len(enemyWorkers) > 0 and len(drones) == 0:
            adjustment += 1
            foodLeft += UNIT_STATS[DRONE][COST]

        if len(scaryFighters) > 0:
            # Pay for defense
            adjustment += len(scaryFighters)
            if len(soldiers) == 0: 
                foodLeft += UNIT_STATS[SOLDIER][COST]

            # Retreat workers and queen
            if len(enemyWorkers) > 0:
                # Find squares under attack
                for enemy in enemyFighters:
                    for coord in listAttackable(enemy.coords,
                                                UNIT_STATS[enemy.type][MOVEMENT] + UNIT_STATS[enemy.type][RANGE]):
                        ant = getAntAt(currentState, coord)
                        # Gently encourage retreat
                        if ant != None and ant.player == self.me:
                            adjustment += 1 if ant.type == WORKER or ant.type == QUEEN else 0

                        # If anthill in danger, double soldier food allowance and make threatening enemy high priority
                        if coord == self.anthillCoords:
                            start = None
                            if len(soldiers) == 0:
                                start = self.anthillCoords
                                wantWorker = False
                                foodLeft += UNIT_STATS[SOLDIER][COST]
                            else:
                                start = soldiers[0].coords
                            adjustment += self.movesToReach(enemy.coords, start,
                                                            SOLDIER) * 10  # Arbitrary to make the priority

        # Encourage drones to kill workers and storm the anthill
        start = None
        if len(drones) > 0:
            start = drones[0].coords
        else:
            start = self.anthillCoords
        if len(enemyWorkers) > 0:
            adjustment += sum(map(lambda enemyWorker: \
                            self.movesToReach(start, enemyWorker.coords, DRONE), enemyWorkers))
        adjustment += self.movesToReach(start, otherInv.getAnthill().coords, DRONE)

        # Encourage soldiers to storm the anthill
        start = None
        if len(soldiers) > 0:
            start = soldiers[0].coords
        else:
            start = self.anthillCoords
        if len(scaryFighters) > 0:
            adjustment += sum(map(lambda target: \
                self.movesToReach(start, target.coords, SOLDIER), scaryFighters))
        adjustment += self.movesToReach(start, otherAnthillCoords, SOLDIER)

        # Penalize no workers
        if len(workers) == 0:
            foodLeft += UNIT_STATS[WORKER][COST]

        # Prevent queen from jamming workers
        queen = inventory.getQueen()
        adjustment += 120.0 / (approxDist(queen.coords, self.bestFoodConstr.coords) + 1) + 120.0 / (
                    approxDist(queen.coords, self.bestFood.coords) + 1)

        raw = self.rawCostToGoal(workers, foodLeft)
        if raw == 0:
            return 0.0
        return float(raw + adjustment)

    # Find actions needed to deliver food for economic victory
    def rawCostToGoal(self, workers, foodLeft):
        raw = 0
        workerCount = len(workers)
        costs = []  # Cost of each worker to deliver food
        for worker in workers:
            raw += self.getWorkerPenalty(worker.coords)
            costs.append(self.getWorkerCost(worker.coords, worker.carrying))

        # First, calculate worker moves + end turns for all workers to deliver food
        if foodLeft < workerCount:
            sortedWorkers = sorted(costs)
            raw = sum(sortedWorkers[:foodLeft])
        elif workerCount > 0:
            raw = sum(costs)
        else:
            raw = self.getWorkerCost(self.bestFoodConstr.coords, False)

        # Now, calculate cost to complete all the necessary full trips to gather all food
        foodRuns = foodLeft - workerCount
        if foodRuns > 0:
            actions = self.getWorkerCost(self.bestFoodConstr.coords, False, True) * foodRuns
            raw +=  2 * actions

        raw = max(raw, foodLeft)
        return raw

    ## Finds the number of move actions it will take to reach a given destination
    def movesToReach(self, source, dest, unitType):
        taxicabDist = abs(dest[0] - source[0]) + abs(dest[1] - source[1])
        cost = float(taxicabDist)
        return cost

    ##
    # getAttack
    # Description: Gets the attack to be made from the Player
    #
    # Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
   #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        # Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]

    ##
    # registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        # method templaste, not implemented
        pass

    ## Gets penalties for workers staying on a construct
    def getWorkerPenalty(self, workerCoords):
        if workerCoords == self.bestFoodConstr.coords: 
            return TUNNEL_CONSTR_PENALTY
        elif workerCoords == self.bestFood.coords:
            return FOOD_CONSTR_PENALTY
        return 0

    ##
    # getWorkerCost
    # Params:
    #   currentState: game state
    #
    # Returns:
    #   the number of moves it will take for the worker to deliver a food plus penalties
    def getWorkerCost(self, workerCoords, carrying, isFakeAnt=False):
        cost = 0
        if carrying:
            cost = self.movesToReach(workerCoords, self.bestFoodConstr.coords,
                                     WORKER) + TUNNEL_CONSTR_PENALTY 
        else:
            cost = self.movesToReach(workerCoords, self.bestFood.coords,
                     WORKER) + self.foodDist + FOOD_CONSTR_PENALTY + TUNNEL_CONSTR_PENALTY
        return cost


    ##
    # expandNode
    #
    # Expands the given node by generating its subnodes
    def expandNode(self, node):
        moves = listAllLegalMoves(node.state)
        gameStates = map(lambda move: (getNextStateAdversarial(node.state, move), move), moves)

        nodes = list(map(lambda stateMove: MMNode(stateMove[1], stateMove[0], node.depth+1, \
                                                      self.heuristicStepsToGoal(stateMove[0]), node), gameStates))
        return nodes

## Data structure for mini-max tree
class MMNode:
    def __init__(self, move, state, depth, heuristic, parent):
        self.move = move
        self.state = state
        self.depth = depth
        self.parent = parent
        self.h = heuristic
        self.ant = getAntAt(state, move.coordList[0]) if move != None and move.coordList else None

    # Operator overloads
    def __le__(self, other):
        return self.h <= other.h
    def __lt__(self, other):
        return self.h < other.h
    def __ge__(self, other):
        return self.h >= other.h
    def __gt__(self, other):
        return self.h > other.h
    def __eq__(self, other):
        return self.h == other.h and ((self.depth == other.depth and self.parent is other.parent and compareAnts(self.ant, other.ant)) or compareStates(self.state, other.state))
    def __hash__(self):
        return int(self.h) * 100 + self.depth * 10 + self.state.whoseTurn

## Checks if two states are identical
def compareStates(currentState, newState):
        if currentState.whoseTurn != newState.whoseTurn:
            return False

        callAnts = getAntList(currentState)
        nallAnts = getAntList(newState)
        if(len(callAnts) != len(nallAnts)):
            return False

        for cant,nant in zip(callAnts,nallAnts):
            if not compareAnts(cant,nant):
                return False
        return True

## Checks if two ants are identical
def compareAnts(lhs, rhs):
        if lhs == None or rhs == None:
            return lhs == rhs
        return lhs.coords == rhs.coords and lhs.type == rhs.type and lhs.carrying == rhs.carrying and \
               lhs.player == rhs.player