import copy


class UltimateTTT:
    """
    Plateau : board[row][col], row et col de 0 à 8.
    Sous-plateau (br, bc) couvre les lignes br*3 à br*3+2 et colonnes bc*3 à bc*3+2.
    Joueur 1 = X (premier à jouer), Joueur 2 = O.
    local_winners[br][bc] : 0=en cours, 1=X, 2=O, 3=nul.
    active_board : (br, bc) imposé, ou None si le joueur choisit librement.
    """

    LINES = [
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)],
    ]

    def __init__(self):
        self.board = [[0] * 9 for _ in range(9)]
        self.local_winners = [[0] * 3 for _ in range(3)]
        self.active_board = None  # None = joueur libre de choisir
        self.current_player = 1
        self.global_winner = 0

    # ------------------------------------------------------------------
    # Lecture de l'état

    def get_local_values(self, br, bc):
        """Retourne une grille 3x3 des valeurs du sous-plateau (br, bc)."""
        return [
            [self.board[br * 3 + r][bc * 3 + c] for c in range(3)]
            for r in range(3)
        ]

    def get_valid_moves(self):
        """Liste de (row, col) jouables ce tour-ci."""
        if self.active_board is not None:
            br, bc = self.active_board
            moves = self._empty_cells_in(br, bc)
            if moves:
                return moves
        # Sous-plateau libre (active_board=None ou sous-plateau imposé terminé)
        moves = []
        for br in range(3):
            for bc in range(3):
                if self.local_winners[br][bc] == 0:
                    moves.extend(self._empty_cells_in(br, bc))
        return moves

    def _empty_cells_in(self, br, bc):
        return [
            (br * 3 + r, bc * 3 + c)
            for r in range(3)
            for c in range(3)
            if self.board[br * 3 + r][bc * 3 + c] == 0
        ]

    # ------------------------------------------------------------------
    # Modification de l'état

    def make_move(self, row, col):
        """Joue le coup (row, col) pour le joueur courant."""
        self.board[row][col] = self.current_player

        br, bc = row // 3, col // 3
        self._update_local_winner(br, bc)
        self._update_global_winner()

        # Le prochain sous-plateau imposé = (row%3, col%3)
        next_br, next_bc = row % 3, col % 3
        if self.local_winners[next_br][next_bc] != 0:
            self.active_board = None
        else:
            self.active_board = (next_br, next_bc)

        self.current_player = 3 - self.current_player

    def _update_local_winner(self, br, bc):
        vals = self.get_local_values(br, bc)
        for line in self.LINES:
            cells = [vals[r][c] for r, c in line]
            if cells[0] != 0 and cells[0] == cells[1] == cells[2]:
                self.local_winners[br][bc] = cells[0]
                return
        if all(vals[r][c] != 0 for r in range(3) for c in range(3)):
            self.local_winners[br][bc] = 3  # nul

    def _update_global_winner(self):
        w = self.local_winners
        for line in self.LINES:
            values = [w[r][c] for r, c in line]
            if values[0] in (1, 2) and values[0] == values[1] == values[2]:
                self.global_winner = values[0]
                return

    # ------------------------------------------------------------------
    # Conditions de fin

    def is_game_over(self):
        if self.global_winner != 0:
            return True
        return all(
            self.local_winners[br][bc] != 0
            for br in range(3)
            for bc in range(3)
        )

    def count_local_wins(self, player):
        return sum(
            1
            for br in range(3)
            for bc in range(3)
            if self.local_winners[br][bc] == player
        )

    # ------------------------------------------------------------------
    # Copie pour le Minimax

    def copy(self):
        return copy.deepcopy(self)
