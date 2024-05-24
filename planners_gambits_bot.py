# Importing libraries
from reconchess import Player
import chess
import chess.engine
import random
from collections import Counter, defaultdict


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
        self.central_squares = []
        self.my_king_position = set()
        self.enemy_king_last_position = None
        self.possible_king_positions = defaultdict(int)
        self.opponent_captured_square = None
        

    def handle_game_start(self, color, board, opponent_name):
        # Handle initial game setup.
        self.color = color
        self.board = board
        self.opponent_name = opponent_name

        # Initialize the starting state with the known initial board
        if board.turn == color:
            self.possible_boards = {board.fen()}  #if my turn, possible boards is just the starting board
            self.central_squares = [chess.D5, chess.E5, chess.C5, chess.F5]
            self.my_king_position = chess.E1
            self.possible_king_positions = {chess.E8} 
            self.enemy_king_last_position = chess.E8
        else:
            self.possible_boards = {board.fen()}   #if my opponents turn, possible boards is all boards after my opponent's possible moves
            self.central_squares = [chess.D4, chess.E4, chess.C4, chess.F4]
            self.my_king_position = chess.E8
            self.possible_king_positions = {chess.E1} 
            self.enemy_king_last_position = chess.E8

    def handle_opponent_move_result(self, captured_my_piece, capture_square):
        # Update possible states based on opponent's capture result.
        new_possible_baords = set()
        self.my_piece_captured_square = capture_square
        if captured_my_piece:
            self.board.remove_piece_at(capture_square)
            for boardFEN in self.possible_boards:
                board = chess.Board(boardFEN)
                if board.piece_at(capture_square) is None or board.piece_at(capture_square).color != self.color:
                    continue
                else:
                    new_possible_baords.add(boardFEN)
            self.possible_boards = new_possible_baords
            expanded_new_possible_boards = self.generate_possible_board_for_all_possible_boards(new_possible_baords)
            self.possible_boards = expanded_new_possible_boards
        if self.color == chess.WHITE and self.board.fullmove_number != 1:
            self.not_first_turn = False
            expanded_new_possible_boards = self.generate_possible_board_for_all_possible_boards(self.possible_boards)
            self.possible_boards = expanded_new_possible_boards
        
        
        # print("Num of possible boards after enemy move: ", len(self.possible_boards))

        self.board.push(chess.Move.null())
        

    def trout_bot_sense(self, sense_actions, move_actions, seconds_left):
        # if our piece was just captured, sense where it was captured
        if self.my_piece_captured_square:
            square = self.my_piece_captured_square
            self.my_piece_captured_square = None
            # print("Sensing where I was just captured")
            return square
        
        # if its tsill the early moves sense near most probable first move squares in center
        if self.board.fullmove_number <2:
            square = random.choice(self.central_squares)
            if square in sense_actions:
                # print("Sensing one of the central squares ")
                return square
        
        # every third move sense where the opponent king could be
        if self.board.fullmove_number %3 ==0:
            # print("Sensing where opponent king might be located")
            return self.try_find_opponent_king()
            
        # every fifth move sense where possible attackers of my king are guessed to be
        if self.board.fullmove_number %4 ==0:
            attacking_square = self.sense_my_king_attackers()
            if attacking_square is not None:
                # print("Sensing where my king might be under attack")
                return attacking_square
        
        #if we captured an opponent piece sense where we just captured
        if self.opponent_captured_square is not None:
            square = self.opponent_captured_square
            self.opponent_captured_square = None
            # print("Sensing where I just captured an opponent")
            return square

        # if we might capture a piece when we move, sense where the capture will occur
        future_move = self.calculate_best_move(move_actions, seconds_left=seconds_left)
        # future_move = self.majority_voting(move_actions)
        self.future_move = future_move
        if future_move is not None and self.board.piece_at(future_move.to_square) is not None:
            self.future_move = future_move
            return future_move.to_square
        
        # Predict opponent's next move
        move_history = [move.uci() for move in self.board.move_stack]
        predicted_move = self.predict_opponent_moves(self.board, move_history)

        # Use predicted move to influence sensing
        if predicted_move and isinstance(predicted_move, chess.Move):
            predicted_square = predicted_move.to_square
            if predicted_square in sense_actions:
                # print("Sensing from opponents future move")
                return predicted_square
        
        # Assign weights to potential sense actions
        square_weights = {square: 1.0 for square in sense_actions}
        for square in sense_actions:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.color:
                square_weights[square] = 0.1  # Avoid sensing where our pieces are
        # print(square_weights)

        # Increase weights for central and high-value squares
        high_value_squares = [chess.E4, chess.D4, chess.E5, chess.D5, chess.F3, chess.F6, chess.C3, chess.C6]
        for square in high_value_squares:
            if square in square_weights:
                square_weights[square] *= 2.0
        # print(f'high value square:{square_weights}')

        # Select the square with the maximum weight
        chosen_square = max(square_weights, key=square_weights.get)
        # print(f'High value squares {chosen_square}') # debug print
        # print("Sensing chosen_square,", chosen_square)

        return chosen_square
    
    def choose_sense(self, sense_actions, move_actions, seconds_left):
        # Get valid sense actions
        valid_sense_actions = [
            action for action in sense_actions if not self.is_edge_square(action)
        ]

        choice = self.trout_bot_sense( sense_actions=valid_sense_actions, move_actions=move_actions, seconds_left=seconds_left)

        
        return choice

    def try_find_opponent_king(self):
        if self.enemy_king_last_position is not None:
            return self.enemy_king_last_position
        else:
            if len(self.possible_king_positions) >0:
                most_frequent_position = max(self.possible_king_positions,key=lambda key: self.possible_king_positions[key])
                return most_frequent_position
            
    def sense_my_king_attackers(self):
        king_position = self.board.king(self.color)
        color = not self.color
        if (self.board.attackers(square=king_position, color=color) is not None):
            attackers = self.board.attackers(square=king_position, color=color)
            if len(attackers) > 0:
                return random.choice(attackers.tolist())
        return None

    def handle_sense_result(self, sense_result):
        sensed_pieces = {square: piece for square, piece in sense_result}
        new_possible_boards = set()
        board_probabilities = defaultdict(float)

        # Place and remove pieces based on sense and update where we've last seen a king
        for square, piece in sense_result:
            if piece is not None:
                self.board.set_piece_at(square, piece)
                #update where we've last seen a king
                if piece.symbol() == "K" and self.color is not chess.WHITE:
                    self.enemy_king_last_position= square
                elif piece.symbol() == "k" and self.color is not chess.BLACK:
                    self.enemy_king_last_position= square
            else:
                if self.board.piece_at(square) is not None:
                    if self.board.piece_at(square).symbol()  == "K" and self.color is not chess.WHITE:
                        self.enemy_king_last_position= None
                    elif self.board.piece_at(square).symbol()  == "k" and self.color is not chess.BLACK:
                        self.enemy_king_last_position= None
                self.board.remove_piece_at(square)

        different_pices_at_position = []
        phantom_piece_at_position = []
        no_piece_at_position = [] 
        
        for boardFEN in self.possible_boards:
            board = chess.Board(boardFEN)
            valid = True
            for square, piece in sense_result:
                if piece is not None and board.piece_at(square) is not None:
                    if piece.symbol() != board.piece_at(square).symbol():
                        valid = False
                        different_pices_at_position.append(boardFEN)
                        break
                elif piece is None and board.piece_at(square) is not None:
                    valid = False
                    phantom_piece_at_position.append(boardFEN)
                    break
                elif piece is not None and board.piece_at(square) is None:
                    valid = False
                    no_piece_at_position.append(boardFEN)
                    break
            if valid:
                new_possible_boards.add(boardFEN)

        if len(new_possible_boards) == 0:
            # print("things have gone wrong")
            # print("Board FEN: ", self.board.fen())
            error = 1
            # print("Sense Result : ", sense_result)
        else:
            self.possible_boards = new_possible_boards

        
        # print("Num of possible boards after sensing: ", len(self.possible_boards))

        # Calculate likelihood of sense_result for each possible board with weights
        for fen in self.possible_boards:
            board = chess.Board(fen)
            likelihood = 1.0
            for square, piece in sensed_pieces.items():
                weight = self.get_square_weight(square, board)
                if board.piece_at(square) == piece:
                    likelihood *= (0.9 * weight)  # Higher probability if the piece matches, scaled by weight
                else:
                    likelihood *= (0.1 * weight)  # Lower probability if the piece doesn't match, scaled by weight

            # Update the probability of this board being the correct board
            board_probabilities[fen] = likelihood

         # Normalize probabilities
        total_probability = sum(board_probabilities.values())
        if total_probability > 0:
            for fen in board_probabilities:
                board_probabilities[fen] /= total_probability

        # Use a different filtering approach by keeping a proportion of the boards with the highest probabilities
        sorted_boards = sorted(board_probabilities.items(), key=lambda item: item[1], reverse=True)
        threshold_index = int(0.5 * len(sorted_boards))  # Keep the top 50% of the boards by probability

        new_possible_boards = set(fen for fen, prob in sorted_boards[:threshold_index]) 


        if len(new_possible_boards)>0 :
            self.possible_boards = new_possible_boards

        if self.future_move_board not in self.possible_boards:
            self.future_move = None

        # print("Num of possible boards after ruling out boards with low probability: ", len(self.possible_boards))

    def get_square_weight(self, square, board):
        if square in [chess.E4, chess.D4, chess.E5, chess.D5]: 
            return 1.5
        # Weights for squares near potential king positions
        for king_pos in self.possible_king_positions:
            if square in self.SQUARES_around(king_pos):
                return 1.2  # Higher weight for squares around potential king positions
        
        return 0.1
    
    def SQUARES_around(self, center):
        offsets = [-9, -8, -7, -1, 1, 7, 8, 9]
        return [center + offset for offset in offsets if self.is_valid_square(center + offset)]
    
    def is_valid_square(self, square):
        return 0 <= square <= 63
    
    def update_possible_king_positions(self, last_sense_result):
        updated_positions = set()
        for pos in self.possible_king_positions:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    new_square = pos + i + 8 * j
                    if self.is_valid_square(new_square):
                        updated_positions.add(new_square)
        self.possible_king_positions = updated_positions

    def can_capture_lead_to_check(self, target_square, board): # consistently checking whether the board is a checkmate or can lead to the capture of the opponent's king
        simulation_board = board.copy()
        simulation_board.remove_piece_at(target_square)
        for move in simulation_board.legal_moves:
            simulation_board.push(move)
            if simulation_board.is_check():
                simulation_board.pop()
                return True
            simulation_board.pop()
        return False

    def update_probabilities(self, move_history):
        for move in move_history:
            # Update board probabilities based on the move history
            pass

    def predict_opponent_moves(self, board, move_history):
        # Pattern recognition based on common strategies
        if 'kingside_castle' in move_history:
            if self.check_kingside_attack_setup(board):
                # Return a valid UCI move for preparing for defense or countering
                # return self.simple_move_predictor(board, self.analyze_position(board))
                return chess.Move.from_uci('e1g1')

        # Analyze the current position and predict the move based on common chess principles
        current_position_features = self.analyze_position(board)
        predicted_move_uci = self.simple_move_predictor(board, current_position_features)

        # Convert the predicted move to a chess.Move object
        predicted_move = chess.Move.from_uci(predicted_move_uci)

        return predicted_move
    
    def check_kingside_attack_setup(self, board):
    # Check for pieces positioning that commonly indicate a kingside attack
        if self.color == chess.WHITE:
            return board.piece_at(chess.F3) is not None  # Knight on F3 might indicate preparing for an attack
        else:
           return board.piece_at(chess.F6) is not None  # Knight on F3 might indicate preparing for an attack 
    #TODO: add the alternative piece based on which color we are playing

    def analyze_position(self, board):
        # Analyze board and return some features
        features = {'material_advantage': self.calculate_material_advantage(board)}
        return features
    
    def simple_move_predictor(self, board, features):
     # Predict move based on simple rules
        if features['material_advantage'] > 0:
            # If we have a material advantage, return a safe move (e.g., consolidate position)
            for move in board.legal_moves:
                if not board.gives_check(move) and not board.is_capture(move):
                    return move.uci()
        else:
            # If we don't have a material advantage, return an aggressive move (e.g., seek counterplay)
            for move in board.legal_moves:
                if board.gives_check(move) or board.is_capture(move):
                    return move.uci()
        return next(iter(board.legal_moves)).uci()

    def calculate_material_advantage(self, board):
        material_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0  # The king's material value is not typically counted
        }

        material_advantage = 0

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                value = material_values[piece.piece_type]
                if piece.color == self.color:
                    material_advantage += value
                else:
                    material_advantage -= value

        return material_advantage
 
    def get_score_from_move_analysis(self,board):
        try:
            info = self.engine.analyse(board, chess.engine.Limit(depth=20))
        except Exception as e:
            # print(e)
            return None
        return info["score"]

    def generate_move_for_board(self,board,seconds_left):
        if board.is_checkmate():
            move = list(board.legal_moves)[0]
        else:  # Safeguard against too low values
            try:
                move = self.engine.play(board, chess.engine.Limit(time=0.1)).move
            except Exception as e:
                # print(e)
                return  list(board.legal_moves)[0]

        return move
    
    def calculate_best_move(self,move_actions, seconds_left):
       
        highestBoardScore = None
        bestMove = None
        bestMoveBoard = None

        if not self.possible_boards:
            return random.choice(move_actions)

        
        for board in self.possible_boards:
            if(seconds_left<100):
                break

            possibleBoard = chess.Board(board)
            move = self.generate_move_for_board(possibleBoard, seconds_left)

            

            if move in move_actions:
                possibleBoard.push(move)
                boardScore = self.get_score_from_move_analysis(possibleBoard)
                if boardScore is None:
                    continue

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
       
        # print("Num of possible boards before choosing move: ", len(self.possible_boards))

        # TODO: find a better way to verify that the chosen best move is best move after sensing
        if self.future_move is not None and self.future_move in move_actions:   
            best_move = self.future_move
            return best_move

        # select move using majority voting
        # best_move = self.majority_voting(move_actions)

       
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
                
                if taken_move is None:
                    if requested_move in current_board.pseudo_legal_moves:
                        continue
                    else:
                       new_possible_boards.add(new_board.fen())
                else: 
                    # If the executed move is different from the requested move, rule out this board
                    if taken_move != requested_move:
                        if requested_move in current_board.pseudo_legal_moves:
                            continue

                    # Check if the capture outcome matches
                    if captured_opponent_piece:
                        # print("I did it I did it")
                        self.opponent_captured_square = capture_square
                    if captured_opponent_piece and current_board.is_capture(taken_move):
                        new_possible_boards.add(new_board.fen())
                    elif not captured_opponent_piece and not current_board.is_capture(taken_move):
                        new_possible_boards.add(new_board.fen())
            except Exception as e:
                # If an illegal move exception occurs, exclude this board
                continue

        # Update to only keep the states that are consistent with the move outcome
        if len(new_possible_boards)==0:
            # print("something has gone worng after making a move bih")
            error = 1
        else:
            self.possible_boards = new_possible_boards

        # expanded_new_possible_boards = self.generate_possible_board_for_all_possible_boards(new_possible_boards)
        # self.possible_boards = expanded_new_possible_boards
        # print("Num of possible boards after making move: ", len(self.possible_boards))
        
    def is_opponent_piece(self, move, board):
        from_square = move.from_square
        piece = board.piece_at(from_square)
        if piece.color== self.color:
            return False
        else:
            return True
    
    def add_possible_king_position_from_board(self,square):
        if square in self.possible_king_positions:
            self.possible_king_positions[square] += 1
        else:
            self.possible_king_positions[square] = 1

    def generate_possible_boards_from_board(self,boardFEN):
        board =  chess.Board(boardFEN)
        possible_moves = list(board.pseudo_legal_moves)
        possible_boards = set()

        for move in possible_moves:
            new_board = board.copy()
            new_board.push(move)
            possible_king_position = new_board.king(not self.color)
            if possible_king_position is not None:
                self.add_possible_king_position_from_board(possible_king_position)
            else:
                continue
                print("nop enemy king on this board I guess I ate them lol") #TODO: remove this board since it can't possibly be a board if we are still in game play
            possible_boards.add(new_board.fen())
        
        return possible_boards
    
    def generate_possible_board_for_all_possible_boards(self, boards):
        new_possible_boards = set()
        self.possible_king_positions = defaultdict(int)
        # print("generating new possible boards from ", len(boards))
        for board in boards:
            new_boards = self.generate_possible_boards_from_board(board) 
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