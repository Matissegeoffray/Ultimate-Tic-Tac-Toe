SYMBOLS = {0: ".", 1: "X", 2: "O"}
WINNER_SYMBOLS = {1: "X", 2: "O", 3: "="}


def print_board(game):
    """Affiche la grille 9x9 avec séparateurs de sous-plateaux."""
    print()

    # En-tête des colonnes
    print("      ", end="")
    for col in range(9):
        if col == 3 or col == 6:
            print("  ", end="")
        print(f"{col + 1} ", end="")
    print()

    for row in range(9):
        # Séparateur horizontal entre sous-plateaux
        if row == 3 or row == 6:
            print("    " + "-" * 29)

        print(f"  {row + 1} ", end="")

        for col in range(9):
            # Séparateur vertical entre sous-plateaux
            if col == 3 or col == 6:
                print(" |", end="")

            val = game.board[row][col]
            br, bc = row // 3, col // 3
            winner = game.local_winners[br][bc]

            # Sous-plateau terminé : gagnant en minuscule, nul = "="
            if winner in (1, 2):
                sym = WINNER_SYMBOLS[winner].lower()
            elif winner == 3:
                sym = "="
            else:
                sym = SYMBOLS[val]

            print(f" {sym}", end="")

        print()

    print()
    _print_status(game)


def _print_status(game):
    """Affiche le statut du sous-plateau actif et des morpions gagnés."""
    if not game.is_game_over():
        if game.active_board is None:
            print("  Sous-plateau : LIBRE (jouez n'importe où)")
        else:
            br, bc = game.active_board
            r1, r2 = br * 3 + 1, br * 3 + 3
            c1, c2 = bc * 3 + 1, bc * 3 + 3
            print(f"  Sous-plateau imposé : lignes {r1}-{r2}, colonnes {c1}-{c2}")

    # Résumé des morpions
    x_wins = game.count_local_wins(1)
    o_wins = game.count_local_wins(2)
    print(f"  Morpions — X: {x_wins}  O: {o_wins}")
    print()
