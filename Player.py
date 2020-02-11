from time import sleep
import time

from GameBoard import Board
from MinMax import bestNextMove


class HumanPlayer(object):
    '''
    Implementation of a human player.
    Uses mouse clicks to determine action.
    '''

    selectedPieceIndex = -1
    aborted = False
    isTurnFinished = True
    
    def __init__ (self, name, pieceType):
        # PieceType will be either black or white
        self.pieceType = pieceType
        self.name = name
        
    def usesMouse (self):
        return True
    
    def hasProgressSignal (self):
        return False
    
    def pieceItemWasClicked (self, pieceType, boardIndex):
        if self.isTurnFinished:
            return
        
        if self.board.gamePhase == Board.PieceSetPhase:
            return False
        
        elif pieceType == self.pieceType:
            if self.board.gamePhase == Board.PieceMovePhase:
                self.selectedPieceIndex = boardIndex
                return True  
            
        elif (self.board.gamePhase == Board.PieceMoveRemovePhase
              or self.board.gamePhase == Board.PieceSetRemovePhase):
            if self.board.executeOpCode((Board.OpRemove, self.pieceType, boardIndex)):
                self.isTurnFinished = True
                
            return False
    
    def boardPositionWasClicked (self, boardIndex):
        if self.isTurnFinished:
            return
        
        if self.board.gamePhase == Board.PieceSetPhase:
            if self.board.executeOpCode((Board.OpSet, self.pieceType, boardIndex)):
                self.isTurnFinished = True
                
        elif self.board.gamePhase == Board.PieceMovePhase:
            if self.selectedPieceIndex != -1:
                if self.board.executeOpCode((Board.OpMove, self.pieceType, self.selectedPieceIndex, boardIndex)):
                    self.isTurnFinished = True
    
    def doTurn(self):
        '''
        Returns False, if the turn was aborted, otherwise True
        '''
        
        self.isTurnFinished = False
        # Waits till either the turn finishes by the player inputing
        # a correct move with there mouse, or the turn is aborted
        while not self.isTurnFinished and not self.aborted:
            sleep(0.1)
            
        # Reset the aborted flag, to signal successful abort
        if self.aborted and not self.isTurnFinished:
            self.aborted = False
            return False
        self.aborted = False
        return True
    
    def abort (self):
        self.aborted = True
        
            
class AIPlayer (object):
    '''
    Implementation of an AI Player, using MinMax to choose
    the most advantageous move.
    '''
    
    aborted = False
    progressChangedReciever = None
    lookAheadDifficulty = [2, 4, 6]
    
    def __init__ (self, name, pieceType, difficulty):
        # PieceType will be either black or white
        self.pieceType = pieceType
        self.name = name
        self.lookAhead = self.lookAheadDifficulty[difficulty]
        
    def usesMouse (self):
        return False
    
    def hasProgressSignal (self):
        return True
    
    def doTurn (self):  
        '''
        Returns False, if the turn was aborted, otherwise True
        '''
        self.progressChangedReciever("0.00% Done")
        startTime = time.time()
        
        bestMove = bestNextMove(self.board, self.pieceType, self.lookAhead, self.moveCalcProgressChanged)
        
        if self.aborted:
            self.aborted = False
            return False
        
        # To make sure, that even if the calculation of the best move was very fast,
        # an AI turn will take at least 1 second. 
        toSleep = 1 - (time.time() - startTime)
        if toSleep > 0:
            sleep(toSleep)
        
        self.board.executeOpCode(bestMove)
        return True

    def abort (self):
        self.aborted = True
        
    def moveCalcProgressChanged (self, percentageComplete):
        if self.progressChangedReciever != None:
            self.progressChangedReciever(str(percentageComplete) + "% done")
        
        
