# Importing libraries
from reconchess import Player
import chess
import chess.engine
import random
from collections import Counter


#---------------------------Baseline Agent ---------------------------------------------------------------------------------------------------------#

class MyAgent(Player):
    def __init__(self):
        # Initialize Stockfish connection
        self.engine = chess.engine.SimpleEngine.popen_uci('./stockfish', setpgrp=True)
        self.color = None
        self.board = None
        self.opponent_name = None
        self.possible_boards = set()
        self.future_move = None
        self.future_move_board = None

    def handle_game_start(self, color, board, opponent_name):
        # Handle initial game setup.
        self.color = color
        self.board = board
        self.opponent_name = opponent_name

        # Initialize the starting state with the known initial board
        if board.turn == color:
            self.possible_boards = {board.fen()}  #if my turn, possible boards is just the starting board
        else:
            self.possible_boards = self.generate_possible_board_for_all_possible_boards(boards= {board.fen()})   #if my opponents turn, possible boards is all boards after my opponent's possible moves

    def handle_opponent_move_result(self, captured_my_piece, capture_square):
        # Update possible states based on opponent's capture result.
        self.my_piece_captured_square = capture_square
        if captured_my_piece:
            self.board.remove_piece_at(capture_square)

        #TODO: for all possible boards remove the boards where opponent could not have captured my piece check for where my piece was under attack, and remove boards where i was not
        

    def trout_bot_sense(self, sense_actions, move_actions, seconds_left):
          #Trout Bot implementation
         # if our piece was just captured, sense where it was captured
        if self.my_piece_captured_square:
            return self.my_piece_captured_square

        # if we might capture a piece when we move, sense where the capture will occur
        future_move = self.calculate_best_move(move_actions, seconds_left=seconds_left)
        self.future_move = future_move
        if future_move is not None and self.board.piece_at(future_move.to_square) is not None:
            self.future_move = future_move
            return future_move.to_square
        
        if self.board.halfmove_clock <2:
            return chess.parse_square('e3')

        # otherwise, just randomly choose a sense action, but don't sense on a square where our pieces are located
        for square, piece in self.board.piece_map().items():
            if piece.color == self.color and square in sense_actions:
                sense_actions.remove(square)
        
        return random.choice(sense_actions)
    
    def choose_sense(self, sense_actions, move_actions, seconds_left):
        # Get valid sense actions
        valid_sense_actions = [
            action for action in sense_actions if not self.is_edge_square(action)
        ]
        choice = self.trout_bot_sense( sense_actions=valid_sense_actions, move_actions=move_actions, seconds_left=seconds_left)
        # choice = random.choice(valid_sense_actions)
        return choice

    def handle_sense_result(self, sense_result):
        new_possible_boards = set()
        
        # Narrow down list of possible moves
        for square, _ in sense_result:
            self.board.remove_piece_at(square)

        # Place the sensed pieces
        for square, piece in sense_result:
            if piece is not None:
                self.board.set_piece_at(square, piece)
        
        for boardFEN in self.possible_boards:
            board = chess.Board(boardFEN)
            valid = True
            for square, piece in sense_result:
                if piece is not None and board.piece_at(square) is not None:
                    if piece.symbol() != board.piece_at(square).symbol():
                        valid = False
                elif piece is None and board.piece_at(square) is not None:
                    valid = False
                elif piece is not None and board.piece_at(square) is None:
                    valid = False
            if valid:
                new_possible_boards.add(boardFEN)

        self.possible_boards = new_possible_boards

        if self.future_move_board not in self.possible_boards:
            self.future_move = None

        print("Num of possible boards after sensing: ", len(self.possible_boards))

        # # sense_result is a list of tuples where each tuple contains a sqaure and a piece if any present on that square after the sensing action
        # sensed_pieces = {square: piece for square, piece in sense_result} # dictionary that maps each sensed square to the piece found on the square. If the square is empty, the piece will be None
        # # print((sensed_pieces)) # debug print
        # new_possible_boards = set() # initialise  a new set that will store board states with the sense information
        # # iterating over each board state the agent has considered so far
        # for fen in self.possible_boards:
        #     board = chess.Board(fen)
        #     # print((board))
        #     # iterates over all sensed squares and pieces. If the piece on a square in the current board matches the piece in the sensed_pieces. returns True if pieces match.
        #     match = all(board.piece_at(square) == piece for square, piece in sensed_pieces.items())
        #     print(match)
        #     if match:
        #     # The matched pieces can then be added to the new possible board set
        #         new_possible_boards.add(board.fen())

        # # the agent's set of possible board is updated to include only board states that have sensed information and discards the rest.
        # self.possible_boards = new_possible_boards
        # # print(self.possible_boards)

    def get_score_from_move_analysis(self,board):
        info = self.engine.analyse(board, chess.engine.Limit(depth=20))
        return info["score"]

    def generate_move_for_board(self,board,seconds_left):
    
        board.turn = self.color
        if board.is_checkmate():
            move = list(board.legal_moves)[0]
        else:
            # time_per_board = max(seconds_left / max(len(self.possible_boards), 1), 0.01)  # Safeguard against too low values
            # if time_per_board > 10:
            #     time_per_board = 0.1
            time_per_board = max(5 / max(len(self.possible_boards), 1), 0.01)  # Safeguard against too low values
            move = self.engine.play(board, chess.engine.Limit(time=time_per_board)).move
    
        return move
    
    def calculate_best_move(self,move_actions, seconds_left):
       
        highestBoardScore = None
        bestMove = None
        bestMoveBoard = None

        if not self.possible_boards:
            return random.choice(move_actions)

        for board in self.possible_boards:
            possibleBoard = chess.Board(board)
            move = self.generate_move_for_board(possibleBoard, seconds_left)

            if(seconds_left<10):
                break

            if move in move_actions:
                possibleBoard.push(move)
                boardScore = self.get_score_from_move_analysis(possibleBoard)
                
                scoreToCheck = boardScore.white()
                if not self.color:
                    scoreToCheck = boardScore.black()

                if highestBoardScore is None:
                    highestBoardScore = scoreToCheck
                    bestMove = move
                    bestMoveBoard = board
                elif(scoreToCheck >highestBoardScore):
                    highestBoardScore =  scoreToCheck
                    bestMove = move 
                    bestMoveBoard = board 
                 
        if bestMove is None:
            return random.choice(move_actions) 
        else:
            self.future_move_board = bestMoveBoard  

        return bestMove
    
    def majority_voting(self, move_actions ):
         # Select a move to play using majority voting strategy
        if not self.possible_boards:
            return random.choice(move_actions)
    
        move_counter = Counter()

        # Set a time limit to divide seconds evenly
        time_per_board = max(10 / max(len(self.possible_boards), 1), 0.01)  # Safeguard against too low values

        for fen in self.possible_boards:
            board = chess.Board(fen)  

            with self.engine.analysis(board, chess.engine.Limit(time=time_per_board)) as analysis:
                info = analysis.get()
                if "pv" in info:
                    best_move = info["pv"][0]
                    move_counter[best_move] += 1

        # Majority voting
        if move_counter:
            best_move = move_counter.most_common(1)[0][0]
        else:
            best_move = random.choice(move_actions)

        return best_move
    
    def choose_move(self, move_actions, seconds_left):
       
        print("Num of possible boards before choosing move: ", len(self.possible_boards))
        # select move using majority voting
        # best_move = self.majority_voting(move_actions)

        # TODO: find a better way to verify that the chosen best move is best move after sensing
        if self.future_move is not None and self.future_move in move_actions:   
            best_move = self.future_move
            return best_move
        # select move using board analysis
        best_move = self.calculate_best_move(move_actions, seconds_left)

        # best_move = random.choice(move_actions)
        return best_move
    
    def handle_move_result(self, requested_move, taken_move, captured_opponent_piece, capture_square):
        
        if(taken_move is not None):
            self.board.push(taken_move)

        # Update possible states based on the actual move executed.
        new_possible_boards = set()

        for fen in self.possible_boards:
            current_board = chess.Board(fen)
            
            new_board = current_board.copy()

            try:
                # Make the requested move in this state to see the potential resulting position
                new_board.push(requested_move)

                # If the executed move is different from the requested move, rule out this board
                if new_board.peek() != taken_move:
                    continue

                
                # Check if the capture outcome matches
                if captured_opponent_piece and current_board.is_capture(taken_move):
                    new_possible_boards.add(new_board.fen())
                    #TODO: track opponent capturesd peice and then sense it
                elif not captured_opponent_piece and not current_board.is_capture(taken_move):
                    new_possible_boards.add(new_board.fen())
            except Exception as e:
                # If an illegal move exception occurs, exclude this board
                continue

        # Update to only keep the states that are consistent with the move outcome
       
        expanded_new_possible_boards = self.generate_possible_board_for_all_possible_boards(new_possible_boards)
        self.possible_boards = expanded_new_possible_boards
        print("Num of possible boards after making move: ", len(self.possible_boards))
        
    def is_opponent_piece(self, move, board):
        from_square = move.from_square
        piece = board.piece_at(from_square)
        if piece.color== self.color:
            return False
        else:
            return True
    
    def generate_possible_boards_from_board(self,boardFEN):
        board =  chess.Board(boardFEN)
        possible_moves = list(board.pseudo_legal_moves)
        possible_boards = set()

        for move in possible_moves:
            new_board = board.copy()
            new_board.push(move)
            possible_boards.add(new_board.fen())
        
        return possible_boards
    
    def generate_possible_board_for_all_possible_boards(self, boards):
        new_possible_boards = set()

        for board in boards:
            new_boards = self.generate_possible_boards_from_board(board)
            # new_possible_boards.add(board)
            if new_boards:
                new_possible_boards = new_possible_boards | new_boards

        return new_possible_boards
                
    
    def handle_game_end(self, winner_color, win_reason, game_history):
        # Terminate the connection to Stockfish and clean up resources."""
        self.engine.quit()

    @staticmethod
    def is_edge_square(square):
        # Check if a square is on the edge of the chessboard.
        row, col = divmod(square, 8)
        return row == 0 or row == 7 or col == 0 or col == 7

# ---------------------------------------------------------------End----------------------------------------------------------------------------------------------#