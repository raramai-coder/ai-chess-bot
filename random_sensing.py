from reconchess import Player
import chess
import chess.engine
import random
from collections import Counter


class RandomSensingAgent(Player):
    def __init__(self):
        # Initialize Stockfish connection
        self.my_piece_captured_square = None
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
        self.possible_boards = {self.board.fen()}

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
        random_action = random.choice(valid_sense_actions)
        # print(random_action) debug print
        return random_action

    def handle_sense_result(self, sense_result):
        sensed_pieces = {square: piece for square, piece in sense_result}
        new_possible_boards = set()
        for fen in self.possible_boards:
            board = chess.Board(fen)
            match = all(board.piece_at(square) == piece for square, piece in sensed_pieces.items())
            if match:
                new_possible_boards.add(board.fen())
        self.possible_boards = new_possible_boards

        for fen in self.possible_boards:
            print(fen)

    def choose_move(self, move_actions, seconds_left):
        if not self.possible_boards:
            return random.choice(move_actions)
        move_counter = Counter()
        # time limit
        time_per_board = max(10 / max(len(self.possible_boards), 1), 0.01)  # Safeguard against too low values
        try:
            for fen in self.possible_boards:
                board = chess.Board(fen)  # Create a new chess.Board from the FEN string
                with self.engine.analysis(board, chess.engine.Limit(time=time_per_board)) as analysis:
                    info = analysis.get()
                    if "pv" in info:
                        best_move = info["pv"][0]
                        move_counter[best_move] += 1
        except Exception as e:
            print(f"Error analysing board {fen}: {str(e)}")
            # print(move_counter[best_move])  # debug print

        # Majority voting
        if move_counter:
            best_move = move_counter.most_common(1)[0][0]
        else:
            best_move = random.choice(move_actions)

        return best_move

    def handle_move_result(self, requested_move, taken_move, captured_opponent_piece, capture_square):
        new_possible_boards = set()

        for fen in self.possible_boards:
            board = chess.Board(fen)

            try:
                # Attempt to apply the requested move on the board
                board.push(requested_move)
            except ValueError:
                print(f"Attempted illegal move {requested_move} on board {fen}")
                continue  # if the move is illegal, skip this board state.

            # Check if the move taken matches the actual move that occurred
            actual_move = board.peek()  # Get the last move made on this board state
            if actual_move != taken_move:
                continue  # If they do not match, this board state is no longer possible

            # If a capture was reported, verify it
            if captured_opponent_piece:
                if capture_square is not None and board.is_capture(taken_move):
                    new_possible_boards.add(board.fen())
            else:
                if capture_square is None or not board.is_capture(taken_move):
                    new_possible_boards.add(board.fen())

        # Update the set of possible boards to only those that are still valid
        self.possible_boards = new_possible_boards

    def handle_game_end(self, winner_color, win_reason, game_history):
        # Terminate the connection to Stockfish and clean up resources.
        self.engine.quit()

    @staticmethod
    def is_edge_square(square):
        # Check if a square is on the edge of the chessboard.
        row, col = divmod(square, 8)
        return row == 0 or row == 7 or col == 0 or col == 7
