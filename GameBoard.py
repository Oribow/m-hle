import copy


def invertPieceType (pieceType):
    '''
    black -> white
    white -> black
    empty -> empty
    '''
    if pieceType == Board.Black:
        return Board.White
    elif pieceType == Board.White:
        return Board.Black
    else:
        return Board.Empty
    
def convIndexToRingNotation (valIndex):
        node = valIndex % 8
        return int((valIndex - node) / 8), node
    
def convRingNotationToIndex (ringIndex, nodeIndex):
    ringIndex = ringIndex % 3
    nodeIndex = nodeIndex % 8
    return ringIndex * 8 + nodeIndex

class Board (object):
    '''
    Designed to hold a the information about the game's current status,
    except the players. This makes it easy for the MinMax algorithm to 
    create it's move tree. All operations on the board are cached, to
    enable undo. 
    A location may appear in 2 different notations (which can be converted into each other):
    1. ring-notation:
        The ring notation consists of a ringIndex and a nodeIndex.
        The rings are counted from out to in, starting at 0 and
        the nodes are counted from top, middle following the ring
        7-----0-----1
        |     |     |Ring 0
        | 7---0---1 |
        | |   |   |Ring 1
        | | 7-0-1 | |
        | | |   |Ring 2
        6-6-6   2-2-2
        | | |   | | |
        | | 5-4-3 | |
        | |   |   | |
        | 5---4---3 |
        |     |     |
        5-----4-----3
    2. index:
        A flat reference to the occupation array. 
        The array follows the exact same counting style, as
        the ring-notation.
        07-----00-----01
        |      |       |
        | 15---08---09 |
        | |    |     | |
        | | 23-16-17 | |
        | | |      | | |
      06-14-22    18-10-02
        | | |      | | |
        | | 21-20-19 | |
        | |    |     | |
        | 13---12---11 |
        |      |       |
        05-----04-----03
    '''
    
    # gamePhases
    PieceSetPhase, PieceMovePhase, PieceMoveRemovePhase, PieceSetRemovePhase, BlackWins, WhiteWins, Remis = range(7)
    
    # pieceTypes
    White, Black, Empty = range(3)
    
    # opCodes (Those starting with "Internal" shouldn't be used outside this class
    OpMove, OpSet, OpRemove, InternalChangePhaseFromSetToMove, InternalChangePhaseFromMoveToEnd, InternalChangePhaseFromSetToRemove, InternalChangePhaseFromMoveToRemove, InternalChangePhaseFromRemoveToMove, InternalChangePhaseFromRemoveToSet = range(9)
    
    def __init__(self, otherBoard=None):
        if otherBoard == None:  # normal constructor
            self.gamePhase = self.PieceSetPhase
            self.unplacedWhitePieces = 0
            self.unplacedBlackPieces = 0
            self.neverPlacedWhitePieces = 9
            self.neverPlacedBlackPieces = 9
            self.opCodeHistory = []
            
            # array containing the occupation of all board positions
            self.values = [Board.Empty] * 8 * 3
            
        else:  # copy constructor
            self.gamePhase = otherBoard.gamePhase
            self.unplacedBlackPieces = otherBoard.unplacedBlackPieces
            self.unplacedWhitePieces = otherBoard.unplacedWhitePieces
            self.neverPlacedWhitePieces = otherBoard.neverPlacedWhitePieces
            self.neverPlacedBlackPieces = otherBoard.neverPlacedBlackPieces
            self.values = copy.copy(otherBoard.values)
            self.opCodeHistory = copy.copy(otherBoard.opCodeHistory)
        
    def getOccupationAt (self, ringIndex, nodeIndex):
        ringIndex = ringIndex % 3
        nodeIndex = nodeIndex % 8
        return self.values[ringIndex * 8 + nodeIndex]
        
    def checkForMuehle (self, ringIndex, nodeIndex):
        '''
        Returns True, if the given piece is part of a muehle, otherwise False.
        '''
        
        # To prevent negative values
        ringIndex += 3
        nodeIndex += 8
        
        nodeVal = self.getOccupationAt(ringIndex, nodeIndex)

        if nodeIndex % 2 != 0:  # corner node (2 connections)
            return ((nodeVal == self.getOccupationAt(ringIndex, nodeIndex - 1) and
                    nodeVal == self.getOccupationAt(ringIndex, nodeIndex - 2)) or
                   (nodeVal == self.getOccupationAt(ringIndex, nodeIndex + 1) and
                    nodeVal == self.getOccupationAt(ringIndex, nodeIndex + 2)))
        else:  # edge node (3 connections)
            return ((nodeVal == self.getOccupationAt(ringIndex, nodeIndex + 1) and
                    nodeVal == self.getOccupationAt(ringIndex, nodeIndex - 1)) or
                    (nodeVal == self.getOccupationAt(ringIndex + 1, nodeIndex) and
                    nodeVal == self.getOccupationAt(ringIndex + 2, nodeIndex)))
    
    def isPieceBlocked(self, ringIndex, nodeIndex):
        '''
        Returns True, if the piece has no connection to an empty field,
        otherwise False
        '''
        if self.getOccupationAt(ringIndex, nodeIndex + 1) == self.Empty:
                return False
        if self.getOccupationAt(ringIndex, nodeIndex - 1) == self.Empty:
                return False
            
        if nodeIndex % 2 == 0:  # edge node
            if ringIndex <= 1 and self.getOccupationAt(ringIndex + 1, nodeIndex) == self.Empty:
                return False
            if ringIndex >= 1 and self.getOccupationAt(ringIndex - 1, nodeIndex) == self.Empty:
                return False  
        return True
        
    def anyUnsafePieceLeft(self, pieceType):
        '''
        Returns False, if all pieces of the given type are part of a Muehle,
        otherwise True
        '''
        for iRing in range(3):
            for iNode in range(8):
                if self.values[iRing * 8 + iNode] != pieceType:
                    continue
                if not self.checkForMuehle(iRing, iNode):
                    return True
        return False
    
    def changeUnplacedPieceCounter(self, pieceType, change):
        if pieceType == self.Black:
            self.unplacedBlackPieces += change
        elif pieceType == self.White:
            self.unplacedWhitePieces += change
            
    def getUnplacedPieceCounter(self, pieceType):
        if pieceType == self.Black:
            return self.unplacedBlackPieces
        elif pieceType == self.White:
            return self.unplacedWhitePieces
        
    def changeNeverPlacedPieceCounter(self, pieceType, change):
        if pieceType == self.Black:
            self.neverPlacedBlackPieces += change
        elif pieceType == self.White:
            self.neverPlacedWhitePieces += change
            
    def getNeverPlacedPieceCounter(self, pieceType):
        if pieceType == self.Black:
            return self.neverPlacedBlackPieces
        elif pieceType == self.White:
            return self.neverPlacedWhitePieces
        
    def setPieceAt (self, valIndex, pieceType):
        if self.getNeverPlacedPieceCounter(pieceType) <= 0:
            return False
        
        if len(self.values) <= valIndex:
            return False 
            
        if self.values[valIndex] != self.Empty:
            return False
        
        self.values[valIndex] = pieceType
        self.changeNeverPlacedPieceCounter(pieceType, -1)
        return True
    
    def movePiece (self, fromValIndex, toValIndex, pieceType):
        if len(self.values) <= fromValIndex:
            return False 
        if len(self.values) <= toValIndex:
            return False 
        if self.values[fromValIndex] != pieceType:
            return False
        if self.values[toValIndex] != self.Empty:
            return False
        
        fromRing, fromNode = convIndexToRingNotation(fromValIndex)
        toRing, toNode = convIndexToRingNotation(toValIndex)
        
        # Only perform the check, if the move destination is connected to
        # the target node, when there are more then 3 pieces of that type left.
        if self.getUnplacedPieceCounter(pieceType) < 9 - 3:
            if fromRing == toRing:
                if abs(toNode - fromNode) != 1 and abs(toNode - fromNode) != 7:
                    return False
            elif abs(fromRing - toRing) == 1:
                if toNode != fromNode:
                    return False
            else:
                return False
            
        self.values[toValIndex] = pieceType
        self.values[fromValIndex] = self.Empty
        return True
            
    def removePieceAt(self, valIndex, pieceType):
        '''
        Removes an opponents piece from the Viewpoint of the supplied
        piece type.
        '''
        nodeVal = self.values[valIndex]
        if nodeVal == pieceType or nodeVal == self.Empty:
            return False
        
        ringIndex, nodeIndex = convIndexToRingNotation(valIndex)
        
        # Checks if the target piece for removing is protected
        if self.checkForMuehle(ringIndex, nodeIndex):
            if self.anyUnsafePieceLeft(invertPieceType(pieceType)):
                return False
            
        self.changeUnplacedPieceCounter(invertPieceType(pieceType,), 1)
        self.values[valIndex] = self.Empty   
        return True
      
    def executeOpCode (self, opCode):
        '''
        Meant to be the goto way to change the board state,
        from outside this class.
        The caller has to supplies a tuple as opCode, consisting
        of the operation type, the pieceType of the caller, and
        some additional information.
        '''
        if  opCode[1] != self.Black and  opCode[1] != self.White:
            print ("Invalid Op Code (1) " + str(opCode))
            return False
        
        if opCode[0] == self.OpSet:
            if self.setPieceAt(opCode[2], opCode[1]):
                self.opCodeHistory.append(opCode)
                # Check if moving created a new Muehle
                toRing, toNode = convIndexToRingNotation(opCode[2])
                if self.checkForMuehle(toRing, toNode):
                    self.gamePhase = self.PieceSetRemovePhase
                    self.opCodeHistory.append((self.InternalChangePhaseFromSetToRemove,))
                return True
            print ("Invalid Op Code (2)" + str(opCode))
            return False
        elif opCode[0] == self.OpMove:
            if self.movePiece(opCode[2], opCode[3], opCode[1]):
                self.opCodeHistory.append(opCode)
                # Check if moving created a new Muehle
                toRing, toNode = convIndexToRingNotation(opCode[3])
                if self.checkForMuehle(toRing, toNode):
                    self.gamePhase = self.PieceMoveRemovePhase
                    self.opCodeHistory.append((self.InternalChangePhaseFromMoveToRemove,))
                return True
            print ("Invalid Op Code (3)" + str(opCode))
            return False
        elif opCode[0] == self.OpRemove:
            if self.removePieceAt(opCode[2], opCode[1]):
                self.opCodeHistory.append(opCode)
                if self.gamePhase == self.PieceMoveRemovePhase:
                    self.opCodeHistory.append((self.InternalChangePhaseFromRemoveToMove,))
                    self.gamePhase = self.PieceMovePhase
                elif self.gamePhase == self.PieceSetRemovePhase:
                    self.opCodeHistory.append((self.InternalChangePhaseFromRemoveToSet,))
                    self.gamePhase = self.PieceSetPhase 
                return True
            print ("Invalid Op Code (4)" + str(opCode))
            return False
        
    def undo (self):
        '''
        Reverse applies a turn
        '''
        while len(self.opCodeHistory) > 0:
            op = self.opCodeHistory.pop()
            if self.invertExecuteOpCode(op):
                break
    
    removeSetFlag = False
    
    def invertExecuteOpCode (self, opCode):
        '''
        As one turn can consist of an internal op code and
        a normal op code, this method returns True, if a normal
        op code has been reverse applied. This signals the
        end of a turn.
        '''
        
        if opCode[0] == self.InternalChangePhaseFromMoveToEnd:
            self.gamePhase = self.PieceMovePhase
            return False
        elif opCode[0] == self.InternalChangePhaseFromSetToMove:
            self.gamePhase = self.PieceSetPhase 
            return False
        elif opCode[0] == self.InternalChangePhaseFromMoveToRemove:
            self.gamePhase = self.PieceMovePhase 
            return False
        elif opCode[0] == self.InternalChangePhaseFromRemoveToMove:
            self.gamePhase = self.PieceMoveRemovePhase
            self.removeSetFlag = False
            return False
        elif opCode[0] == self.InternalChangePhaseFromRemoveToSet:
            self.gamePhase = self.PieceSetRemovePhase
            self.removeSetFlag = True
            return False
        elif opCode[0] == self.InternalChangePhaseFromSetToRemove:
            self.gamePhase = self.PieceSetPhase
            return False
        
        if opCode[0] == self.OpRemove:
            self.values[opCode[2]] = invertPieceType(opCode[1])
            if self.removeSetFlag:
                self.changeUnplacedPieceCounter(invertPieceType(opCode[1]), -1)
            return False
        if opCode[0] == self.OpSet:
            self.values[opCode[2]] = self.Empty  
            self.changeNeverPlacedPieceCounter(opCode[1], 1)
            return True
        if opCode[0] == self.OpMove:
            self.movePiece(opCode[3], opCode[2], opCode[1])
            return True
          
    def checkBoardState (self, nextPlayerPieceType):
        '''
        Should be called after the a call to executeOpCode().1
        Checks the board for terminal states (one party one, or remis) and
        gamePhase changes.
        '''
        if self.gamePhase == Board.PieceSetPhase:
            if self.neverPlacedBlackPieces == 0 and self.neverPlacedWhitePieces == 0:
                self.opCodeHistory.append((self.InternalChangePhaseFromSetToMove,))
                
                if not self.anyUnblockedPieceLeft(nextPlayerPieceType):
                    self.opCodeHistory.append((self.InternalChangePhaseFromMoveToEnd,))
                    self.letPieceTypeWin(invertPieceType(nextPlayerPieceType))
                    print ("Win 0")
                    
                else:
                    self.gamePhase = Board.PieceMovePhase
        else:
            if not self.anyUnblockedPieceLeft(nextPlayerPieceType):
                self.opCodeHistory.append((self.InternalChangePhaseFromMoveToEnd,))
                self.letPieceTypeWin(invertPieceType(nextPlayerPieceType))
                print ("Win 1")
                
            if self.unplacedBlackPieces >= 9 - 2:
                self.opCodeHistory.append((self.InternalChangePhaseFromMoveToEnd,))
                self.gamePhase = Board.WhiteWins
                print ("Win 2")
                
            elif self.unplacedWhitePieces >= 9 - 2:
                self.opCodeHistory.append((self.InternalChangePhaseFromMoveToEnd,))
                self.gamePhase = Board.BlackWins 
                print ("Win 3")
    
    def letPieceTypeWin (self, pieceType):
        if pieceType == self.Black:
            self.gamePhase = self.BlackWins
        else:
            self.gamePhase = self.WhiteWins    
            
    def anyUnblockedPieceLeft(self, pieceType):
        '''
        Returns True, if at least 1 piece of the supplied piece type
        has a connection to an empty field. Otherwise it returns False
        '''
        
        for iRing in range(3):
            for iNode in range(8):
                if self.values[iRing * 8 + iNode] != pieceType:
                    continue
                
                if not self.isPieceBlocked(iRing, iNode):
                    return True
        return False   
    
            
            
                
                    
            
            
            
            
            
            
