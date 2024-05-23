import chess.engine
import random
from reconchess import *
import os

# Set the environment variable in the script (remove this if you set it in your system)
os.environ['STOCKFISH_EXECUTABLE'] = 'C:/Users/smwmb/PycharmProjects/ChessAIproject/stockfish/stockfish-windows-x86-64-avx2.exe'

class TroutBot(Player):
    def __init__(self):
        self.board = None
        self.color = None
        self.my_piece_captured_square = None

        # make sure stockfish environment variable exists
        if 'STOCKFISH_EXECUTABLE' not in os.environ:
            raise KeyError(
                'TroutBot requires an environment variable called "STOCKFISH_EXECUTABLE" pointing to the Stockfish executable')

        # make sure there is actually a file
        # stockfish_path = os.environ['STOCKFISH_EXECUTABLE']
        # print(stockfish_path)
        # if not os.path.exists(stockfish_path):
        #     raise ValueError('No stockfish executable found at "{}"'.format(stockfish_path))

        # initialize the stockfish engine
        self.engine = chess.engine.SimpleEngine.popen_uci('./stockfish', setpgrp=True)

    def handle_game_start(self, color: Color, board: chess.Board, opponent_name: str):
        self.board = board
        self.color = color

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        self.my_piece_captured_square = capture_square
        if captured_my_piece:
            self.board.remove_piece_at(capture_square)

    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> \
            Optional[Square]:
        if self.my_piece_captured_square:
            return self.my_piece_captured_square

        future_move = self.choose_move(move_actions, seconds_left)
        if future_move is not None and self.board.piece_at(future_move.to_square) is not None:
            return future_move.to_square

        own_squares = set(self.board.piece_map().keys())
        sense_actions = [action for action in sense_actions if action not in own_squares]
        return random.choice(sense_actions)

    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):
        for square, piece in sense_result:
            self.board.set_piece_at(square, piece)

    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        enemy_king_square = self.board.king(not self.color)
        if enemy_king_square:
            enemy_king_attackers = self.board.attackers(self.color, enemy_king_square)
            if enemy_king_attackers:
                attacker_square = enemy_king_attackers.pop()
                return chess.Move(attacker_square, enemy_king_square)

        try:
            self.board.turn = self.color
            self.board.clear_stack()
            result = self.engine.play(self.board, chess.engine.Limit(time=0.5))
            return result.move
        except chess.engine.EngineTerminatedError:
            print('Stockfish Engine died')
        except chess.engine.EngineError:
            print('Stockfish Engine bad state at "{}"'.format(self.board.fen()))

        return None

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):
        if taken_move is not None:
            self.board.push(taken_move)

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        try:
            self.engine.quit()
        except chess.engine.EngineTerminatedError:
            pass
