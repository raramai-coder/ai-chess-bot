
import chess

def nextStatePredictionWithCaptures(fen, captureSquare):
    board = chess.Board(fen)
    captureMoves = []

    for move in board.legal_moves:
        if move.to_square == chess.parse_square(captureSquare):
            board.push(move)
            captureMoves.append(board.fen())
            board.pop()

    return sorted(captureMoves)

fen = input()
captureSquare = input()

nextPossibleStates = nextStatePredictionWithCaptures(fen, captureSquare)
for state in nextPossibleStates:
    print(state)
