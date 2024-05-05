import chess

def get_piece_and_square(obs):
    obs_arr = obs.split(":")

    square = chess.parse_square(obs_arr[0])
    
    if obs_arr[1] == '?':
        piece = None
    else:
        piece = obs_arr[1]

    return piece, square


def get_potential_states(observations, states):
    potential_states=[]
    
    for state in states:
        board = chess.Board(state)
        skip_state = False

        for obs in observations:
            piece, square = get_piece_and_square(obs)

            state_piece = board.piece_at(square)

            if state_piece is None:    
                if piece is not None:
                    skip_state = True
            elif(state_piece.symbol()!=piece):
                skip_state = True
                # continue

        if skip_state == False:
            potential_states.append(state)
        
    return sorted(potential_states)


N_string = input()
N = int(N_string)
states=[]

for x in range(N):
    state = input()
    states.append(state)

window_observed = input()
observation_arr = window_observed.split(";")

potential_states = get_potential_states(observation_arr, states)

for state in potential_states:
    print(state)





