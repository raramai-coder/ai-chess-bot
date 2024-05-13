import chess
import chess.engine

def get_score_from_move_analysis(board, engine):
    info = engine.analyse(board, chess.engine.Limit(depth=20))
    return info["score"]

def generate_move_for_board(fenString,engine):
    
    board = chess.Board(fenString)
    if board.is_checkmate():
        move = list(board.legal_moves)[0]
    else:
        move = engine.play(board, chess.engine.Limit(time=0.1)).move
    
    return move

def calculate_best_move(boards):
     # PATH FOR TESTING
    # engine = chess.engine.SimpleEngine.popen_uci('./stockfish', setpgrp=True)
    # PATH FOR AUTOMARKER
    engine = chess.engine.SimpleEngine.popen_uci('/opt/stockfish/stockfish', setpgrp=True)
    
    highestBoardScore = None
    bestMove = ""

    for board in boards:
        move = generate_move_for_board(board, engine)
        # move = chess.Move.from_uci(move)
        possibleBoard = chess.Board(board)
        possibleBoard.push(move)
        boardScore = get_score_from_move_analysis(possibleBoard, engine)

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
    
    engine.quit()

    return bestMove

possibleBoards = input()
numberOfPossibleBoards = int(possibleBoards)
boards=[]

for x in range(numberOfPossibleBoards):
    fen = input()
    boards.append(fen)

bestMove = calculate_best_move(boards)
print(bestMove)