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

    return nextPossibleMoves

def nextStatePrediction(fenString):
    nextPossibleMoves = nextMovePrediction(fenString)
    fen_strings = []  # List initialised to store FEN strings

    for move in nextPossibleMoves:
        board = chess.Board(fenString)
        board.push(move)
        fen_strings.append(board.fen())  # Append FEN string to the list

    fen_strings.sort()  # Sort the list of FEN strings alphabetically
    for fen in fen_strings:
        print(fen)


fenString = input()
nextStatePrediction(fenString)
