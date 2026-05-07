# ============================================================
# ULTIMATE TIC TAC TOE — Version standalone Google Colab v2
# Optimisations appliquées :
#   [1] fast_clone()         — remplace copy.deepcopy (5-10× plus rapide)
#   [2] Move ordering        — centre > coins > bords (meilleurs coupes alpha-beta)
#   [3] Hard-limit minimax   — _Timeout levée à l'intérieur de la récursion
#   [4] Heuristique asymét.  — défense 2× plus lourde, malus position dangereuse
# Usage : copier ce fichier dans Colab puis exécuter la cellule
# ============================================================

import math
import time

AI_TIME_LIMIT = 9.5  # secondes max par coup (marge de 0.5s sous la limite de 10s)

# [OPTIM 4] Poids asymétriques : two_in_row_def > two_in_row_atk
DEFAULT_WEIGHTS = {
    "local_win":           29,
    "global_center":        5,
    "two_in_row_atk":       7,   # attaque : 2 pions propres alignés
    "two_in_row_def":      14,   # défense : 2 pions adverses — 2× plus fort
    "one_in_row":           2,
    "local_center":         2,
    "freedom":              2,
    "center_gift_malus":    4,   # malus si l'adversaire est envoyé au centre global
    "free_move_malus":      3,   # malus si l'adversaire a le choix libre
}


# ============================================================
# MOTEUR DE JEU
# ============================================================

class UltimateTTT:
    LINES = [
        [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],
        [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],
        [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)],
    ]

    def __init__(self):
        self.board = [[0] * 9 for _ in range(9)]
        self.local_winners = [[0] * 3 for _ in range(3)]
        self.active_board = None
        self.current_player = 1
        self.global_winner = 0

    def get_local_values(self, br, bc):
        return [[self.board[br*3+r][bc*3+c] for c in range(3)] for r in range(3)]

    def get_valid_moves(self):
        if self.active_board is not None:
            br, bc = self.active_board
            moves = self._empty_cells_in(br, bc)
            if moves:
                return moves
        moves = []
        for br in range(3):
            for bc in range(3):
                if self.local_winners[br][bc] == 0:
                    moves.extend(self._empty_cells_in(br, bc))
        return moves

    def _empty_cells_in(self, br, bc):
        return [
            (br*3+r, bc*3+c)
            for r in range(3) for c in range(3)
            if self.board[br*3+r][bc*3+c] == 0
        ]

    def make_move(self, row, col):
        self.board[row][col] = self.current_player
        br, bc = row // 3, col // 3
        self._update_local_winner(br, bc)
        self._update_global_winner()
        next_br, next_bc = row % 3, col % 3
        self.active_board = None if self.local_winners[next_br][next_bc] != 0 else (next_br, next_bc)
        self.current_player = 3 - self.current_player

    def _update_local_winner(self, br, bc):
        vals = self.get_local_values(br, bc)
        for line in self.LINES:
            cells = [vals[r][c] for r, c in line]
            if cells[0] != 0 and cells[0] == cells[1] == cells[2]:
                self.local_winners[br][bc] = cells[0]
                return
        if all(vals[r][c] != 0 for r in range(3) for c in range(3)):
            self.local_winners[br][bc] = 3

    def _update_global_winner(self):
        w = self.local_winners
        for line in self.LINES:
            vals = [w[r][c] for r, c in line]
            if vals[0] in (1, 2) and vals[0] == vals[1] == vals[2]:
                self.global_winner = vals[0]
                return

    def is_game_over(self):
        if self.global_winner != 0:
            return True
        return all(self.local_winners[br][bc] != 0 for br in range(3) for bc in range(3))

    def count_local_wins(self, player):
        return sum(1 for br in range(3) for bc in range(3) if self.local_winners[br][bc] == player)

    # [OPTIM 1] Copie manuelle par compréhension de listes — remplace copy.deepcopy
    def fast_clone(self):
        clone = UltimateTTT.__new__(UltimateTTT)
        clone.board = [row[:] for row in self.board]
        clone.local_winners = [row[:] for row in self.local_winners]
        clone.active_board = self.active_board
        clone.current_player = self.current_player
        clone.global_winner = self.global_winner
        return clone


# ============================================================
# AFFICHAGE
# ============================================================

SYMBOLS = {0: ".", 1: "X", 2: "O"}

def print_board(game):
    print()
    print("      ", end="")
    for col in range(9):
        if col in (3, 6):
            print("  ", end="")
        print(f"{col+1} ", end="")
    print()

    for row in range(9):
        if row in (3, 6):
            print("    " + "-" * 29)
        print(f"  {row+1} ", end="")
        for col in range(9):
            if col in (3, 6):
                print(" |", end="")
            val = game.board[row][col]
            br, bc = row // 3, col // 3
            winner = game.local_winners[br][bc]
            if winner in (1, 2):
                sym = SYMBOLS[winner].lower()
            elif winner == 3:
                sym = "="
            else:
                sym = SYMBOLS[val]
            print(f" {sym}", end="")
        print()

    print()
    if not game.is_game_over():
        if game.active_board is None:
            print("  Sous-plateau : LIBRE")
        else:
            br, bc = game.active_board
            print(f"  Sous-plateau imposé : lignes {br*3+1}-{br*3+3}, colonnes {bc*3+1}-{bc*3+3}")
    print(f"  Morpions — X: {game.count_local_wins(1)}  O: {game.count_local_wins(2)}")
    print()


# ============================================================
# IA — MINIMAX + ALPHA-BETA + HEURISTIQUE OPTIMISÉE
# ============================================================

# [OPTIM 2] Clé de tri : centre local (0) > coins (1) > bords (2)
def _move_order_key(move):
    r, c = move[0] % 3, move[1] % 3
    if r == 1 and c == 1:
        return 0
    if r in (0, 2) and c in (0, 2):
        return 1
    return 2


# [OPTIM 3] Exception pour couper la récursion instantanément dès le timeout
class _Timeout(Exception):
    pass


# [OPTIM 4] Scores asymétriques : w_def > w_atk pour prioriser la défense
def _score_lines(vals, player, w_atk, w_def, w_one):
    opponent = 3 - player
    score = 0
    lines = [
        [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],
        [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],
        [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)],
    ]
    for line in lines:
        cells = [vals[r][c] for r, c in line]
        p = cells.count(player)
        o = cells.count(opponent)
        if o == 0:
            if p == 2:
                score += w_atk        # attaque : poids offensif standard
            elif p == 1:
                score += w_one
        if p == 0:
            if o == 2:
                score -= w_def        # défense : poids renforcé (asymétrie)
            elif o == 1:
                score -= w_one
    return score


def heuristic(game, ai_player, weights=None):
    w = weights if weights is not None else DEFAULT_WEIGHTS
    opponent = 3 - ai_player
    score = 0
    score += game.count_local_wins(ai_player) * w["local_win"]
    score -= game.count_local_wins(opponent)  * w["local_win"]
    center = game.local_winners[1][1]
    if center == ai_player:
        score += w["global_center"]
    elif center == opponent:
        score -= w["global_center"]
    for br in range(3):
        for bc in range(3):
            if game.local_winners[br][bc] != 0:
                continue
            vals = game.get_local_values(br, bc)
            # [OPTIM 4] Passe w_atk et w_def séparément
            score += _score_lines(vals, ai_player,
                                  w["two_in_row_atk"], w["two_in_row_def"],
                                  w["one_in_row"])
            c = vals[1][1]
            if c == ai_player:
                score += w["local_center"]
            elif c == opponent:
                score -= w["local_center"]
    # [OPTIM 4] Malus si l'adversaire a liberté de jeu ou est envoyé au centre global
    if game.active_board is None:
        if game.current_player == opponent:
            score -= w["free_move_malus"]   # l'adversaire choisit librement son sous-plateau
        else:
            score += w["freedom"]
    elif game.active_board == (1, 1) and game.current_player == opponent:
        score -= w["center_gift_malus"]     # on envoie l'adversaire sur le centre global
    return score


def minimax(game, depth, alpha, beta, maximizing, ai_player, weights, deadline):
    # [OPTIM 3] Vérification du temps au tout début de chaque appel récursif
    if time.time() >= deadline:
        raise _Timeout()

    if game.is_game_over():
        w = game.global_winner
        if w == ai_player:
            return 10000
        elif w == 0:
            return (game.count_local_wins(ai_player) - game.count_local_wins(3 - ai_player)) * 100
        else:
            return -10000
    if depth == 0:
        return heuristic(game, ai_player, weights)

    # [OPTIM 2] Tri des coups : centre local d'abord pour maximiser les coupes
    moves = sorted(game.get_valid_moves(), key=_move_order_key)

    if maximizing:
        best = -math.inf
        for row, col in moves:
            child = game.fast_clone()   # [OPTIM 1] fast_clone au lieu de deepcopy
            child.make_move(row, col)
            best = max(best, minimax(child, depth-1, alpha, beta, False, ai_player, weights, deadline))
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = math.inf
        for row, col in moves:
            child = game.fast_clone()   # [OPTIM 1] fast_clone au lieu de deepcopy
            child.make_move(row, col)
            best = min(best, minimax(child, depth-1, alpha, beta, True, ai_player, weights, deadline))
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best


def get_best_move_timed(game, time_limit=AI_TIME_LIMIT, weights=None):
    """Iterative deepening avec hard-limit strict géré par _Timeout."""
    ai_player = game.current_player
    # [OPTIM 2] Move ordering dès la racine
    moves = sorted(game.get_valid_moves(), key=_move_order_key)

    if len(moves) == 1:
        return moves[0], 1

    w = weights if weights is not None else DEFAULT_WEIGHTS
    best_move = moves[0]
    best_depth = 0
    deadline = time.time() + time_limit

    for depth in range(1, 15):
        candidate = moves[0]
        best_val = -math.inf
        alpha, beta = -math.inf, math.inf
        try:
            for row, col in moves:
                child = game.fast_clone()   # [OPTIM 1]
                child.make_move(row, col)
                val = minimax(child, depth-1, alpha, beta, False, ai_player, w, deadline)
                if val > best_val:
                    best_val = val
                    candidate = (row, col)
                alpha = max(alpha, best_val)
            # Profondeur complète atteinte → on valide ce coup
            best_move = candidate
            best_depth = depth
        except _Timeout:
            # [OPTIM 3] Profondeur interrompue → on conserve le coup de la profondeur précédente
            break

        if time.time() >= deadline:
            break

    return best_move, best_depth


# ============================================================
# BOUCLE DE JEU
# ============================================================

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
                pretty = [(c+1, r+1) for r, c in sorted(valid_moves)]
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
    print("  [1] Vous (X)  [2] L'IA (X)")
    choice = ask_choice("  Choix : ", ["1", "2"])
    human_player = 1 if choice == "1" else 2
    print(f"\n  Vous jouez {'X' if human_player == 1 else 'O'}.\n")
    print_board(game)

    while not game.is_game_over():
        sym = "X" if game.current_player == 1 else "O"
        if game.current_player == human_player:
            print(f"--- Votre tour ({sym}) ---")
            row, col = get_player_move(game)
            print(f"  → Vous jouez : colonne {col+1}, ligne {row+1}")
        else:
            print(f"--- Tour de l'IA ({sym}) ---")
            print("  L'IA réfléchit...", end="", flush=True)
            t0 = time.time()
            (row, col), depth_reached = get_best_move_timed(game)
            elapsed = time.time() - t0
            print(f"\r  → L'IA joue   : colonne {col+1}, ligne {row+1}  (depth={depth_reached}, temps={elapsed:.2f}s)")
        game.make_move(row, col)
        print_board(game)

    print("=" * 40)
    if game.global_winner != 0:
        print("  Vous avez gagné !" if game.global_winner == human_player else "  L'IA a gagné !")
    else:
        x, o = game.count_local_wins(1), game.count_local_wins(2)
        print(f"  Grille complète — X: {x}  O: {o}")
        if x == o:
            print("  Égalité parfaite !")
        else:
            winner = 1 if x > o else 2
            print("  Vous gagnez par majorité !" if winner == human_player else "  L'IA gagne par majorité !")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    while True:
        play_game()
        if ask_choice("Rejouer ? [o/n] : ", ["o", "n"]) == "n":
            print("À bientôt !")
            break
