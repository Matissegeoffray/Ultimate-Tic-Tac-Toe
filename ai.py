import math


# ---------------------------------------------------------------------------
# Heuristique
# ---------------------------------------------------------------------------

def _score_lines(vals, player):
    """
    Pour une grille 3x3 (vals[r][c]), calcule un score basé sur les lignes.
    Récompense les alignements à 2 (sans blocage), pénalise ceux de l'adversaire.
    """
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

        if o_count == 0:           # ligne non bloquée par l'adversaire
            if p_count == 2:
                score += 3         # menace immédiate
            elif p_count == 1:
                score += 1         # développement
        if p_count == 0:           # ligne non bloquée par le joueur
            if o_count == 2:
                score -= 3
            elif o_count == 1:
                score -= 1
    return score


def heuristic(game, ai_player):
    """
    Évalue la position du point de vue de ai_player.
    Retourne un entier : positif = bon pour l'IA, négatif = mauvais.
    """
    opponent = 3 - ai_player
    score = 0

    # 1. Sous-plateaux gagnés (objectif principal)
    score += game.count_local_wins(ai_player) * 10
    score -= game.count_local_wins(opponent)  * 10

    # 2. Sous-plateau central du plateau global (pivot stratégique)
    center_winner = game.local_winners[1][1]
    if center_winner == ai_player:
        score += 5
    elif center_winner == opponent:
        score -= 5

    # 3. Analyse de chaque sous-plateau non terminé
    for br in range(3):
        for bc in range(3):
            if game.local_winners[br][bc] != 0:
                continue

            vals = game.get_local_values(br, bc)

            # Menaces à 2 et développement à 1
            score += _score_lines(vals, ai_player)

            # Case centrale du sous-plateau
            center = vals[1][1]
            if center == ai_player:
                score += 1
            elif center == opponent:
                score -= 1

    # 4. Liberté du prochain joueur
    # Si le joueur courant (qui vient de jouer) a forcé l'adversaire dans un
    # sous-plateau terminé, l'adversaire joue librement (mauvais pour l'IA).
    # La liberté de choix (active_board=None) est un avantage pour le joueur courant.
    if game.active_board is None:
        if game.current_player == ai_player:
            score += 2   # l'IA joue librement = bon pour elle
        else:
            score -= 2   # l'adversaire joue librement = mauvais pour l'IA

    return score


# ---------------------------------------------------------------------------
# Minimax avec élagage Alpha-Beta
# ---------------------------------------------------------------------------

def minimax(game, depth, alpha, beta, maximizing, ai_player):
    """
    Minimax avec élagage Alpha-Beta.
    maximizing=True  → c'est le tour de l'IA (on maximise).
    maximizing=False → c'est le tour de l'adversaire (on minimise).
    """
    if game.is_game_over():
        winner = game.global_winner
        if winner == ai_player:
            return 10000
        elif winner == 0:
            # Fin par remplissage : on compte les morpions gagnés
            ai_wins  = game.count_local_wins(ai_player)
            opp_wins = game.count_local_wins(3 - ai_player)
            return (ai_wins - opp_wins) * 100
        else:
            return -10000

    if depth == 0:
        return heuristic(game, ai_player)

    moves = game.get_valid_moves()

    if maximizing:
        best = -math.inf
        for row, col in moves:
            child = game.copy()
            child.make_move(row, col)
            val = minimax(child, depth - 1, alpha, beta, False, ai_player)
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break   # coupure bêta
        return best
    else:
        best = math.inf
        for row, col in moves:
            child = game.copy()
            child.make_move(row, col)
            val = minimax(child, depth - 1, alpha, beta, True, ai_player)
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha:
                break   # coupure alpha
        return best


def get_best_move(game, depth=3):
    """
    Retourne le meilleur coup (row, col) pour le joueur courant.
    depth : profondeur de recherche (3 = bon compromis vitesse/qualité).
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
        val = minimax(child, depth - 1, alpha, beta, False, ai_player)
        if val > best_val:
            best_val  = val
            best_move = (row, col)
        alpha = max(alpha, best_val)

    return best_move
