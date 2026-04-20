# Compte-rendu — Ultimate Tic Tac Toe : Affrontement entre IA

**Auteur :** Matisse Geoffray  
**Date :** Avril 2026  
**Dépôt :** https://github.com/Matissegeoffray/Ultimate-Tic-Tac-Toe

---

## 1. Présentation du projet

L'Ultimate Tic Tac Toe est une variante du morpion classique jouée sur une grille de 9×9 cases,
composée de 9 sous-plateaux de 3×3. Le vainqueur est le premier joueur à aligner 3 sous-plateaux
gagnés (en ligne, colonne ou diagonale).

**Règle centrale :** après chaque coup joué en case (row, col) d'un sous-plateau,
l'adversaire est forcé de jouer dans le sous-plateau de coordonnées (row % 3, col % 3).
Si ce sous-plateau est déjà terminé (gagné ou nul), le joueur peut choisir librement.

---

## 2. Structure du code

| Fichier | Rôle | Lignes |
|---|---|---|
| `game.py` | Moteur de jeu : plateau, règles, validation, détection de victoire | 126 |
| `ai.py` | Algorithme Minimax + élagage Alpha-Beta + heuristique | 166 |
| `display.py` | Affichage texte de la grille 9×9 | 64 |
| `main.py` | Boucle de jeu : joueur vs IA et bataille IA vs IA | 292 |
| `optimize.py` | Optimisation génétique des poids de l'heuristique | 192 |
| `colab_game.py` | Version standalone pour Google Colab (compétition) | 313 |

**Total : ~1 150 lignes de Python.**

---

## 3. Représentation de l'état du jeu (`game.py`)

### Plateau

```
board[row][col]  →  0 = vide, 1 = X, 2 = O
row et col : 0 à 8
```

Le sous-plateau (br, bc) correspond aux lignes br×3 à br×3+2 et colonnes bc×3 à bc×3+2.

```python
local_winners[br][bc]  →  0 = en cours, 1 = X gagne, 2 = O gagne, 3 = nul
active_board           →  (br, bc) imposé, ou None si choix libre
current_player         →  1 (X) ou 2 (O)
```

### Principales méthodes

- `get_valid_moves()` : retourne la liste des coups légaux `(row, col)`.
  Si `active_board` est imposé et non terminé → cases vides de ce sous-plateau uniquement.
  Sinon → cases vides de tous les sous-plateaux non terminés.

- `make_move(row, col)` : place le pion, met à jour `local_winners`, `global_winner`,
  `active_board` et `current_player`.

- `is_game_over()` : vrai si un joueur a aligné 3 morpions **ou** si tous les sous-plateaux
  sont terminés.

- `copy()` : copie profonde pour le Minimax (chaque nœud de l'arbre est indépendant).

---

## 4. Algorithme IA (`ai.py`)

### 4.1 Minimax

Le Minimax explore récursivement tous les coups possibles jusqu'à une profondeur donnée.
À chaque niveau, le joueur maximiseur (IA) choisit le coup qui maximise le score,
et le joueur minimiseur (adversaire) choisit celui qui le minimise.

```
                Position actuelle (IA joue → MAXIMISE)
                           │
          ┌────────────────┼────────────────┐
          │                │                │
       Coup A           Coup B           Coup C
    (adversaire)     (adversaire)     (adversaire)
       MINIMISE         MINIMISE         MINIMISE
       │                │                │
    ┌──┴──┐          ┌──┴──┐          ┌──┴──┐
   D1    D2         E1    E2         F1    F2
  +10   -5        -10   +3          +7   +2

  min=−5         min=−10           min=+2

     └────────────────┼────────────────┘
               max(−5, −10, +2) = +2
               → L'IA choisit le Coup C
```

### 4.2 Élagage Alpha-Beta

L'élagage Alpha-Beta évite d'explorer des branches inutiles :
- **α (alpha)** : meilleur score garanti pour le maximiseur
- **β (beta)** : meilleur score garanti pour le minimiseur
- Si β ≤ α : la branche est abandonnée (coupure)

**Gain typique : 60 à 80 % de nœuds en moins** à explorer, ce qui permet
d'augmenter la profondeur sans ralentir l'IA.

```python
def minimax(game, depth, alpha, beta, maximizing, ai_player, weights=None):
    if game.is_game_over():
        ...  # score terminal
    if depth == 0:
        return heuristic(game, ai_player, weights)

    for row, col in game.get_valid_moves():
        child = game.copy()
        child.make_move(row, col)
        val = minimax(child, depth-1, alpha, beta, not maximizing, ai_player, weights)
        ...
        if beta <= alpha:
            break  # coupure Alpha-Beta
```

### 4.3 Profondeur de recherche

La profondeur par défaut est **3** (bon compromis vitesse/qualité, ~0.15s par coup).
Elle est configurable via `AI_DEPTH` dans `main.py` et `DEPTH` dans `optimize.py`.

| Profondeur | Temps moyen/coup | Qualité |
|---|---|---|
| 2 | ~0.01s | Correct |
| 3 | ~0.15s | Bon ✓ |
| 4 | ~2–5s | Très fort |
| 5 | ~30s+ | Risqué pour la compétition |

---

## 5. Heuristique (`ai.py` — `heuristic()`)

L'heuristique évalue une position non terminale du point de vue de l'IA.
Elle retourne un score entier : positif = bon pour l'IA, négatif = mauvais.

### Critères et poids par défaut

| Critère | Poids par défaut | Explication |
|---|---|---|
| Morpion gagné | ×10 | Objectif principal du jeu |
| Morpion central global gagné | +5 | Pivot stratégique (diagonales) |
| 2 pièces alignées sans blocage | +3 | Menace immédiate dans un sous-plateau |
| 1 pièce en développement | +1 | Construction à long terme |
| Case centrale d'un sous-plateau | +1 | Participe à 4 lignes gagnantes |
| Liberté de choix (active_board=None) | +2 | Avantage positionnel |

Les scores adverses sont symétriquement soustraits.

### Scores terminaux

- Victoire de l'IA → **+10 000**
- Défaite → **−10 000**
- Fin par remplissage → **(morpions_IA − morpions_adversaire) × 100**

---

## 6. Optimisation génétique des poids (`optimize.py`)

Pour trouver les meilleurs poids de l'heuristique automatiquement, on utilise un
**algorithme génétique** inspiré de la sélection naturelle.

### Principe

```
Population → Tournoi round-robin → Classement → Sélection (top 50%)
     ↑                                                    ↓
  Mutation ← Croisement ← Nouveaux individus générés
```

### Étapes détaillées

1. **Initialisation** : N individus avec des poids aléatoires (+ poids par défaut).
2. **Tournoi** : chaque individu affronte tous les autres (2 parties par duel).
   Les points sont calculés selon le barème du sujet (victoire=4, nul=1, défaite=0).
3. **Sélection** : les 50 % meilleurs survivent.
4. **Croisement** : deux parents sont choisis parmi les survivants, chaque poids
   est hérité aléatoirement de l'un ou l'autre.
5. **Mutation** : chaque poids a 40 % de chance d'être modifié de ±1 à ±3.
6. Répéter pour le nombre de générations configuré.

### Paramètres configurables (en haut de `optimize.py`)

```python
DEPTH       = 5   # profondeur pendant l'optimisation
POP_SIZE    = 8   # individus par génération
GENERATIONS = 3   # nombre de générations
```

---

## 7. Mode bataille IA vs IA (`main.py`)

Le menu principal propose deux modes :

- **[1] Joueur vs IA** : le joueur humain saisit ses coups (colonne puis ligne, 1–9).
- **[2] Bataille IA vs IA** : deux IA s'affrontent avec des profondeurs et des poids
  configurables séparément. Chaque combat = 2 parties (alternance qui commence).
  Les points sont calculés selon le barème officiel.

### Exemple de session bataille

```
Profondeur IA-A : 3
Profondeur IA-B : 4
Poids IA-B : two_in_row=6, global_center=12 (reste par défaut)
Nombre de combats : 3

--- Combat 1/3 ---
  Partie 1 (A=X) : Victoire A  [4.2s]  pts A=4 B=0
  Partie 2 (B=X) : Nul (X:4 O:4)      pts A=1 B=1
...
RÉSULTATS FINAUX
  IA-A (depth=3) : 2 victoires  18 pts
  IA-B (depth=4) : 1 victoire   10 pts
```

---

## 8. Utilisation pour la compétition (Google Colab)

Le fichier `colab_game.py` contient l'intégralité du code en un seul fichier.

**Instructions pour la compétition :**
1. Uploader `colab_game.py` dans Google Colab.
2. Dans une cellule : `!python colab_game.py`
3. Saisir les coups adverses manuellement quand c'est le tour du joueur.

---

## 9. Lancer le jeu

```bash
# Mode normal (VS Code)
python main.py

# Optimisation des poids
python optimize.py
```

---

## 10. Pistes d'amélioration possibles

- **Menace globale à 2** : bonus si 2 morpions alignés sans blocage au niveau global.
- **Bonus de coin** : les cases de coin participent à 3 lignes — les valoriser davantage.
- **Ordre d'exploration** : trier les coups par score heuristique avant le Minimax
  → l'Alpha-Beta coupe plus tôt → depth=4 devient jouable en temps raisonnable.
- **Iterative deepening** : explorer progressivement depth=1, 2, 3... avec une limite de temps,
  et retourner le meilleur coup trouvé avant timeout.
