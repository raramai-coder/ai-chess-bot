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
        

    def choose_sense(self, sense_actions, move_actions, seconds_left):
        # Select a sensing action uniformly at random (excluding edge squares).
        valid_sense_actions = [
            action for action in sense_actions if not self.is_edge_square(action)
        ]
        return random.choice(valid_sense_actions)

    def handle_sense_result(self, sense_result):
        # Narrow down list of possible moves
        for square, _ in sense_result:
            self.board.remove_piece_at(square)

        # Place the sensed pieces
        for square, piece in sense_result:
            if piece is not None:
                self.board.set_piece_at(square, piece)


    def choose_move(self, move_actions, seconds_left):
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