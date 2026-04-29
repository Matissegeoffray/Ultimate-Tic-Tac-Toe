# ============================================================
# BATTLE COLAB — Mon IA vs IA du pote
# Usage : !python battle_colab.py
# ============================================================

import copy
import math
import time

# ============================================================
# CONSTANTES COMMUNES
# ============================================================

EMPTY    = 0
PLAYER_X = 1
PLAYER_O = 2
TIE      = 3

WIN_LINES = [
    [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],
    [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],
    [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)],
]


# ============================================================
# MON IA — Moteur de jeu
# ============================================================

class UltimateTTT:
    LINES = WIN_LINES

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

    def copy(self):
        return copy.deepcopy(self)


# MON IA — Heuristique + Minimax

MY_WEIGHTS = {
    "local_win":      29,
    "global_center":   5,
    "two_in_row":      7,
    "one_in_row":      2,
    "local_center":    2,
    "freedom":         2,
}

def _my_score_lines(vals, player, w_two, w_one):
    opponent = 3 - player
    score = 0
    for line in WIN_LINES:
        cells = [vals[r][c] for r, c in line]
        p = cells.count(player)
        o = cells.count(opponent)
        if o == 0:
            if p == 2: score += w_two
            elif p == 1: score += w_one
        if p == 0:
            if o == 2: score -= w_two
            elif o == 1: score -= w_one
    return score

def _my_heuristic(game, ai_player):
    w = MY_WEIGHTS
    opponent = 3 - ai_player
    score = 0
    score += game.count_local_wins(ai_player) * w["local_win"]
    score -= game.count_local_wins(opponent)  * w["local_win"]
    center = game.local_winners[1][1]
    if center == ai_player:   score += w["global_center"]
    elif center == opponent:  score -= w["global_center"]
    for br in range(3):
        for bc in range(3):
            if game.local_winners[br][bc] != 0:
                continue
            vals = game.get_local_values(br, bc)
            score += _my_score_lines(vals, ai_player, w["two_in_row"], w["one_in_row"])
            c = vals[1][1]
            if c == ai_player:   score += w["local_center"]
            elif c == opponent:  score -= w["local_center"]
    if game.active_board is None:
        score += w["freedom"] if game.current_player == ai_player else -w["freedom"]
    return score

def _my_minimax(game, depth, alpha, beta, maximizing, ai_player):
    if game.is_game_over():
        w = game.global_winner
        if w == ai_player:   return 10000
        elif w == 0:         return (game.count_local_wins(ai_player) - game.count_local_wins(3 - ai_player)) * 100
        else:                return -10000
    if depth == 0:
        return _my_heuristic(game, ai_player)
    moves = game.get_valid_moves()
    if maximizing:
        best = -math.inf
        for row, col in moves:
            child = game.copy()
            child.make_move(row, col)
            best = max(best, _my_minimax(child, depth-1, alpha, beta, False, ai_player))
            alpha = max(alpha, best)
            if beta <= alpha: break
        return best
    else:
        best = math.inf
        for row, col in moves:
            child = game.copy()
            child.make_move(row, col)
            best = min(best, _my_minimax(child, depth-1, alpha, beta, True, ai_player))
            beta = min(beta, best)
            if beta <= alpha: break
        return best

def my_get_best_move(game, time_limit=5.0):
    """Iterative deepening avec limite de temps."""
    ai_player = game.current_player
    moves = game.get_valid_moves()
    if len(moves) == 1:
        return moves[0], 1
    best_move = moves[0]
    best_depth = 0
    start = time.time()
    for depth in range(1, 15):
        t0 = time.time()
        candidate = moves[0]
        best_val = -math.inf
        alpha, beta = -math.inf, math.inf
        for row, col in moves:
            child = game.copy()
            child.make_move(row, col)
            val = _my_minimax(child, depth-1, alpha, beta, False, ai_player)
            if val > best_val:
                best_val = val
                candidate = (row, col)
            alpha = max(alpha, best_val)
        best_move = candidate
        best_depth = depth
        elapsed = time.time() - t0
        remaining = time_limit - (time.time() - start)
        if remaining < elapsed * 3:
            break
    return best_move, best_depth


# ============================================================
# IA DU POTE — Code original (renommé pour éviter les conflits)
# ============================================================

class F_TimeoutException(Exception):
    pass

class F_State:
    def __init__(self):
        self.board = [[EMPTY] * 9 for _ in range(9)]
        self.macro_board = [[EMPTY] * 3 for _ in range(3)]
        self.next_macro = None
        self.current_player = PLAYER_X

    def fast_clone(self):
        s = F_State()
        s.board = [r[:] for r in self.board]
        s.macro_board = [r[:] for r in self.macro_board]
        s.next_macro = self.next_macro
        s.current_player = self.current_player
        return s

    def get_valid_moves(self):
        moves = []
        if self.next_macro is not None and self.macro_board[self.next_macro[0]][self.next_macro[1]] == EMPTY:
            mr, mc = self.next_macro
            for r in range(mr*3, mr*3+3):
                for c in range(mc*3, mc*3+3):
                    if self.board[r][c] == EMPTY:
                        moves.append((r, c))
        else:
            for r in range(9):
                for c in range(9):
                    if self.macro_board[r//3][c//3] == EMPTY and self.board[r][c] == EMPTY:
                        moves.append((r, c))
        def move_score(move):
            lr, lc = move[0] % 3, move[1] % 3
            if lr == 1 and lc == 1: return 3
            if lr != 1 and lc != 1: return 2
            return 1
        moves.sort(key=move_score, reverse=True)
        return moves

    def check_win(self, grid, player):
        for line in WIN_LINES:
            if grid[line[0][0]][line[0][1]] == player and \
               grid[line[1][0]][line[1][1]] == player and \
               grid[line[2][0]][line[2][1]] == player:
                return True
        return False

    def make_move(self, r, c):
        self.board[r][c] = self.current_player
        mr, mc = r // 3, c // 3
        grid = [[self.board[mr*3+i][mc*3+j] for j in range(3)] for i in range(3)]
        if self.check_win(grid, self.current_player):
            self.macro_board[mr][mc] = self.current_player
        elif not any(EMPTY in row for row in grid):
            self.macro_board[mr][mc] = TIE
        next_mr, next_mc = r % 3, c % 3
        self.next_macro = None if self.macro_board[next_mr][next_mc] != EMPTY else (next_mr, next_mc)
        self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X

    def is_terminal(self):
        if self.check_win(self.macro_board, PLAYER_X): return PLAYER_X
        if self.check_win(self.macro_board, PLAYER_O): return PLAYER_O
        if not self.get_valid_moves(): return TIE
        return False

def f_evaluate(state, ai_player):
    opponent = PLAYER_X if ai_player == PLAYER_O else PLAYER_O
    score = 0
    for r in range(3):
        for c in range(3):
            val = state.macro_board[r][c]
            if val == ai_player:   score += 1000 + (500 if r==1 and c==1 else 0)
            elif val == opponent:  score -= 1000 + (500 if r==1 and c==1 else 0)
    for line in WIN_LINES:
        vals = [state.macro_board[r][c] for r, c in line]
        if vals.count(ai_player) == 2 and vals.count(EMPTY) == 1: score += 300
        elif vals.count(opponent) == 2 and vals.count(EMPTY) == 1: score -= 300
    for r in range(9):
        for c in range(9):
            if state.macro_board[r//3][c//3] == EMPTY:
                val = state.board[r][c]
                if val != EMPTY:
                    lr, lc = r % 3, c % 3
                    pts = 10 if lr==1 and lc==1 else (3 if lr!=1 and lc!=1 else 1)
                    score += pts if val == ai_player else -pts
    if state.next_macro is None:
        score += 200 if state.current_player == ai_player else -200
    return score

def f_minimax(state, depth, alpha, beta, maximizing, ai_player, start_time, time_limit):
    if time.time() - start_time > time_limit:
        raise F_TimeoutException()
    terminal = state.is_terminal()
    if terminal == ai_player:   return 100000 + depth, None
    elif terminal not in (False, TIE): return -100000 - depth, None
    elif terminal == TIE:       return 0, None
    elif depth == 0:            return f_evaluate(state, ai_player), None
    best_move = None
    if maximizing:
        max_eval = -math.inf
        for move in state.get_valid_moves():
            new_state = state.fast_clone()
            new_state.make_move(move[0], move[1])
            eval_score, _ = f_minimax(new_state, depth-1, alpha, beta, False, ai_player, start_time, time_limit)
            if eval_score > max_eval:
                max_eval, best_move = eval_score, move
            alpha = max(alpha, eval_score)
            if beta <= alpha: break
        return max_eval, best_move
    else:
        min_eval = math.inf
        for move in state.get_valid_moves():
            new_state = state.fast_clone()
            new_state.make_move(move[0], move[1])
            eval_score, _ = f_minimax(new_state, depth-1, alpha, beta, True, ai_player, start_time, time_limit)
            if eval_score < min_eval:
                min_eval, best_move = eval_score, move
            beta = min(beta, eval_score)
            if beta <= alpha: break
        return min_eval, best_move

def friend_get_best_move(state, ai_player, time_limit=4.8):
    start_time = time.time()
    best_move = None
    depth = 1
    try:
        while True:
            current_eval, current_move = f_minimax(state, depth, -math.inf, math.inf, True, ai_player, start_time, time_limit)
            best_move = current_move
            if abs(current_eval) > 50000: break
            depth += 1
    except F_TimeoutException:
        pass
    return best_move if best_move else state.get_valid_moves()[0], depth - 1


# ============================================================
# ADAPTATEUR : UltimateTTT → F_State
# ============================================================

def to_friend_state(game):
    """Convertit l'état maître UltimateTTT en F_State pour l'IA du pote."""
    s = F_State()
    s.board = [row[:] for row in game.board]
    s.macro_board = [row[:] for row in game.local_winners]  # 0/1/2/3 identiques
    s.next_macro = game.active_board
    s.current_player = game.current_player
    return s


# ============================================================
# BATAILLE
# ============================================================

def play_one(my_player, verbose=True):
    """
    Joue une partie.
    my_player : 1 (X) ou 2 (O) — le rôle de MON IA.
    Retourne 'moi', 'pote' ou 'nul'.
    """
    game = UltimateTTT()
    friend_player = 3 - my_player

    while not game.is_game_over():
        sym = "X" if game.current_player == 1 else "O"
        t0 = time.time()

        if game.current_player == my_player:
            (row, col), depth = my_get_best_move(game, time_limit=5.0)
            elapsed = time.time() - t0
            if verbose:
                print(f"  [MOI  {sym}] col={col+1} lig={row+1}  depth={depth}  ({elapsed:.2f}s)", flush=True)
        else:
            fstate = to_friend_state(game)
            move, f_depth = friend_get_best_move(fstate, friend_player, time_limit=4.8)
            row, col = move
            elapsed = time.time() - t0
            if verbose:
                print(f"  [POTE {sym}] col={col+1} lig={row+1}  depth={f_depth}  ({elapsed:.2f}s)", flush=True)

        game.make_move(row, col)

    if game.global_winner == my_player:
        return "moi"
    elif game.global_winner == friend_player:
        return "pote"
    else:
        my_count   = game.count_local_wins(my_player)
        pote_count = game.count_local_wins(friend_player)
        if my_count > pote_count:   return "moi"
        elif pote_count > my_count: return "pote"
        else:                       return "nul"


def battle(n_combats=3, verbose=True):
    """
    Lance n_combats combats (2 parties chacun : alternance qui commence).
    Barème : victoire=4pts, nul=1pt, défaite=0pt.
    """
    print("=" * 55)
    print("  BATAILLE : MON IA  vs  IA DU POTE")
    print("=" * 55)
    print(f"  {n_combats} combat(s) — {n_combats * 2} partie(s) au total\n")

    pts_moi = pts_pote = 0
    wins_moi = wins_pote = nuls = 0

    for combat in range(1, n_combats + 1):
        print(f"--- Combat {combat}/{n_combats} ---")

        # Partie 1 : MON IA joue X (commence)
        print("  Partie 1 — MON IA = X")
        t0 = time.time()
        r1 = play_one(my_player=1, verbose=verbose)
        t1 = time.time() - t0
        p1_moi  = 4 if r1 == "moi"  else (1 if r1 == "nul" else 0)
        p1_pote = 4 if r1 == "pote" else (1 if r1 == "nul" else 0)
        pts_moi  += p1_moi
        pts_pote += p1_pote
        print(f"  → Résultat : {r1.upper()}  [{t1:.1f}s]  pts moi={p1_moi} pote={p1_pote}")

        # Partie 2 : IA du pote joue X (commence)
        print("  Partie 2 — POTE = X")
        t0 = time.time()
        r2 = play_one(my_player=2, verbose=verbose)
        t2 = time.time() - t0
        p2_moi  = 4 if r2 == "moi"  else (1 if r2 == "nul" else 0)
        p2_pote = 4 if r2 == "pote" else (1 if r2 == "nul" else 0)
        pts_moi  += p2_moi
        pts_pote += p2_pote
        print(f"  → Résultat : {r2.upper()}  [{t2:.1f}s]  pts moi={p2_moi} pote={p2_pote}")

        for r in (r1, r2):
            if r == "moi":   wins_moi  += 1
            elif r == "pote": wins_pote += 1
            else:             nuls      += 1

        print()

    print("=" * 55)
    print("  RÉSULTATS FINAUX")
    print("=" * 55)
    print(f"  Mon IA   : {wins_moi} victoires  {pts_moi} pts")
    print(f"  IA pote  : {wins_pote} victoires  {pts_pote} pts")
    print(f"  Nuls     : {nuls}")
    if pts_moi > pts_pote:
        print("  → MON IA remporte le tournoi !")
    elif pts_pote > pts_moi:
        print("  → L'IA du pote remporte le tournoi !")
    else:
        print("  → Égalité parfaite !")
    print("=" * 55)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    try:
        n = int(input("Nombre de combats (1 combat = 2 parties) [défaut 3] : ").strip())
    except ValueError:
        n = 3

    try:
        v = input("Afficher les coups ? [o/n, défaut o] : ").strip().lower()
        verbose = v != "n"
    except Exception:
        verbose = True

    battle(n_combats=n, verbose=verbose)
