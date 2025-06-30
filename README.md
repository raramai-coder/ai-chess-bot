# Reconnaissance Blind Chess AI Bot

Welcome to the Reconnaissance Blind Chess Bot repository! This project focuses on developing an AI bot designed to play Reconnaissance Blind Chess, a variant of chess where players cannot see the opponent's pieces but can "reconnaissance" (query) the position of specific pieces.
The bot leverages Stockfish for move evaluation and employs a simple strategy to handle the uncertainties of RBC.

## Features

- **Stockfish Integration**: Utilizes the Stockfish chess engine to evaluate potential moves.
- **Basic Sensing Strategy**: Senses squares randomly, excluding edge squares to maximize information gain.
- **Move Selection via Majority Voting**: Chooses moves based on the most common best move across possible board states.
- **State Management**: Maintains a set of possible board states to account for the uncertainty in RBC.
- **RBC Adaptation**: Specifically designed to handle the unique rules of Reconnaissance Blind Chess.
- **Minimax with Heuristics**: Utilizes a minimax algorithm enhanced with custom heuristics for RBC.
- **Recon Strategy**: Implements intelligent querying strategies to maximize information gain.
- **Bot vs. Bot Competition**: Capable of competing against other chess bots in a tournament setting.

## Technologies Used

- **Python**: The primary programming language for bot development.
- **Python-Chess**: Adapted to manage RBC-specific game states.
- **Machine Learning Libraries**: For developing and optimizing reconnaissance strategies.
- **Reconchess Library**: For the specific RBC game rules and playing environment.
- **NumPy & Collections**: For efficient data handling and counting.

To get started with the RBC Bot, follow these steps:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/raramai-coder/ai-chess-bot.git
   cd ai-chess-bot
