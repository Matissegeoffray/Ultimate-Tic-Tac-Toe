from game import UltimateTTT
from display import print_board
from ai import get_best_move

AI_DEPTH = 3  # profondeur Minimax (augmenter pour une IA plus forte, mais plus lente)


def ask_choice(prompt, valid_options):
    while True:
        answer = input(prompt).strip()
        if answer in valid_options:
            return answer
        print(f"  Répondez avec : {' / '.join(valid_options)}")


def get_player_move(game):
    """Demande et valide le coup du joueur humain."""
    valid_moves = set(game.get_valid_moves())
    while True:
        try:
            raw = input("  Votre coup (colonne ligne, ex: 5 3) : ").strip().split()
            if len(raw) != 2:
                print("  Entrez deux nombres séparés par un espace.")
                continue
            col, row = int(raw[0]) - 1, int(raw[1]) - 1
            if not (0 <= row <= 8 and 0 <= col <= 8):
                print("  Colonne et ligne doivent être entre 1 et 9.")
                continue
            if (row, col) not in valid_moves:
                pretty = [(c + 1, r + 1) for r, c in sorted(valid_moves)]
                print(f"  Coup invalide. Cases autorisées (col, ligne) : {pretty}")
                continue
            return row, col
        except ValueError:
            print("  Entrez deux nombres entiers.")


def play_game():
    game = UltimateTTT()

    print("\n" + "=" * 40)
    print("     ULTIMATE TIC TAC TOE")
    print("=" * 40)
    print("\nQui commence ?")
    print("  [1] Vous (X — premier joueur)")
    print("  [2] L'IA (X — premier joueur)")
    choice = ask_choice("  Choix : ", ["1", "2"])

    human_player = 1 if choice == "1" else 2
    symbol = "X" if human_player == 1 else "O"
    print(f"\n  Vous jouez {symbol}.\n")

    print_board(game)

    while not game.is_game_over():
        current_symbol = "X" if game.current_player == 1 else "O"

        if game.current_player == human_player:
            print(f"--- Votre tour ({current_symbol}) ---")
            row, col = get_player_move(game)
            print(f"  → Vous jouez : colonne {col + 1}, ligne {row + 1}")
        else:
            print(f"--- Tour de l'IA ({current_symbol}) ---")
            print("  L'IA réfléchit...", end="", flush=True)
            row, col = get_best_move(game, depth=AI_DEPTH)
            print(f"\r  → L'IA joue   : colonne {col + 1}, ligne {row + 1}")

        game.make_move(row, col)
        print_board(game)

    _announce_result(game, human_player)


def _announce_result(game, human_player):
    print("=" * 40)
    if game.global_winner != 0:
        if game.global_winner == human_player:
            print("  Félicitations, vous avez gagné !")
        else:
            print("  L'IA a gagné. Bonne chance la prochaine fois !")
    else:
        x_wins = game.count_local_wins(1)
        o_wins = game.count_local_wins(2)
        print(f"  Grille complète — X: {x_wins} morpions  /  O: {o_wins} morpions")
        if x_wins == o_wins:
            print("  Égalité parfaite !")
        else:
            winner_player = 1 if x_wins > o_wins else 2
            who = "Vous gagnez" if winner_player == human_player else "L'IA gagne"
            print(f"  {who} par majorité de morpions !")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    while True:
        play_game()
        again = ask_choice("Rejouer ? [o/n] : ", ["o", "n"])
        if again == "n":
            print("À bientôt !")
            break
