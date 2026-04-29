"""
Optimisation génétique des poids de l'heuristique.
Lance : python optimize.py
Les résultats sont sauvegardés dans optimize_results/
"""

import random
import time
import os
from datetime import datetime
from game import UltimateTTT
from ai import get_best_move, DEFAULT_WEIGHTS

# ---------------------------------------------------------------------------
# Paramètres de l'optimisation
# ---------------------------------------------------------------------------

DEPTH       = 3   # profondeur Minimax pendant l'optimisation
POP_SIZE    = 8   # individus par génération (pair recommandé)
GENERATIONS = 3   # nombre de générations
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
# Journalisation (console + fichier)
# ---------------------------------------------------------------------------

_log_file = None

def _log(msg=""):
    print(msg, flush=True)
    if _log_file:
        _log_file.write(msg + "\n")
        _log_file.flush()


# ---------------------------------------------------------------------------
# Génération et manipulation des individus
# ---------------------------------------------------------------------------

def random_individual():
    return {k: random.randint(lo, hi) for k, (lo, hi) in RANGES.items()}


def mutate(weights, rate=0.4):
    child = dict(weights)
    for k, (lo, hi) in RANGES.items():
        if random.random() < rate:
            delta = random.randint(-3, 3)
            child[k] = max(lo, min(hi, child[k] + delta))
    return child


def crossover(a, b):
    return {k: (a[k] if random.random() < 0.5 else b[k]) for k in a}


# ---------------------------------------------------------------------------
# Évaluation : duel entre deux individus
# ---------------------------------------------------------------------------

def play_one(weights_a, weights_b, a_starts):
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
# Tournoi round-robin
# ---------------------------------------------------------------------------

def tournament(population):
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
            _log(f"    Duel {done}/{total_duels} : individu {i+1} vs {j+1} → {pts_i}-{pts_j}")

    ranked = sorted(zip(scores, population), key=lambda x: -x[0])
    return ranked


# ---------------------------------------------------------------------------
# Boucle évolutionnaire
# ---------------------------------------------------------------------------

def evolve():
    global _log_file

    # Création du dossier de résultats
    os.makedirs("optimize_results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join("optimize_results", f"run_{timestamp}.txt")
    _log_file = open(log_path, "w", encoding="utf-8")

    try:
        _log("=" * 60)
        _log("  OPTIMISATION GÉNÉTIQUE DES POIDS")
        _log("=" * 60)
        _log(f"  Lancé le : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
        _log(f"  Population : {POP_SIZE}  |  Générations : {GENERATIONS}  |  Depth : {DEPTH}")
        _log(f"  Poids par défaut : {DEFAULT_WEIGHTS}")
        _log()

        population = [DEFAULT_WEIGHTS] + [random_individual() for _ in range(POP_SIZE - 1)]

        _log("  Population initiale :")
        for i, ind in enumerate(population):
            label = " (poids par défaut)" if i == 0 else ""
            _log(f"    Individu {i+1}{label} : {ind}")

        best_ever = None
        best_score_ever = -1
        history = []  # [(gen, score, weights)]

        for gen in range(1, GENERATIONS + 1):
            _log()
            _log("=" * 60)
            _log(f"  GÉNÉRATION {gen}/{GENERATIONS}")
            _log("=" * 60)

            t0 = time.time()
            ranked = tournament(population)
            elapsed = time.time() - t0

            _log()
            _log(f"  Classement après {elapsed:.0f}s de tournoi :")
            _log(f"  {'Rang':<5} {'Score':>6}  {'local_win':>9} {'glob_ctr':>8} {'2row':>5} {'1row':>5} {'lctr':>5} {'free':>5}")
            _log(f"  {'-'*5} {'-'*6}  {'-'*9} {'-'*8} {'-'*5} {'-'*5} {'-'*5} {'-'*5}")
            for rank, (score, ind) in enumerate(ranked, 1):
                marker = " ← MEILLEUR" if rank == 1 else ""
                _log(
                    f"  {rank:<5} {score:>6}  "
                    f"{ind['local_win']:>9} {ind['global_center']:>8} "
                    f"{ind['two_in_row']:>5} {ind['one_in_row']:>5} "
                    f"{ind['local_center']:>5} {ind['freedom']:>5}"
                    f"{marker}"
                )

            top_score, top_ind = ranked[0]
            history.append((gen, top_score, dict(top_ind)))

            if top_score > best_score_ever:
                best_score_ever = top_score
                best_ever = dict(top_ind)
                _log(f"\n  → Nouveau meilleur global ! score={top_score}")

            survivors = [ind for _, ind in ranked[:POP_SIZE // 2]]
            new_pop = list(survivors)
            while len(new_pop) < POP_SIZE:
                parent_a = random.choice(survivors)
                parent_b = random.choice(survivors)
                child = crossover(parent_a, parent_b)
                child = mutate(child)
                new_pop.append(child)
            population = new_pop

        # ------------------------------------------------------------------
        # Résumé de l'évolution
        # ------------------------------------------------------------------
        _log()
        _log("=" * 60)
        _log("  ÉVOLUTION DU MEILLEUR SCORE PAR GÉNÉRATION")
        _log("=" * 60)
        for gen, score, ind in history:
            _log(f"  Génération {gen} : meilleur score = {score}")
            for k, v in ind.items():
                default = DEFAULT_WEIGHTS[k]
                diff = f" (+{v-default})" if v > default else (f" ({v-default})" if v < default else "")
                _log(f"    {k:20s} : {v}{diff}")

        # ------------------------------------------------------------------
        # Meilleurs poids finaux
        # ------------------------------------------------------------------
        _log()
        _log("=" * 60)
        _log("  MEILLEURS POIDS TROUVÉS")
        _log("=" * 60)
        _log(f"  Score total : {best_score_ever}")
        _log()
        _log(f"  {'Critère':<22} {'Défaut':>7} {'Optimal':>8} {'Différence':>12}")
        _log(f"  {'-'*22} {'-'*7} {'-'*8} {'-'*12}")
        for k, v in best_ever.items():
            default = DEFAULT_WEIGHTS[k]
            diff = f"+{v-default}" if v > default else (f"{v-default}" if v < default else "=")
            _log(f"  {k:<22} {default:>7} {v:>8} {diff:>12}")

        _log()
        _log("  Copier-coller dans ai.py → DEFAULT_WEIGHTS :")
        _log(f"  {best_ever}")
        _log()
        _log(f"  Résultats sauvegardés dans : {log_path}")
        _log("=" * 60)

    finally:
        _log_file.close()
        _log_file = None

    return best_ever


if __name__ == "__main__":
    random.seed(42)
    best = evolve()
