import chess
import chess.engine

def get_score_from_move_analysis(board):
     # PATH FOR TESTING
    # engine = chess.engine.SimpleEngine.popen_uci('./stockfish', setpgrp=True)
    # PATH FOR AUTOMARKER
    engine = chess.engine.SimpleEngine.popen_uci('/opt/stockfish/stockfish', setpgrp=True)
    info = engine.analyse(board, chess.engine.Limit(depth=20))
    engine.quit()
    return info["score"]

def generate_move_for_board(fenString):
    # PATH FOR TESTING
    # engine = chess.engine.SimpleEngine.popen_uci('./stockfish', setpgrp=True)
    # PATH FOR AUTOMARKER
    engine = chess.engine.SimpleEngine.popen_uci('/opt/stockfish/stockfish', setpgrp=True)
    
    board = chess.Board(fenString)
    if board.is_checkmate():
        move = list(board.legal_moves)[0]
    else:
        move = engine.play(board, chess.engine.Limit(time=0.1)).move
    
    engine.quit()
    return move

def calculate_best_move(boards):
    highestBoardScore = None
    bestMove = ""
    for board in boards:
        move = generate_move_for_board(board)
        # move = chess.Move.from_uci(move)
        possibleBoard = chess.Board(board)
        possibleBoard.push(move)
        boardScore = get_score_from_move_analysis(possibleBoard)

        if highestBoardScore is None:
            highestBoardScore = boardScore.white()
            bestMove = move.uci()
        elif( boardScore.white() >highestBoardScore):
            highestBoardScore =  boardScore.white()
            bestMove = move.uci()
        elif  boardScore.white() == highestBoardScore:
            # take move with in alphabetical order
            movesIncontention  = sorted([bestMove, move.uci()])
            bestMove = movesIncontention[0]
    
    return bestMove

possibleBoards = input()
numberOfPossibleBoards = int(possibleBoards)
boards=[]

for x in range(numberOfPossibleBoards):
    fen = input()
    boards.append(fen)

bestMove = calculate_best_move(boards)
print(bestMove)