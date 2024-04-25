import chess
import reconchess

def nextMovePrediction(piecePlacementString):
    board = chess.Board(piecePlacementString)
    nextPossibleMoves = list(board.pseudo_legal_moves)
    nextPossibleMoves.append(chess.Move.null())

    for move in reconchess.utilities.without_opponent_pieces(board).generate_castling_moves():
        if not reconchess.is_illegal_castle(board, move):
            nextPossibleMoves.append(move)

    nextPossibleMoves = sorted(set(nextPossibleMoves), key=lambda move: move.uci())

    for move in nextPossibleMoves:
        print(move)

fenString = input()
nextMovePrediction(fenString)
