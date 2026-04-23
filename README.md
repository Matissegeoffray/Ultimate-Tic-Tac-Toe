# 🎮 Ultimate Tic Tac Toe — IA Minimax

> Implémentation jouable d'Ultimate Morpion avec une IA Minimax alpha-bêta et optimisation génétique des poids heuristiques.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Algorithm](https://img.shields.io/badge/Minimax-Alpha--Beta-orange)
![Optimization](https://img.shields.io/badge/Optimisation-Génétique-green)
![Modes](https://img.shields.io/badge/Modes-Joueur%20%2F%20IA%20vs%20IA-purple)

---

## 🎯 Objectif

Implémenter une IA capable de jouer à l'Ultimate Morpion (9 morpions imbriqués dans un plateau 3×3 global) en utilisant l'algorithme **Minimax avec élagage alpha-bêta** et une heuristique à poids réglables.

Projet réalisé dans le cadre du cours **ESILV A3 — Fondements de l'IA**, avec compétition inter-IA sur Google Colab.

**Contraintes du sujet :**
- Minimax + Alpha-Beta obligatoires — aucun dictionnaire de coups ou ouverture pré-calculée
- Python pur, compatible VS Code et Google Colab
- Affichage texte 9×9, colonnes et lignes numérotées 1 à 9
- En cas de nul : le joueur avec le plus de morpions gagnés remporte la partie

---

## 📊 Résultats

| Configuration | Comportement observé |
|---|---|
| Minimax depth=2 | Réactif, quelques erreurs tactiques |
| Minimax depth=3 (défaut) | Bon niveau — évite la majorité des pièges |
| Minimax depth=4 | Fort mais ~10× plus lent qu'en depth=3 |
| **Poids optimisés (génétique)** | **Supérieur aux poids par défaut en tournoi round-robin** |

L'optimisation génétique identifie systématiquement une valorisation plus élevée du morpion central global (`global_center`) et des alignements de 2 pièces (`two_in_row`) par rapport aux poids initiaux.

---

## 🛠️ Stack

- **Moteur de jeu** : `game.py` — logique complète d'Ultimate Morpion (coups valides, gagnant local/global, copie d'état)
- **IA** : `ai.py` — heuristique à 6 poids, Minimax récursif avec élagage alpha-bêta
- **Interface** : `display.py` — affichage console du plateau 9×9 avec zones actives
- **Modes de jeu** : `main.py` — Joueur vs IA, Bataille IA vs IA avec barème de points
- **Optimisation** : `optimize.py` — algorithme génétique (sélection, croisement, mutation) sur les poids heuristiques
- **Compétition** : `colab_game.py` — wrapper Google Colab pour la compétition académique

---

## 🔬 Approche

### 1. Moteur de jeu

Le plateau est une grille `9×9` divisée en 9 sous-plateaux `3×3`. Chaque coup envoie l'adversaire dans le sous-plateau correspondant à la case jouée (`next = (row % 3, col % 3)`). Si ce sous-plateau est déjà terminé (gagné ou plein), le joueur est libre de choisir n'importe quel sous-plateau actif. Le moteur maintient `active_board`, `local_winners` et `global_winner`.

### 2. Heuristique à 6 poids

L'évaluation de position combine six critères réglables :

| Poids | Rôle | Valeur par défaut |
|---|---|---|
| `local_win` | Morpion gagné | 10 |
| `global_center` | Morpion central du plateau global | 5 |
| `two_in_row` | 2 pièces alignées sans blocage | 3 |
| `one_in_row` | 1 pièce en développement | 1 |
| `local_center` | Case centrale d'un sous-plateau | 1 |
| `freedom` | Liberté de choisir le sous-plateau suivant | 2 |

### 3. Minimax avec élagage alpha-bêta

L'algorithme explore l'arbre de jeu en profondeur configurable (`depth=3` par défaut). L'élagage alpha-bêta coupe les branches inutiles, rendant le depth=3 jouable en temps réel. Les feuilles reçoivent un score terminal (`±10 000`) ou heuristique à depth=0.

### 4. Optimisation génétique

`optimize.py` fait évoluer une population de jeux de poids sur plusieurs générations :
- **Évaluation** : tournoi round-robin, chaque individu affronte tous les autres (2 parties par duel)
- **Sélection** : on conserve la moitié supérieure du classement
- **Reproduction** : croisement uniforme + mutation aléatoire (Δ ∈ [-3, +3] avec probabilité 40%)
- **Barème** : victoire = 4 pts, nul = 1 pt, défaite = 0 pt

---

## 🧪 Cas limites gérés

| Scénario | Comportement |
|---|---|
| Coup invalide (case prise) | Message d'erreur, re-demande le coup |
| Mauvais sous-plateau | Message + indication du sous-plateau autorisé |
| Sous-plateau cible déjà terminé | Joueur libre de choisir n'importe quel sous-plateau actif |
| Victoire globale | 3 sous-plateaux alignés → annonce du vainqueur, fin de partie |
| Match nul (tous sous-plateaux complets) | Compte les morpions gagnés → vainqueur par majorité |
| Égalité parfaite de morpions | Nul total annoncé |

---

## 📂 Structure du projet

```
ultimate-tic-tac-toe/
├── game.py          # Moteur de jeu — état, coups valides, conditions de fin
├── ai.py            # Heuristique + Minimax alpha-bêta + get_best_move
├── display.py       # Affichage console du plateau
├── main.py          # Menu principal, mode Joueur vs IA, mode Bataille IA vs IA
├── optimize.py      # Optimisation génétique des poids heuristiques
├── colab_game.py    # Version adaptée pour Google Colab (compétition)
└── README.md
```

---

## ⚙️ Lancer le jeu

```bash
git clone https://github.com/Matissegeoffray/ultimate-tic-tac-toe.git
cd ultimate-tic-tac-toe
python main.py
```

Pour lancer l'optimisation génétique des poids :

```bash
python optimize.py
```

**Vérification rapide du moteur :**

```bash
python -c "from game import UltimateTTT; g = UltimateTTT(); print(len(g.get_valid_moves()))"
# → 81 (tous les coups valides au premier tour)
```

Modifier `AI_DEPTH` dans `main.py` et `DEPTH`, `POP_SIZE`, `GENERATIONS` dans `optimize.py` pour ajuster les paramètres.

---

## 💡 Points clés

- **L'heuristique prime sur la profondeur** : passer de depth=2 à depth=3 améliore le niveau, mais des poids mal calibrés à depth=3 perdent contre de bons poids à depth=2.
- **L'élagage alpha-bêta est indispensable** : sans lui, depth=3 serait injouable en temps réel sur un plateau à 81 cases.
- **L'optimisation génétique converge vite** : en 3 générations de 8 individus, on trouve des poids nettement meilleurs — les gains supplémentaires sont marginaux au-delà.
- **Le contrôle du sous-plateau central** est la variable stratégique dominante — confirmée à la fois par l'heuristique et par les poids optimisés.

---

## 👤 Auteur

**Matisse Geoffray** — Étudiant ingénieur 3ème année à l'ESILV

🔍 À la recherche d'un **stage de 2 mois en ML / Data Science** (juin–juillet 2026) — Paris ou Singapour

📧 matisse.geoffray@gmail.com · [GitHub](https://github.com/Matissegeoffray)
