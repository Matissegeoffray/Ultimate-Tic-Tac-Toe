"""
Optimisation génétique des poids de l'heuristique.
Lance : python optimize.py
"""

import random
import time
from game import UltimateTTT
from ai import get_best_move, DEFAULT_WEIGHTS

# ---------------------------------------------------------------------------
# Paramètres de l'optimisation
# ---------------------------------------------------------------------------

DEPTH       = 3   # profondeur Minimax pendant l'optimisation
POP_SIZE    = 8   # individus par génération (pair recommandé)
GENERATIONS = 5   # nombre de générations
MATCHES     = 2   # parties par duel (1 en X + 1 en O)

# Plages de valeurs autorisées pour chaque poids
RANGES = {
    "local_win":      (5,  30),
    "global_center":  (0,  15),
    "two_in_row":     (1,  10),
    "one_in_row":     (0,   5),
    "local_center":   (0,   5),
    "freedom":        (0,   8),
}


# ---------------------------------------------------------------------------
# Génération et manipulation des individus
# ---------------------------------------------------------------------------

def random_individual():
    return {k: random.randint(lo, hi) for k, (lo, hi) in RANGES.items()}


def mutate(weights, rate=0.4):
    """Modifie aléatoirement chaque poids avec probabilité rate."""
    child = dict(weights)
    for k, (lo, hi) in RANGES.items():
        if random.random() < rate:
            delta = random.randint(-3, 3)
            child[k] = max(lo, min(hi, child[k] + delta))
    return child


def crossover(a, b):
    """Crée un enfant en prenant chaque poids aléatoirement chez l'un ou l'autre."""
    return {k: (a[k] if random.random() < 0.5 else b[k]) for k in a}


# ---------------------------------------------------------------------------
# Évaluation : duel entre deux individus
# ---------------------------------------------------------------------------

def play_one(weights_a, weights_b, a_starts):
    """Joue une partie, retourne 'A', 'B' ou 'Nul'."""
    game = UltimateTTT()
    player_a = 1 if a_starts else 2
    player_b = 2 if a_starts else 1

    while not game.is_game_over():
        if game.current_player == player_a:
            row, col = get_best_move(game, depth=DEPTH, weights=weights_a)
        else:
            row, col = get_best_move(game, depth=DEPTH, weights=weights_b)
        game.make_move(row, col)

    if game.global_winner == player_a:
        return "A"
    elif game.global_winner == player_b:
        return "B"
    else:
        xa = game.count_local_wins(player_a)
        xb = game.count_local_wins(player_b)
        return "A" if xa > xb else ("B" if xb > xa else "Nul")


def score_duel(weights_a, weights_b):
    """
    Retourne (pts_a, pts_b) sur 2 parties (A en X puis B en X).
    Barème : victoire=4, nul=1, défaite=0.
    """
    pts_a = pts_b = 0
    for a_starts in (True, False):
        result = play_one(weights_a, weights_b, a_starts)
        if result == "A":
            pts_a += 4
        elif result == "B":
            pts_b += 4
        else:
            pts_a += 1
            pts_b += 1
    return pts_a, pts_b


# ---------------------------------------------------------------------------
# Tournoi round-robin : chaque individu affronte tous les autres
# ---------------------------------------------------------------------------

def tournament(population):
    """Retourne un classement [(score_total, individu), ...] décroissant."""
    n = len(population)
    scores = [0] * n

    total_duels = n * (n - 1) // 2
    done = 0
    for i in range(n):
        for j in range(i + 1, n):
            pts_i, pts_j = score_duel(population[i], population[j])
            scores[i] += pts_i
            scores[j] += pts_j
            done += 1
            print(f"    Duel {done}/{total_duels} : individu {i+1} vs {j+1} "
                  f"→ {pts_i}-{pts_j}", flush=True)

    ranked = sorted(zip(scores, population), key=lambda x: -x[0])
    return ranked


# ---------------------------------------------------------------------------
# Boucle évolutionnaire
# ---------------------------------------------------------------------------

def evolve():
    print("=" * 50)
    print("  OPTIMISATION GÉNÉTIQUE DES POIDS")
    print("=" * 50)
    print(f"  Population : {POP_SIZE}  |  Générations : {GENERATIONS}  |  Depth : {DEPTH}")
    print(f"  Poids par défaut : {DEFAULT_WEIGHTS}\n")

    # Génération 0 : population initiale (inclut les poids par défaut)
    population = [DEFAULT_WEIGHTS] + [random_individual() for _ in range(POP_SIZE - 1)]

    best_ever = None
    best_score_ever = -1

    for gen in range(1, GENERATIONS + 1):
        print(f"\n{'='*50}")
        print(f"  GÉNÉRATION {gen}/{GENERATIONS}")
        print(f"{'='*50}")

        t0 = time.time()
        ranked = tournament(population)
        elapsed = time.time() - t0

        print(f"\n  Classement (temps : {elapsed:.0f}s) :")
        for rank, (score, ind) in enumerate(ranked, 1):
            marker = " ← MEILLEUR" if rank == 1 else ""
            print(f"    {rank}. score={score:3d}  {ind}{marker}")

        # Mise à jour du meilleur global
        top_score, top_ind = ranked[0]
        if top_score > best_score_ever:
            best_score_ever = top_score
            best_ever = dict(top_ind)

        # Sélection : on garde la moitié supérieure
        survivors = [ind for _, ind in ranked[:POP_SIZE // 2]]

        # Nouvelle population : survivors + enfants (croisements + mutations)
        new_pop = list(survivors)
        while len(new_pop) < POP_SIZE:
            parent_a = random.choice(survivors)
            parent_b = random.choice(survivors)
            child = crossover(parent_a, parent_b)
            child = mutate(child)
            new_pop.append(child)

        population = new_pop

    print(f"\n{'='*50}")
    print("  MEILLEURS POIDS TROUVÉS")
    print(f"{'='*50}")
    print(f"  Score total : {best_score_ever}")
    for k, v in best_ever.items():
        default = DEFAULT_WEIGHTS[k]
        diff = f"  (+{v-default})" if v > default else (f"  ({v-default})" if v < default else "")
        print(f"    {k:20s} : {v}{diff}")
    print()
    print("  Pour utiliser ces poids, modifie DEFAULT_WEIGHTS dans ai.py :")
    print(f"  {best_ever}")
    print("=" * 50)

    return best_ever


if __name__ == "__main__":
    random.seed(42)
    best = evolve()
