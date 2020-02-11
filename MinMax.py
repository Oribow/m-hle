from asyncio.tasks import sleep

from GameBoard import Board, invertPieceType, convRingNotationToIndex, convIndexToRingNotation


infinity = 10000000000

def nextPossibleMoves (board, pieceType):
    '''
    Returns all possible next board moves for the given board.
    '''
    
    if board.gamePhase == Board.PieceSetPhase:  # Set moves
        for iVal in range(len(board.values)):
            if board.values[iVal] == Board.Empty:
                yield (Board.OpSet, pieceType, iVal)
    elif board.gamePhase == Board.PieceMovePhase:  # move moves
        for iRing in range(3):
            for iNode in range(8):
                nodeVal = iRing * 8 + iNode
                if board.values[nodeVal] != pieceType:
                    continue
                
                if board.getUnplacedPieceCounter(pieceType) >= 9 - 3:
                    index = 0
                    for iVal in board.values:
                        if iVal == Board.Empty:
                            yield (Board.OpMove, pieceType, nodeVal, index)
                        index += 1
                    continue
                if board.getOccupationAt(iRing, iNode + 1) == Board.Empty:
                    yield (Board.OpMove, pieceType, nodeVal, convRingNotationToIndex(iRing, iNode + 1))
                if board.getOccupationAt(iRing, iNode - 1) == Board.Empty:
                    yield (Board.OpMove, pieceType, nodeVal, convRingNotationToIndex(iRing, iNode - 1))             
                if iNode % 2 == 0:  # edge node
                    if iRing <= 1 and board.getOccupationAt(iRing + 1, iNode) == Board.Empty:
                        yield (Board.OpMove, pieceType, nodeVal, convRingNotationToIndex(iRing + 1, iNode))  
                    if iRing >= 1 and board.getOccupationAt(iRing - 1, iNode) == Board.Empty:
                        yield (Board.OpMove, pieceType, nodeVal, convRingNotationToIndex(iRing - 1, iNode))
    elif (board.gamePhase == Board.PieceSetRemovePhase
          or board.gamePhase == Board.PieceMoveRemovePhase):
        opponentPieceType = invertPieceType(pieceType)
        for iVal in range(len(board.values)):
            if board.values[iVal] == opponentPieceType:
                iRing, iNode = convIndexToRingNotation(iVal)
                if board.checkForMuehle(iRing, iNode):
                    if not board.anyUnsafePieceLeft(invertPieceType(pieceType)):
                        yield (Board.OpRemove, pieceType, iVal)
                    continue
                yield (Board.OpRemove, pieceType, iVal)

def nextBoardStates (board, pieceType):
    '''
    Returns all possible next board states for the given board.
    '''
    
    for move in nextPossibleMoves(board, pieceType):
        cpyBoard = Board(board)
        cpyBoard.executeOpCode(move)
        yield cpyBoard, move
                
def isTerminal (board, nextPlayerPieceType):
    '''
    Checks if the game is over
    '''
    board.checkBoardState(nextPlayerPieceType)
    return (board.gamePhase == Board.WhiteWins or
            board.gamePhase == Board.BlackWins or
            board.gamePhase == Board.Remis)

def evaluateTerminalState(board, pieceType):
    '''
    Assigns a game over state it's value
    '''
    if board.gamePhase == Board.BlackWins:
        if pieceType == Board.Black:
            return infinity
        else:
            return -infinity
    if board.gamePhase == Board.WhiteWins:
        if pieceType == Board.Black:
            return -infinity
        else:
            return infinity
    if board.gamePhase == Board.Remis:
        return 0
    
def bestNextMove(board, pieceType, depth, progressChange=None):
    '''
    Returns best next move for Agent, using Alpha Beta Min Max search
    '''
    
    alpha = -infinity 
    bestMove = None
    counter = 0
    topLevelPossibleMoveCount = 100 / countTopLevelPossibleMoves(board, pieceType)
    for newBoard, opCode in nextBoardStates(board, pieceType):
        result = minScore(newBoard, depth - 1, pieceType, invertPieceType(pieceType), alpha, infinity)
        if result > alpha:
            alpha = result
            bestMove = opCode
        if alpha >= infinity:
            break
        if progressChange != None:
            progressChange("%.2f" % (topLevelPossibleMoveCount * counter))
        counter += 1
    return bestMove

def countTopLevelPossibleMoves (board, pieceType):
    counter = 0
    for m in nextPossibleMoves(board, pieceType):
        counter += 1
    return counter
    
def minScore (board, depth, pieceType, currentPlayerPieceType, alpha, beta):
    if isTerminal(board, invertPieceType(currentPlayerPieceType)):
        return evaluateTerminalState(board, pieceType)
    
    if depth <= 0:
        return evaluateBoardState(board, pieceType, currentPlayerPieceType)
    
    for newBoard, op in nextBoardStates(board, currentPlayerPieceType):
        result = maxScore(newBoard, depth - 1, pieceType, invertPieceType(currentPlayerPieceType), alpha, beta)
        beta = min(beta, result)
        
        if alpha >= beta:
            return alpha
    return beta

def maxScore (board, depth, pieceType, currentPlayerPieceType, alpha, beta):
    if isTerminal(board, currentPlayerPieceType):
        return evaluateTerminalState(board, pieceType)
    if depth <= 0:
        return evaluateBoardState(board, pieceType, currentPlayerPieceType)
    
    for newBoard, op in nextBoardStates(board, currentPlayerPieceType):
        result = minScore(newBoard, depth - 1, pieceType, invertPieceType(currentPlayerPieceType), alpha, beta)
        alpha = max(alpha, result)
           
        if alpha >= beta:
            return beta
    return alpha    


def evaluateBoardState (board, pieceType, currentPlayerPieceType):
    threePiecesCounter = evaluateNumberOfThreePieceSets(board, pieceType)
    piecesCounter = (9 - board.getUnplacedPieceCounter(pieceType) - board.getNeverPlacedPieceCounter(pieceType))
    piecesCounter -= (9 - board.getUnplacedPieceCounter(invertPieceType(pieceType)) - board.getNeverPlacedPieceCounter(invertPieceType(pieceType)))
    blockedPiecesCounter = evaluateNumberOfBlockedPieces(board, pieceType) 
    twoPiecesCounter = evaluateNumberOfTwoPiecesSets(board, pieceType)
    muehleCounter, doubleMuehleCounter = evaluateMuehles(board, pieceType) 
    
    muehleClosedCounter = 0
    if len(board.opCodeHistory) != 0:
        lastOpCode = board.opCodeHistory[len(board.opCodeHistory) - 1]
        if (lastOpCode[0] == Board.InternalChangePhaseFromRemoveToMove or
            lastOpCode[0] == Board.InternalChangePhaseFromRemoveToSet):
            if currentPlayerPieceType == pieceType:
                muehleClosedCounter = -1
            else:
                muehleClosedCounter = 1

    if (board.gamePhase == Board.PieceSetPhase or board.gamePhase == Board.PieceSetRemovePhase): 
        return 18 * muehleClosedCounter + 26 * muehleCounter + 1 * blockedPiecesCounter + 9 * piecesCounter + 10 * twoPiecesCounter + 7 * threePiecesCounter + 0 * doubleMuehleCounter 
    elif (board.gamePhase == Board.PieceMovePhase
        or board.gamePhase == Board.PieceMoveRemovePhase): 
        if board.getUnplacedPieceCounter(currentPlayerPieceType) >= 9 - 3:
            return 16 * muehleClosedCounter + 0 * muehleCounter + 0 * blockedPiecesCounter + 0 * piecesCounter + 10 * twoPiecesCounter + 1 * threePiecesCounter + 0 * doubleMuehleCounter 
        return 14 * muehleClosedCounter + 43 * muehleCounter + 10 * blockedPiecesCounter + 11 * piecesCounter + 0 * twoPiecesCounter + 0 * threePiecesCounter + 8 * doubleMuehleCounter 
               
def evaluateNumberOfBlockedPieces(board, pieceType): 
    counter = 0
    for iRing in range(3):
        for iNode in range(8):
            val = board.getOccupationAt(iRing, iNode)
            if val == Board.Empty:
                continue
         
            if board.isPieceBlocked(iRing, iNode): 
                if val == pieceType: 
                    counter -= 1 
                else:
                    counter += 1 
    return counter    
            
def evaluateNumberOfTwoPiecesSets (board, pieceType):
    counter = 0
    
    for iRing in range(3):
        for iRow in range(4):   
            iStartNode = (7 + iRow * 3) % 8
            
            firstNodeType = Board.Empty
            containedOneEmptyField = False
            
            for rowOffset in range (3):
                val = board.getOccupationAt(iRing, iStartNode + rowOffset)
                
                if val == Board.Empty:
                    if containedOneEmptyField:
                        firstNodeType = Board.Empty
                        break
                    containedOneEmptyField = True
                    continue
                
                if firstNodeType == Board.Empty:
                    firstNodeType = val
                    
                elif firstNodeType != val:
                    firstNodeType = Board.Empty
                    break
            
            if containedOneEmptyField and firstNodeType != Board.Empty:
                if firstNodeType == pieceType:
                    counter += 1
                else:
                    counter -= 1
                    
    for iVRow in range(4):
        iStartNode = 2 * iVRow
        
        firstNodeType = Board.Empty
        containedOneEmptyField = False
        
        for iRing in range (3):
            val = board.getOccupationAt(iRing, iStartNode)
            
            if val == Board.Empty:
                if containedOneEmptyField:
                        firstNodeType = Board.Empty
                        break
                containedOneEmptyField = True
                continue
            
            if firstNodeType == Board.Empty:
                firstNodeType = val
                
            elif firstNodeType != val:
                firstNodeType = Board.Empty
                break
        
        if containedOneEmptyField and firstNodeType != Board.Empty:
            if firstNodeType == pieceType:
                counter += 1
            else:
                counter -= 1
                
    return counter
            
def evaluateMuehles(board, pieceType): 
    counter = 0
    doubleCounter = 0
    
    prevRowWasMuehle = False
    firstRowWasMuehle = False
    for iRing in range(3):
        for iRow in range(4):   
            muehleType = checkRowForMuehle(board, iRing, iRow)
            
            if muehleType != Board.Empty:
                if muehleType == pieceType:
                    counter += 1
                else:
                    counter -= 1
                
                if prevRowWasMuehle:
                    doubleCounter += 1
                
                vPieceType = checkVRowForMuehle(board, iRow)
                if vPieceType == pieceType:
                    doubleCounter += 1
                elif vPieceType != Board.Empty:
                    doubleCounter -= 1
                    
                if iRow == 0:
                    firstRowWasMuehle = True
                prevRowWasMuehle = True
            else:
                prevRowWasMuehle = False
                
        if prevRowWasMuehle and firstRowWasMuehle:
            doubleCounter += 1
            
    return counter, doubleCounter

def evaluateNumberOfThreePieceSets (board, pieceType):
    counter = 0
    for iRing in range(3):
        for iCorner in range(4):
            firstNodeType = Board.Empty
            iStartNode = iCorner * 2 + 8
            for conerOffset in range(3):
                val = board.getOccupationAt(iRing, iStartNode + conerOffset)
                if val == Board.Empty or (firstNodeType != Board.Empty and firstNodeType != val):
                    firstNodeType = Board.Empty
                    break
                firstNodeType = val
            if firstNodeType != Board.Empty:
                # Now check if both ends of the corner connect to a free place
                if (board.getOccupationAt(iRing, iStartNode - 1) != Board.Empty or
                    board.getOccupationAt(iRing, iStartNode + 3) != Board.Empty):
                    continue
                if firstNodeType == pieceType:
                    counter += 1
                else:
                    counter -= 1
    
    for iVRow in range (4):
        startNodeIndex = iVRow * 2 + 8
        middleVal = board.getOccupationAt(1, startNodeIndex)
        if middleVal == Board.Empty:
            continue
        
        rowOffset = [0, 1, 1, 0, 0, -1, -1, 0, -1, 0, 0, 1, -1, 0, 0, 1]
        ringOffset = [0, 1, 1, 2, 2, 1, 1, 0, 0, 0, 0, 0, 2, 2, 2, 2]
        
        rowOffsetCheck = [0, -1, 0, -1, 0, 1, 0, 1, 1, 0, 0, -1, 1, 0, -1, 0]
        ringOffsetCheck = [2, 1, 0, 1, 0, 1, 2, 1, 0, 2, 2, 0, 2, 0, 2, 0]
        
        for iCornor in range (0, 8, 2):
            outerVal1 = board.getOccupationAt(ringOffset[iCornor], rowOffset[iCornor] + startNodeIndex)
            outerVal2 = board.getOccupationAt(ringOffset[iCornor + 1], rowOffset[iCornor + 1] + startNodeIndex)
            
            if outerVal2 != middleVal or outerVal1 != middleVal:
                continue
            
            # Now check if both ends of the corner connect to a free place
            if (board.getOccupationAt(ringOffsetCheck[iCornor], rowOffsetCheck[iCornor] + startNodeIndex) != Board.Empty or
                board.getOccupationAt(ringOffsetCheck[iCornor + 1], rowOffsetCheck[iCornor + 1] + startNodeIndex) != Board.Empty):
                continue
            
            if middleVal == pieceType:
                counter += 1
            else:
                counter -= 1
                    
    return counter     
          
def checkRowForMuehle (board, iRing, iRow):
    iStartNode = (8 + iRow * 2) - 1
            
    firstNodeType = Board.Empty
    
    for rowOffset in range (3):
        val = board.getOccupationAt(iRing, iStartNode + rowOffset)
        
        if val == Board.Empty or (firstNodeType != Board.Empty and firstNodeType != val):
            return Board.Empty
        
        firstNodeType = val
    
    return firstNodeType    

def checkVRowForMuehle (board, iVRow):
    iStartNode = 2 * iVRow
        
    firstNodeType = Board.Empty

    for iRing in range (3):
        val = board.getOccupationAt(iRing, iStartNode)
        
        if val == Board.Empty or (firstNodeType != Board.Empty and firstNodeType != val):
            return Board.Empty
        
        firstNodeType = val
    return firstNodeType
            
            
            
            
