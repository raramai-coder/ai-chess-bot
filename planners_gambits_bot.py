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
        

    def handle_game_start(self, color, board, opponent_name):
        # Handle initial game setup.
        self.color = color
        self.board = board
        self.opponent_name = opponent_name

        # Set initial possible king position based on the agent's color
        self.possible_king_positions = {chess.E1 if color == chess.WHITE else chess.E8}  # This line

        # Initialize the starting state with the known initial board
        if board.turn == color:
            self.possible_boards = {board.fen()}  #if my turn, possible boards is just the starting board
            self.central_squares = [chess.D5, chess.E5, chess.C5, chess.F5]
        else:
            self.possible_boards = self.generate_possible_board_for_all_possible_boards(boards= {board.fen()})   #if my opponents turn, possible boards is all boards after my opponent's possible moves
            self.central_squares = [chess.D4, chess.E4, chess.C4, chess.F4]

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
        # future_move = self.majority_voting(move_actions)
        self.future_move = future_move
        if future_move is not None and self.board.piece_at(future_move.to_square) is not None:
            self.future_move = future_move
            return future_move.to_square
        
        if self.board.fullmove_number <2:
            square = random.choice(self.central_squares)
            if square in sense_actions:
                return square
            
        
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
        # print(f'high value squares:{square_weights}')

        # Select the square with the maximum weight
        chosen_square = max(square_weights, key=square_weights.get)
        print(f'High value squares {chosen_square}') # debug print

        return chosen_square
        # otherwise, just randomly choose a sense action, but don't sense on a square where our pieces are located
        # for square, piece in self.board.piece_map().items():
        #     if piece.color == self.color and square in sense_actions:
        #         sense_actions.remove(square)
        
        # return random.choice(sense_actions)
    
    def choose_sense(self, sense_actions, move_actions, seconds_left):
        # Get valid sense actions
        valid_sense_actions = [
            action for action in sense_actions if not self.is_edge_square(action)
        ]
        choice = self.trout_bot_sense( sense_actions=valid_sense_actions, move_actions=move_actions, seconds_left=seconds_left)
        # choice = random.choice(valid_sense_actions)
        return choice

    def handle_sense_result(self, sense_result):
        sensed_pieces = {square: piece for square, piece in sense_result}
        new_possible_boards = set()
        board_probabilities = defaultdict(float)

        # Place and remove pieces based on sense
        for square, piece in sense_result:
            if piece is not None:
                self.board.set_piece_at(square, piece)
            else:
               self.board.remove_piece_at(square) 
        
        for boardFEN in self.possible_boards:
            board = chess.Board(boardFEN)
            valid = True
            for square, piece in sense_result:
                if piece is not None and board.piece_at(square) is not None:
                    if piece.symbol() != board.piece_at(square).symbol():
                        valid = False
                        break
                elif piece is None and board.piece_at(square) is not None:
                    valid = False
                    break
                elif piece is not None and board.piece_at(square) is None:
                    valid = False
                    break
            if valid:
                new_possible_boards.add(boardFEN)

        if len(new_possible_boards) == 0:
            print("things have gone wrong")
            print("Board FEN: ", self.board.fen())
            # print("Possible FENs : ", self.possible_boards[:10])
            print("Sense Result : ", sense_result)


        self.possible_boards = new_possible_boards
        print("Num of possible boards after sensing: ", len(self.possible_boards))

        # Calculate likelihood of sense_result for each possible board with weights
        for fen in self.possible_boards:
            board = chess.Board(fen)
            likelihood = 1.0
            for square, piece in sensed_pieces.items():
                weight = self.get_square_weight(square,board)
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

        new_possible_boards = set()
        # Threshold to consider a board as a possible board
        probability_threshold = 0.1
        # probability_threshold = total_probability/len(board_probabilities)
        for fen, probability in board_probabilities.items():
            if probability > probability_threshold:
                new_possible_boards.add(fen)

        if len(new_possible_boards)>0:
            self.possible_boards = new_possible_boards

        if self.future_move_board not in self.possible_boards:
            self.future_move = None

        print("Num of possible boards after ruling out boards with low probability: ", len(self.possible_boards))

    def get_square_weight(self, square, board):
        if square in [chess.E4, chess.D4, chess.E5, chess.D5]: #TODO: make it the center squares
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
    # pattern recognition based on common strategies
        if 'kingside_castle' in move_history:
        # Opponent has castled kingside, might prepare for a kingside attack
            if self.check_kingside_attack_setup(board):
                return 'Prepare for kingside defense or counter in the center'

    # Analyze the current position and predict the move based on common chess principles
        current_position_features = self.analyze_position(board)
        predicted_move = self.simple_move_predictor(current_position_features)
        return predicted_move
    
    def check_kingside_attack_setup(self, board):
    # Check for pieces positioning that commonly indicate a kingside attack
        return board.piece_at(chess.F3) is not None  # Knight on F3 might indicate preparing for an attack
    #TODO: add the alternative piece based on which color we are playing

    def analyze_position(self, board):
        # Analyze board and return some features
        features = {}
        features['material_advantage'] = self.calculate_material_advantage(board)
        return features
    
    def simple_move_predictor(self, features):
    # Predict move based on simple rules
        if features['material_advantage'] > 0:
            return 'Consolidate position'
        else:
            return 'Seek counterplay'

    
    def get_score_from_move_analysis(self,board):
        info = self.engine.analyse(board, chess.engine.Limit(depth=20))
        return info["score"]

    def generate_move_for_board(self,board,seconds_left):
    
        # board.turn = self.color
        if board.is_checkmate():
            move = list(board.legal_moves)[0]
        else:
            # time_per_board = max(seconds_left / max(len(self.possible_boards), 1), 0.01)  # Safeguard against too low values
            # if time_per_board > 10:
            #     time_per_board = 0.1
            time_per_board = max(10 / max(len(self.possible_boards), 1), 0.5)  # Safeguard against too low values
            move = self.engine.play(board, chess.engine.Limit(time=0.1)).move
    
        return move
    
    def calculate_best_move(self,move_actions, seconds_left):
       
        highestBoardScore = None
        bestMove = None
        bestMoveBoard = None

        if not self.possible_boards:
            return random.choice(move_actions)

        count = 0
        for board in self.possible_boards:
            count +=1
            if count > 9:
                break

            possibleBoard = chess.Board(board)
            move = self.generate_move_for_board(possibleBoard, seconds_left)

            # if(seconds_left<10):
            #     break

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
                new_possible_boards.add(new_board.fen())
                continue

        # Update to only keep the states that are consistent with the move outcome
        if len(new_possible_boards)==0:
            print("somethinghas gone worng after making a move bih")

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