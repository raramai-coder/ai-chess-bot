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
        self.engine = chess.engine.SimpleEngine.popen_uci('stockfish/stockfish-windows-x86-64-avx2.exe')
        self.color = None
        self.board = None
        self.opponent_name = None
        self.possible_boards = set()

    def handle_game_start(self, color, board, opponent_name):
        # Handle initial game setup.
        self.color = color
        self.board = board
        self.opponent_name = opponent_name

        # Initialize the starting state with the known initial board
        self.possible_boards = {board.fen()}

    def handle_opponent_move_result(self, captured_my_piece, capture_square):
        # Update possible states based on opponent's capture result.
        self.my_piece_captured_square = capture_square
        if captured_my_piece:
            self.board.remove_piece_at(capture_square)
        

    def trout_bot_sense(self, sense_actions, move_actions, seconds_left):
          #Trout Bot implementation
         # if our piece was just captured, sense where it was captured
        if self.my_piece_captured_square:
            return self.my_piece_captured_square

        # if we might capture a piece when we move, sense where the capture will occur
        future_move = self.choose_move(move_actions, seconds_left)
        if future_move is not None and self.board.piece_at(future_move.to_square) is not None:
            return future_move.to_square

        # otherwise, just randomly choose a sense action, but don't sense on a square where our pieces are located
        for square, piece in self.board.piece_map().items():
            if piece.color == self.color:
                sense_actions.remove(square)
        
        return random.choice(sense_actions)
    
    def choose_sense(self, sense_actions, move_actions, seconds_left):
        # Get valid sense actions
        valid_sense_actions = [
            action for action in sense_actions if not self.is_edge_square(action)
        ]
        choice = self.trout_bot_sense(self, valid_sense_actions, move_actions, seconds_left)
        return choice

    def handle_sense_result(self, sense_result):
        # Narrow down list of possible moves
        for square, _ in sense_result:
            self.board.remove_piece_at(square)

        # Place the sensed pieces
        for square, piece in sense_result:
            if piece is not None:
                self.board.set_piece_at(square, piece)

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
    
    def calculate_best_move(self,boards):
     # PATH FOR TESTING
    # engine = chess.engine.SimpleEngine.popen_uci('./stockfish', setpgrp=True)
    # PATH FOR AUTOMARKER
        engine = chess.engine.SimpleEngine.popen_uci('/opt/stockfish/stockfish', setpgrp=True)
    
        highestBoardScore = None
        bestMove = ""

        for board in boards:
            move = self.generate_move_for_board(board, engine)
            # move = chess.Move.from_uci(move)
            possibleBoard = chess.Board(board)
            possibleBoard.push(move)
            boardScore = self.get_score_from_move_analysis(possibleBoard, engine)

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
       
        # select move using majority voting
        best_move = self.majority_voting(self,move_actions)

        # select move using board analysis
        # best_move = self.calculate_best_move(self,move_actions)
        return best_move
    
    def handle_move_result(self, requested_move, taken_move, captured_opponent_piece, capture_square):
        # Update possible states based on the actual move executed.
        new_possible_boards = set()

        for fen in self.possible_boards:
            board = chess.Board(fen)
            
            new_board = board.copy()

            try:
                # Make the requested move in this state to see the potential resulting position
                new_board.push(requested_move)

                # If the executed move is different from the requested move, rule out this board
                if new_board.peek() != taken_move:
                    continue

                # Check if the capture outcome matches
                if captured_opponent_piece and new_board.is_capture(capture_square):
                    new_possible_boards.add(new_board)
                elif not captured_opponent_piece and not new_board.is_capture(capture_square):
                    new_possible_boards.add(new_board)
            except Exception as e:
                # If an illegal move exception occurs, exclude this board
                continue

        # Update to only keep the states that are consistent with the move outcome
        self.possible_boards = new_possible_boards

    def handle_game_end(self, winner_color, win_reason, game_history):
        # Terminate the connection to Stockfish and clean up resources."""
        self.engine.quit()

    @staticmethod
    def is_edge_square(square):
        # Check if a square is on the edge of the chessboard.
        row, col = divmod(square, 8)
        return row == 0 or row == 7 or col == 0 or col == 7

# ---------------------------------------------------------------End----------------------------------------------------------------------------------------------#