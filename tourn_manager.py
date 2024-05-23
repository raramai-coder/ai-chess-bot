import random

from reconchess import play_local_game

# from my_agent import MyAgent  # Adjust import based on actual file structure

from random_bot import RandomBot  # Adjust import based on actual file structure

from trout_bot import TroutBot  # Adjust import based on actual file structure

from planners_gambits_bot import MyAgent





def play_tournament(agents, num_games=10):

    results = {agent.__name__: 0 for agent in agents}



    for i in range(num_games):

        random.shuffle(agents)

        white_agent = agents[0]

        black_agent = agents[1]



        print(f"Game {i + 1}: {white_agent.__name__} (white) vs {black_agent.__name__} (black)")



        winner_color, win_reason, game_history = play_local_game(white_agent(), black_agent())



        if winner_color is not None:

            if winner_color:

                results[white_agent.__name__] += 1

                winner_color, win_reason = winner_color, win_reason

                winner_name = white_agent.__name__

            else:

                results[black_agent.__name__] += 1

                winner_color, win_reason = winner_color, win_reason

                winner_name = black_agent.__name__



                print(f"Game {i+1} Winner: {winner_name}")

                print(f"Win Reason: {win_reason}")



        else:

            print(f"Game {i+1} ended in a draw or was incomplete")

    return results





if __name__ == "__main__":

    # agents = [TroutBot, RandomBot, MyAgent]  # List your agent classes here
    # agents = [TroutBot,  MyAgent]  # List your agent classes here
    agents = [RandomBot, MyAgent]  # List your agent classes here



    results = play_tournament(agents, num_games=10)

    for agent, score in results.items():

        print(f'{agent}: {score} wins')

