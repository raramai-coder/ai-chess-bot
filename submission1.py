import chess

def representBoard(piecePlacementString):
    board = chess.Board(piecePlacementString)
    print(board)


fenString = input()

splitFEN = fenString.split(" ")

piecePlacement = splitFEN[0]
activeColor = splitFEN[1]
castingAvailability = splitFEN[2]
enPassant = splitFEN[3]
halfMoveClock = splitFEN[4]
fullMoveClock = splitFEN[5]

representBoard(piecePlacement)

