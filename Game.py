from time import sleep
import time

from PyQt5.Qt import QThread, pyqtSignal

from GameBoard import Board, invertPieceType


class Game(QThread):
    '''
    Runs in it's own thread, independent from the UI Thread.
    High level manager for the GameBoard. Decides which players,
    turn it is.
    '''

    playerFinishedTurn = pyqtSignal()
    gameEnded = pyqtSignal()
    
    # Flag to abort this thread as soon as possible
    aborted = False
    
    def __init__ (self, player1, player2):
        QThread.__init__(self)
        
        self.board = Board()
        self.player1 = player1
        self.player2 = player2
        player1.board = self.board
        player2.board = self.board
        self.turnCounter = 0
        
    def __del__ (self):
        self.wait()
        
    def start(self, delayedStart=False):
        self.aborted = False
        self.delayedStart = delayedStart
        QThread.start(self)
        
    def run(self):
        # Delayed start happens after one undo, so if the next player is an AI
        # it doesn't start calculating it's moves right away. So if the player
        # hits undo multiple times, there is less delay, cause we don't have
        # to wait for the AI to abort every time 
        if self.delayedStart:
            counter = 100
            while not self.aborted and counter > 0:
                counter -= 1
                sleep(0.01)
        
        if self.aborted:
            return
        
        while not self.aborted and (self.board.gamePhase == Board.PieceMovePhase or
               self.board.gamePhase == Board.PieceSetPhase or
               self.board.gamePhase == Board.PieceSetRemovePhase or
               self.board.gamePhase == Board.PieceMoveRemovePhase):
            self.nextTurn()
            
        if not self.aborted:
            self.gameEnded.emit()
    
    def nextTurn (self):
        player = self.getCurrentPlayer()
        if player.doTurn():
            self.playerFinishedTurn.emit()
            
            if (self.board.gamePhase == Board.PieceSetRemovePhase
                or self.board.gamePhase == Board.PieceMoveRemovePhase):
                player.doTurn()
                self.playerFinishedTurn.emit()
             
            self.board.checkBoardState(invertPieceType(player.pieceType))
            self.turnCounter += 1
        
    def undo (self):
        if self.turnCounter == 0:
            return
        
        self.turnCounter -= 1
        self.board.undo()
        
    def abort (self):
        if not self.isRunning():
            return
        
        self.aborted = True
        self.getCurrentPlayer().abort()
        
    def doesCurrentPlayerUseMouse (self):
        return self.getCurrentPlayer().usesMouse()
        
    def getCurrentPlayer (self):
        if self.turnCounter % 2 == 0:
            return self.player1
        else:
            return self.player2
        
        
        
    
