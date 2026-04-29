import math
import time


# ---------------------------------------------------------------------------
# Poids par défaut de l'heuristique
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS = {
    "local_win":      29,  # morpion gagné
    "global_center":   5,  # morpion central du plateau global
    "two_in_row":      7,  # 2 pièces alignées sans blocage dans un morpion
    "one_in_row":      2,  # 1 pièce en développement
    "local_center":    2,  # case centrale d'un morpion
    "freedom":         2,  # liberté de choix (active_board=None)
}


# ---------------------------------------------------------------------------
# Heuristique
# ---------------------------------------------------------------------------

def _score_lines(vals, player, w_two, w_one):
    opponent = 3 - player
    score = 0
    lines = [
        [(0,0),(0,1),(0,2)],
        [(1,0),(1,1),(1,2)],
        [(2,0),(2,1),(2,2)],
        [(0,0),(1,0),(2,0)],
        [(0,1),(1,1),(2,1)],
        [(0,2),(1,2),(2,2)],
        [(0,0),(1,1),(2,2)],
        [(0,2),(1,1),(2,0)],
    ]
    for line in lines:
        cells = [vals[r][c] for r, c in line]
        p_count = cells.count(player)
        o_count = cells.count(opponent)

        if o_count == 0:
            if p_count == 2:
                score += w_two
            elif p_count == 1:
                score += w_one
        if p_count == 0:
            if o_count == 2:
                score -= w_two
            elif o_count == 1:
                score -= w_one
    return score


def heuristic(game, ai_player, weights=None):
    """
    Évalue la position du point de vue de ai_player.
    weights : dict de poids (utilise DEFAULT_WEIGHTS si None).
    """
    w = weights if weights is not None else DEFAULT_WEIGHTS
    opponent = 3 - ai_player
    score = 0

    # 1. Morpions gagnés
    score += game.count_local_wins(ai_player) * w["local_win"]
    score -= game.count_local_wins(opponent)  * w["local_win"]

    # 2. Morpion central du plateau global
    center_winner = game.local_winners[1][1]
    if center_winner == ai_player:
        score += w["global_center"]
    elif center_winner == opponent:
        score -= w["global_center"]

    # 3. Analyse de chaque sous-plateau non terminé
    for br in range(3):
        for bc in range(3):
            if game.local_winners[br][bc] != 0:
                continue
            vals = game.get_local_values(br, bc)
            score += _score_lines(vals, ai_player, w["two_in_row"], w["one_in_row"])
            center = vals[1][1]
            if center == ai_player:
                score += w["local_center"]
            elif center == opponent:
                score -= w["local_center"]

    # 4. Liberté de choix
    if game.active_board is None:
        if game.current_player == ai_player:
            score += w["freedom"]
        else:
            score -= w["freedom"]

    return score


# ---------------------------------------------------------------------------
# Minimax avec élagage Alpha-Beta
# ---------------------------------------------------------------------------

def minimax(game, depth, alpha, beta, maximizing, ai_player, weights=None):
    if game.is_game_over():
        winner = game.global_winner
        if winner == ai_player:
            return 10000
        elif winner == 0:
            ai_wins  = game.count_local_wins(ai_player)
            opp_wins = game.count_local_wins(3 - ai_player)
            return (ai_wins - opp_wins) * 100
        else:
            return -10000

    if depth == 0:
        return heuristic(game, ai_player, weights)

    moves = game.get_valid_moves()

    if maximizing:
        best = -math.inf
        for row, col in moves:
            child = game.copy()
            child.make_move(row, col)
            val = minimax(child, depth - 1, alpha, beta, False, ai_player, weights)
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = math.inf
        for row, col in moves:
            child = game.copy()
            child.make_move(row, col)
            val = minimax(child, depth - 1, alpha, beta, True, ai_player, weights)
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best


def get_best_move(game, depth=3, weights=None):
    """
    Retourne le meilleur coup (row, col) pour le joueur courant.
    weights : poids de l'heuristique (DEFAULT_WEIGHTS si None).
    """
    ai_player = game.current_player
    moves = game.get_valid_moves()

    if len(moves) == 1:
        return moves[0]

    best_val  = -math.inf
    best_move = moves[0]
    alpha     = -math.inf
    beta      =  math.inf

    for row, col in moves:
        child = game.copy()
        child.make_move(row, col)
        val = minimax(child, depth - 1, alpha, beta, False, ai_player, weights)
        if val > best_val:
            best_val  = val
            best_move = (row, col)
        alpha = max(alpha, best_val)

    return best_move


def get_best_move_timed(game, time_limit=5.0, weights=None):
    """
    Iterative deepening : explore depth=1, 2, 3... jusqu'à la limite de temps.
    Retourne (meilleur_coup, profondeur_atteinte).
    """
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
        alpha = -math.inf
        beta = math.inf

        for row, col in moves:
            child = game.copy()
            child.make_move(row, col)
            val = minimax(child, depth - 1, alpha, beta, False, ai_player, weights)
            if val > best_val:
                best_val = val
                candidate = (row, col)
            alpha = max(alpha, best_val)

        best_move = candidate
        best_depth = depth

        elapsed_this_depth = time.time() - t0
        remaining = time_limit - (time.time() - start)

        # Si la profondeur suivante dépasserait probablement le temps restant, on s'arrête
        if remaining < elapsed_this_depth * 3:
            break

    return best_move, best_depth
