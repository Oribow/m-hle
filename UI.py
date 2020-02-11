import os
import sys
import webbrowser

from PyQt5 import uic
from PyQt5.Qt import pyqtSignal
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Game import Game
from GameBoard import Board, convIndexToRingNotation
import MinMax
from Player import HumanPlayer, AIPlayer


# path pointing to project folder in which Main.py is located
path = os.path.dirname(os.path.abspath(__file__))

def relPathToAbs (relPath):
    '''
    Converts a path relative to the project folder into an absolute one
    '''
    return os.path.join(path, relPath)

class QMainMuehleUI (QMainWindow):
    
    # diameter of inner most ring
    smallestRingDim = 100
    
    # will be added to 
    ringScaleVal = 100 
    
    pieceDiameter = 30
    
    focusIndicatorDiameter = 33
    
    # where white pieces not placed on the board will go
    pieceStackOriginWhite = QPointF((smallestRingDim + ringScaleVal * 2) / 2 + 130, (smallestRingDim + ringScaleVal * 2) / 2)
    
    # where black pieces not placed on the board will go
    pieceStackOriginBlack = QPointF(-(smallestRingDim + ringScaleVal * 2) / 2 - 100, (smallestRingDim + ringScaleVal * 2) / 2)
    
    # where white pieces not placed on the board will go
    pieceStackOriginNeverWhite = QPointF((smallestRingDim + ringScaleVal * 2) / 2 + 100, (smallestRingDim + ringScaleVal * 2) / 2)
    
    # where black pieces not placed on the board will go
    pieceStackOriginNeverBlack = QPointF(-(smallestRingDim + ringScaleVal * 2) / 2 - 130, (smallestRingDim + ringScaleVal * 2) / 2)
    
    # currently highlighted Piece
    focusedPiece = None 
    
    def __init__ (self):
        self.app = QApplication(sys.argv)
        QMainWindow.__init__(self)
        uic.loadUi(relPathToAbs("ui/mainwindow.ui"), self)
        
        boardView = self.findChild(QWidget, "boardWidget")
        self.scene = QGraphicsScene(boardView)
        boardView.setScene(self.scene)
        
        # shows current turn count and current player
        self.turnCounterLabel = self.findChild(QLabel, 'turnCounter')
        
        # shows some helpful advise on what the player can do
        self.instructionLabel = self.findChild(QLabel, 'instruction')
        
        # shows simple black or white circle to indicate current players color
        self.pieceTypeIndicator = self.findChild(QLabel, 'pieceTypeIndicator')
        
        self.findChild(QPushButton, 'new_game').clicked.connect(self.showNewGameDialog)
        self.findChild(QPushButton, 'undo_button').clicked.connect(self.undo)
        self.findChild(QPushButton, 'help').clicked.connect(self.showHelp)
        
        self.pieceItemsWhite = []
        self.pieceItemsBlack = []
        
        # populate board with all items necessary for visualization
        self.initBoardLines()
        self.initBoardPosClickHandler()
        self.initBoardItems()
        
        # start a new game
        self.game = None
        self.startNewGame(Game(HumanPlayer("Riko", Board.White), AIPlayer("Regu", Board.Black, 1)))
        
    def start(self):
        self.show()
        self.app.exec_()
        
    def startNewGame (self, game):
        # abort old game, if still running
        if self.game != None and self.game.isRunning():
            self.game.abort()
            self.game.wait()
            
        # event handling, so the AI can display its turn calculation completion
        # mainly to let a human player now, the AI didn't crash
        if game.player1.hasProgressSignal():
            game.player1.progressChangedReciever = self.overrideInstructionLabel
        if game.player2.hasProgressSignal():
            game.player2.progressChangedReciever = self.overrideInstructionLabel
            
        self.game = game
        self.game.playerFinishedTurn.connect(self.playerFinishedTurn)
        self.game.gameEnded.connect(self.showVictoryWindow)
        
        # Starts the games own thread
        self.game.start()
        
        # to update the UI representation of the new game
        self.playerFinishedTurn()
        
    def updatePiecePositions (self):
        '''
        Will move the black and white pieces around,
        to fit the new board state
        '''
        offset = self.pieceDiameter / 2       
        index = -1
        
        # Counts how many pieces of that kind are currently on the board
        usedCounterWhite = 0
        usedCounterBlack = 0
        
        # Handle pieces set on the board
        for val in self.game.board.values:
            index += 1
            
            # If there is now piece at that location, skip it
            if val == Board.Empty:
                continue
            
            x, y = self.pieceIndexToScreenCoors(index)    
            x -= offset
            y -= offset
            if val == Board.White:
                self.pieceItemsWhite[usedCounterWhite].setPos(x, y)
                self.pieceItemsWhite[usedCounterWhite].boardIndex = index
                usedCounterWhite += 1
            else:
                self.pieceItemsBlack[usedCounterBlack].setPos(x, y)
                self.pieceItemsBlack[usedCounterBlack].boardIndex = index
                usedCounterBlack += 1
            
        # Handle pieces not set on the board
        for i in range(self.game.board.unplacedWhitePieces):
            index = i + usedCounterWhite
            self.pieceItemsWhite[index].setPos(self.pieceStackOriginWhite.x() - offset,
                                self.pieceStackOriginWhite.y() - i * (self.pieceDiameter + 3) - offset)
            self.pieceItemsWhite[index].boardIndex = -1
             
        for i in range(self.game.board.unplacedBlackPieces):
            index = i + usedCounterBlack
            self.pieceItemsBlack[index].setPos(self.pieceStackOriginBlack.x() - offset,
                                self.pieceStackOriginBlack.y() - i * (self.pieceDiameter + 3) - offset)
            self.pieceItemsBlack[index].boardIndex = -1
        
        for i in range(self.game.board.neverPlacedWhitePieces):
            index = i + usedCounterWhite + self.game.board.unplacedWhitePieces
            
            self.pieceItemsWhite[index].setPos(self.pieceStackOriginNeverWhite.x() - offset,
                                self.pieceStackOriginNeverWhite.y() - i * (self.pieceDiameter + 3) - offset)
            self.pieceItemsWhite[index].boardIndex = -1
             
        for i in range(self.game.board.neverPlacedBlackPieces):
            index = i + usedCounterBlack + self.game.board.unplacedBlackPieces
            self.pieceItemsBlack[index].setPos(self.pieceStackOriginNeverBlack.x() - offset,
                                self.pieceStackOriginNeverBlack.y() - i * (self.pieceDiameter + 3) - offset)
            self.pieceItemsBlack[index].boardIndex = -1
             
    def updateFocusIndicator (self):
        if self.focusedPiece == None:
            self.focusIndicator.setVisible(False)
        else:
            point = self.focusedPiece.pos()
            offset = self.focusIndicatorDiameter / 2 - self.pieceDiameter / 2
            point.setX(point.x() - offset)
            point.setY(point.y() - offset)
            self.focusIndicator.setPos(point)
            self.focusIndicator.setVisible(True)
            
    def pieceIndexToScreenCoors (self, index):
        '''
        Converts from a piece index, (see GameBoard.py) to screen coordinates
        '''
        iRing, iNode = convIndexToRingNotation(index)
        ringDiameterHalfed = (self.smallestRingDim + (2 - iRing) * self.ringScaleVal) / 2
        
        if iNode > 0 and iNode < 4:
            x = ringDiameterHalfed
        elif iNode > 4:
            x = -ringDiameterHalfed
        else:
            x = 0
        if iNode > 6 or iNode < 2:
            y = -ringDiameterHalfed
        elif iNode > 2 and iNode < 6:
            y = ringDiameterHalfed
        else:
            y = 0
        return x, y
    
    def initBoardItems (self):
        '''
        Adds 9 black and 9 white piece to the scene.
        Also adds the focus indicator to the scene.
        '''
        
        # black
        blackPieceImg = QPixmap()
        blackPieceImg.load("assets/muehle_piece_black.png")
        blackPieceImg = blackPieceImg.scaledToWidth(self.pieceDiameter)
        for i in range(9):  # Black pieces
            piece = PieceGraphicsItem(blackPieceImg, Board.Black, self.pieceItemClicked)
            self.pieceItemsBlack.append(piece)
            self.scene.addItem(piece)
        
        # white
        whitePieceImg = QPixmap()
        whitePieceImg.load("assets/muehle_piece_white.png")
        whitePieceImg = whitePieceImg.scaledToWidth(self.pieceDiameter)
        for i in range(9):  # White pieces
            piece = PieceGraphicsItem(whitePieceImg, Board.White, self.pieceItemClicked)
            self.pieceItemsWhite.append(piece)
            self.scene.addItem(piece)
            
        # focus-indicator
        self.focusIndicator = QGraphicsEllipseItem()
        self.focusIndicator.setRect(QRectF(0, 0, self.focusIndicatorDiameter, self.focusIndicatorDiameter))
        self.focusIndicator.setBrush(QBrush(Qt.blue))
        self.focusIndicator.setZValue(-2)
        self.scene.addItem(self.focusIndicator)
    
    def initBoardLines (self):
        '''
        Adds the black lines to the scene marking the game field
        0-----0-----0
        |     |     |
        | 0---0---0 |
        | |   |   | |
        | | 0-0-0 | |
        | | |   | | |
        0-0-0   0-0-0
        | | |   | | |
        | | 0-0-0 | |
        | |   |   | |
        | 0---0---0 |
        |     |     |
        0-----0-----0
        
        i = (1,0)
        0 = (0,i),(1, i + 1)
        1 = (1, i + 1),(2, i)
        2 = (2, i),(1, i -1)
        3 = (1, i -1),(0,i)
        '''
        pen = QPen()
        pen.setColor(Qt.black)
        pen.setWidth(5)
        pen.setJoinStyle(Qt.MiterJoin)
        brush = QBrush(Qt.NoBrush)
        
        # add the rings
        for i in range(3):
            dim = self.smallestRingDim + i * self.ringScaleVal
            r = QRectF(0 - dim / 2, 0 - dim / 2, dim, dim)
            self.scene.addRect(r, pen, brush)
            
        # add the connections between the rings
        l = QLineF(0, self.smallestRingDim / 2, 0, (self.smallestRingDim + 2 * self.ringScaleVal) / 2)
        self.scene.addLine(l, pen)
        
        l = QLineF(0, -self.smallestRingDim / 2, 0, -(self.smallestRingDim + 2 * self.ringScaleVal) / 2)
        self.scene.addLine(l, pen)
        
        l = QLineF(self.smallestRingDim / 2, 0, (self.smallestRingDim + 2 * self.ringScaleVal) / 2, 0)
        self.scene.addLine(l, pen)
        
        l = QLineF(-self.smallestRingDim / 2, 0, -(self.smallestRingDim + 2 * self.ringScaleVal) / 2, 0)
        self.scene.addLine(l, pen)
        
    def initBoardPosClickHandler(self):
        '''
        Adds invisible rects to every board location.
        Their function is to handle clicks at still empty board locations.
        They're the same size as a normal piece, and can only trigger a
        mouse click event, when the position is empty. Otherwise the normal
        piece gets the click.
        '''
        for i in range(0, 8 * 3):
            x, y = self.pieceIndexToScreenCoors(i)
            offset = self.pieceDiameter / 2
            x -= offset
            y -= offset
            rect = QRectF(x, y, self.pieceDiameter, self.pieceDiameter)
            self.scene.addItem(BoardPositionClickHandler(rect, i, self.boardPositionClicked))
        
    def updateInfoLabels (self):
        '''
        Updates the instructionLabel, the pieceTypeIndicator and the turnCounterLabel
        in reflection of the current game state.
        '''
        
        player = self.game.getCurrentPlayer()
        
        self.turnCounterLabel.setText("Turn " + str(self.game.turnCounter + 1) + ", " + player.name)
        
        if self.game.board.gamePhase == Board.PieceSetPhase:
            self.instructionLabel.setText("Click on an empty place on the board, to set your piece")
        
        elif self.game.board.gamePhase == Board.PieceMovePhase:
            self.instructionLabel.setText("Select on of your placed pieces and click on an empty place on the board, to move it there")
        
        elif (self.game.board.gamePhase == Board.PieceSetRemovePhase
            or self.game.board.gamePhase == Board.PieceMoveRemovePhase):
            self.instructionLabel.setText("Select on of your opponents pieces to remove it")
        
        elif self.game.board.gamePhase == Board.Remis:
            self.instructionLabel.setText("Remis")
        
        elif self.game.board.gamePhase == Board.BlackWins:
            self.instructionLabel.setText("Black Wins")
        
        elif self.game.board.gamePhase == Board.WhiteWins:
            self.instructionLabel.setText("White Wins")
        
        if player.pieceType == Board.White:
            self.pieceTypeIndicator.setPixmap(QPixmap("assets/white_turn_indicator.png"))
        else:
            self.pieceTypeIndicator.setPixmap(QPixmap("assets/black_turn_indicator.png"))
            
    @pyqtSlot()
    def playerFinishedTurn (self):
        self.focusedPiece = None              
        self.updatePiecePositions()
        self.updateFocusIndicator()
        self.updateInfoLabels()
        
    def pieceItemClicked (self, pieceItem):
        '''
        A piece item on the board was clicked
        '''
        if self.game.doesCurrentPlayerUseMouse():
            if self.game.getCurrentPlayer().pieceItemWasClicked(pieceItem.pieceType, pieceItem.boardIndex):
                self.focusedPiece = pieceItem
                self.updateFocusIndicator()
    
    def boardPositionClicked (self, boardPositionClickHandler):
        '''
        An empty location on the board was clicked
        '''
        if self.game.doesCurrentPlayerUseMouse():
            self.game.getCurrentPlayer().boardPositionWasClicked(boardPositionClickHandler.boardIndex)
    
    def overrideInstructionLabel (self, text):
        '''
        Useful to display the user a custom message.
        Will be replaced with the default again, when a new turn starts
        '''
        self.instructionLabel.setText(text)
    
    @pyqtSlot()
    def showNewGameDialog (self):
        dialog = NewGameDialog(self.startNewGame)
        dialog.exec_()
        
    @pyqtSlot()
    def showHelp (self):
        webbrowser.open("file://" + os.path.realpath("assets/muehle_tutorial.pdf"))
    
    @pyqtSlot()
    def showVictoryWindow(self):
        print("ShowVictory: " + str(self.game.board.gamePhase))
        dialog = GameEndDialog(self.game.board.gamePhase)
        dialog.exec_()
        
    @pyqtSlot()
    def undo (self):
        # Have to abort the game thread first, to prevent a change in 
        # game state, while performing the undo operation
        self.game.abort()
        self.game.wait()

        self.game.undo()
        
        # Update UI
        self.playerFinishedTurn()
        
        # Restart game again
        self.game.start(True)
        
class BoardGraphicsView (QGraphicsView):
    
    def __init__(self, parent=None):
        super(BoardGraphicsView, self).__init__(parent)
        self.setRenderHint(QPainter.HighQualityAntialiasing)
        self.setStyleSheet("background-image: url(assets/game_table.jpg)")
    
class PieceGraphicsItem (QGraphicsPixmapItem):   
    '''
    Represents a black or white piece in the scene
    '''
     
    def __init__ (self, qGraphicsItem, pieceType, clickHandler):
        QGraphicsPixmapItem.__init__(self, qGraphicsItem)
        self.pieceType = pieceType
        self.boardIndex = -1
        self.clickHandler = clickHandler
        
    def mousePressEvent(self, mouseClickEvent):
        if self.boardIndex != -1:
            self.clickHandler(self)
        
class BoardPositionClickHandler (QGraphicsItem):
    '''
    Invisible helper box, to collect click events
    at empty board positions.
    '''
    
    def __init__(self, bounds, boardIndex, clickHandler):
        QGraphicsItem.__init__(self)
        self.bounds = bounds
        self.boardIndex = boardIndex
        self.clickHandler = clickHandler
        self.setZValue(-100)
    
    def mousePressEvent(self, mouseClickEvent):
        self.clickHandler(self) 
        
    def boundingRect(self, *args, **kwargs):
        return self.bounds
    
    def paint(self, *args, **kwargs):
        return
    
class NewGameDialog (QDialog):
    
    def __init__ (self, newGameCallback):        
        QDialog.__init__(self)
        uic.loadUi(relPathToAbs("ui/newgame.ui"), self)
        self.show()
        
        # setup name editing for player 1
        player1NameEdit = self.findChild(QLineEdit, 'player1_name')
        player1NameEdit.textChanged.connect(self.player1NameTextChanged)
        self.player1Name = player1NameEdit.text()
        
        # setup name editing for player 2
        player2NameEdit = self.findChild(QLineEdit, 'player2_name')
        player2NameEdit.textChanged.connect(self.player2NameTextChanged)
        self.player2Name = player2NameEdit.text()
        
        self.okButton = self.findChild(QDialogButtonBox, 'buttonBox')
        
        # setup player types
        playerTypes = [" Human", " AI - Easy", " AI - Medium", " AI - Hard"]
        
        self.comboBox1 = self.findChild(QComboBox, 'player1_types')
        self.comboBox1.addItems(playerTypes)
        
        self.comboBox2 = self.findChild(QComboBox, 'player2_types')
        self.comboBox2.addItems(playerTypes)
        
        self.newGameCallback = newGameCallback
        
    def player1NameTextChanged (self, text):
        self.player1Name = text
        self.evalOk()
        
    def player2NameTextChanged (self, text):
        self.player2Name = text
        self.evalOk()
        
    def evalOk (self):
        '''
        The Ok button should only be clickable, if both players have a name
        that contains at least one character
        '''
        if self.player1Name and self.player2Name:
            self.okButton.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.okButton.button(QDialogButtonBox.Ok).setEnabled(False)
            
    def accept(self):
        # Create player1 and player2 from the choosen configuration
        if self.comboBox1.currentIndex() == 0:
            player1 = HumanPlayer(self.player1Name, Board.White)
        else:
            player1 = AIPlayer(self.player1Name, Board.White, self.comboBox1.currentIndex() - 1)
            
        if self.comboBox2.currentIndex() == 0:
            player2 = HumanPlayer(self.player2Name, Board.Black)
        else:
            player2 = AIPlayer(self.player2Name, Board.Black, self.comboBox2.currentIndex() - 1)
            
        self.newGameCallback(Game(player1, player2))
        QDialog.accept(self)
        
class GameEndDialog (QDialog):
    '''
    A Window with a Gif as background, displaying which color won the game
    '''
    
    def __init__(self, gamePhase):
        QDialog.__init__(self)
        uic.loadUi(relPathToAbs("ui/win.ui"), self)
        
        label = self.findChild(QLabel, 'winner_label')
        if gamePhase == Board.WhiteWins:
            self.setWindowTitle("White Wins")
            label.setText("White Wins")
            label.setStyleSheet("QLabel{color: black;}")
            
        elif gamePhase == Board.BlackWins:
            self.setWindowTitle("Black Wins")
            label.setText("Black Wins")
            label.setStyleSheet("QLabel{color: white;}")
            
        elif gamePhase == Board.Remis:
            self.setWindowTitle("Remis")
            label.setText("Remis")
            label.setStyleSheet("QLabel{color: gray;}")
            
        self.findChild(QGifLabel, "widget").startMov(relPathToAbs("assets/congrats2.gif"))
        self.show()
        
class QGifLabel (QWidget):
    '''
    Custom label-widget capable of displaying a Gif
    '''
    
    def __init__ (self, something):
        QWidget.__init__(self)
        
    def startMov (self, gifPath):
        self.movie = QMovie(gifPath)
        self.movie.frameChanged.connect(self.repaint)
        self.movie.start() 

    def paintEvent(self, event):
        currentFrame = self.movie.currentPixmap()
        frameRect = currentFrame.rect()
        frameRect.moveCenter(self.rect().center())
        if frameRect.intersects(event.rect()):
            painter = QPainter(self)
            painter.drawPixmap(frameRect.left(), frameRect.top(), currentFrame)


        
