from game import UltimateTTT
from display import print_board
from ai import get_best_move, DEFAULT_WEIGHTS

AI_DEPTH = 3  # profondeur Minimax (augmenter pour une IA plus forte, mais plus lente)


def ask_choice(prompt, valid_options):
    while True:
        answer = input(prompt).strip()
        if answer in valid_options:
            return answer
        print(f"  Répondez avec : {' / '.join(valid_options)}")


def get_player_move(game):
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


# ------------------------------------------------------------------
# Mode joueur vs IA
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# Mode bataille IA vs IA
# ------------------------------------------------------------------

def _play_one_battle(depth_a, depth_b, a_starts, weights_a=None, weights_b=None):
    """
    Joue une partie IA-A vs IA-B.
    Retourne (gagnant, x_wins, o_wins) où gagnant = 'A', 'B' ou 'Nul'.
    Si a_starts : IA-A joue X (joueur 1), IA-B joue O (joueur 2).
    Sinon l'inverse.
    """
    game = UltimateTTT()
    player_a = 1 if a_starts else 2
    player_b = 2 if a_starts else 1

    while not game.is_game_over():
        if game.current_player == player_a:
            row, col = get_best_move(game, depth=depth_a, weights=weights_a)
        else:
            row, col = get_best_move(game, depth=depth_b, weights=weights_b)
        game.make_move(row, col)

    x_wins = game.count_local_wins(1)
    o_wins = game.count_local_wins(2)

    if game.global_winner == player_a:
        winner = "A"
    elif game.global_winner == player_b:
        winner = "B"
    elif game.global_winner == 0:
        a_count = x_wins if a_starts else o_wins
        b_count = o_wins if a_starts else x_wins
        winner = "A" if a_count > b_count else ("B" if b_count > a_count else "Nul")
    else:
        winner = "Nul"

    return winner, x_wins, o_wins


def _points(winner, is_fastest):
    """Calcule les points selon le barème du sujet."""
    if winner == "A":
        return (4 if is_fastest else 3, 0)
    elif winner == "B":
        return (0, 4 if is_fastest else 3)
    else:
        return (1 if is_fastest else 0, 1 if is_fastest else 0)


def _ask_weights(name):
    """Demande les poids pour une IA. Entrée vide = valeur par défaut."""
    print(f"\n  Poids de {name} (Entrée = garder la valeur par défaut) :")
    weights = dict(DEFAULT_WEIGHTS)
    labels = {
        "local_win":     f"  Morpion gagné          [{weights['local_win']}] : ",
        "global_center": f"  Morpion central global  [{weights['global_center']}] : ",
        "two_in_row":    f"  2 alignés sans blocage  [{weights['two_in_row']}] : ",
        "one_in_row":    f"  1 pièce en développ.   [{weights['one_in_row']}] : ",
        "local_center":  f"  Case centrale morpion   [{weights['local_center']}] : ",
        "freedom":       f"  Liberté de choix        [{weights['freedom']}] : ",
    }
    for key, prompt in labels.items():
        raw = input(prompt).strip()
        if raw:
            try:
                weights[key] = int(raw)
            except ValueError:
                pass
    return weights


def battle_mode():
    print("\n" + "=" * 40)
    print("     BATAILLE IA vs IA")
    print("=" * 40)

    print("\nProfondeur IA-A :", AI_DEPTH)
    try:
        depth_b = int(input("  Profondeur IA-B (ex: 2, 3, 4) : ").strip())
    except ValueError:
        depth_b = AI_DEPTH

    weights_a = _ask_weights("IA-A")
    weights_b = _ask_weights("IA-B")

    try:
        nb_combats = int(input("\n  Nombre de combats (1 combat = 2 parties) : ").strip())
    except ValueError:
        nb_combats = 3

    show_boards = ask_choice("  Afficher les grilles ? [o/n] : ", ["o", "n"]) == "o"

    print(f"\n  IA-A depth={AI_DEPTH}  vs  IA-B depth={depth_b}")
    print(f"  Poids A : {weights_a}")
    print(f"  Poids B : {weights_b}")
    print(f"  {nb_combats} combat(s) — {nb_combats * 2} partie(s) au total\n")

    total_pts_a = 0
    total_pts_b = 0
    wins_a = wins_b = draws = 0

    for combat in range(1, nb_combats + 1):
        print(f"--- Combat {combat}/{nb_combats} ---")

        import time

        # Partie 1 : A commence (joue X)
        t0 = time.time()
        w1, x1, o1 = _play_one_battle(AI_DEPTH, depth_b, a_starts=True, weights_a=weights_a, weights_b=weights_b)
        t1 = time.time() - t0

        pts_a1, pts_b1 = _points(w1, True)
        total_pts_a += pts_a1
        total_pts_b += pts_b1
        print(f"  Partie 1 (A=X) : {_result_str(w1, x1, o1)}  [{t1:.1f}s]  pts A={pts_a1} B={pts_b1}")

        if show_boards:
            _replay_and_show(AI_DEPTH, depth_b, a_starts=True, weights_a=weights_a, weights_b=weights_b)

        # Partie 2 : B commence (joue X)
        t0 = time.time()
        w2, x2, o2 = _play_one_battle(AI_DEPTH, depth_b, a_starts=False, weights_a=weights_a, weights_b=weights_b)
        t2 = time.time() - t0

        pts_a2, pts_b2 = _points(w2, True)
        total_pts_a += pts_a2
        total_pts_b += pts_b2
        print(f"  Partie 2 (B=X) : {_result_str(w2, x2, o2)}  [{t2:.1f}s]  pts A={pts_a2} B={pts_b2}")

        if show_boards:
            _replay_and_show(AI_DEPTH, depth_b, a_starts=False, weights_a=weights_a, weights_b=weights_b)

        # Stats de la partie
        for w in (w1, w2):
            if w == "A":
                wins_a += 1
            elif w == "B":
                wins_b += 1
            else:
                draws += 1

    print("\n" + "=" * 40)
    print("  RÉSULTATS FINAUX")
    print("=" * 40)
    print(f"  IA-A (depth={AI_DEPTH}) : {wins_a} victoires  {total_pts_a} pts")
    print(f"  IA-B (depth={depth_b})  : {wins_b} victoires  {total_pts_b} pts")
    print(f"  Nuls : {draws}")
    if total_pts_a > total_pts_b:
        print("  → IA-A remporte le tournoi !")
    elif total_pts_b > total_pts_a:
        print("  → IA-B remporte le tournoi !")
    else:
        print("  → Égalité parfaite !")
    print("=" * 40 + "\n")


def _result_str(winner, x_wins, o_wins):
    if winner in ("A", "B"):
        return f"Victoire {winner}"
    return f"Nul (X:{x_wins} O:{o_wins})"


def _replay_and_show(depth_a, depth_b, a_starts, weights_a=None, weights_b=None):
    game = UltimateTTT()
    player_a = 1 if a_starts else 2
    print_board(game)
    while not game.is_game_over():
        if game.current_player == player_a:
            row, col = get_best_move(game, depth=depth_a, weights=weights_a)
            print(f"  IA-A joue : col {col+1} ligne {row+1}")
        else:
            row, col = get_best_move(game, depth=depth_b, weights=weights_b)
            print(f"  IA-B joue : col {col+1} ligne {row+1}")
        game.make_move(row, col)
        print_board(game)


# ------------------------------------------------------------------
# Menu principal
# ------------------------------------------------------------------

if __name__ == "__main__":
    while True:
        print("\n" + "=" * 40)
        print("  [1] Jouer contre l'IA")
        print("  [2] Bataille IA vs IA")
        print("  [q] Quitter")
        choice = ask_choice("  Choix : ", ["1", "2", "q"])

        if choice == "1":
            play_game()
        elif choice == "2":
            battle_mode()
        else:
            print("À bientôt !")
            break
