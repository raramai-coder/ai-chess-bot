import chess

def representBoard(current_board_State_String, move_to_be_playedString):
    board = chess.Board(current_board_State_String)  # initialise the current board state

    move = chess.Move.from_uci(move_to_be_playedString)
    if move in board.legal_moves:
        board.push(move)
    else:
        print('Invalid move')

    return board

fenString = input("")  # a full FEN string from the user
moveString = input("") # should be a string that represents the start and end square that the pieces move to. eg.('a1a8') 


new_board = representBoard(fenString, moveString)
print(new_board.fen())