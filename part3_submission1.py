import os
import chess
import chess.engine

def moveGeneration(fenString):
    # PATH FOR TESTING
    #engine = chess.engine.SimpleEngine.popen_uci('./stockfish', setpgrp=True)
    # PATH FOR AUTOMARKER
    engine = chess.engine.SimpleEngine.popen_uci('/opt/stockfish/stockfish', setpgrp=True)
    
    board = chess.Board(fenString)
    if board.is_checkmate():
        move = list(board.legal_moves)[0]
    else:
        move = engine.play(board, chess.engine.Limit(time=0.5)).move
    
    engine.quit()
    return move.uci()

fenString = input()
print(moveGeneration(fenString))
