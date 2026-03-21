# gui/board_view.py
"""Draws the FreeCell board: cascades, free cells, foundations."""
import pygame


class BoardView:
    def __init__(self, deck, theme=None):
        self.deck = deck
        self.theme = theme

        self.card_width = 100
        self.card_height = 140
        self.spacing = 20
        self.vertical_spacing = 35

        self.hitbox = {
            'free_cells': [None] * 4,
            'foundations': [None] * 4,
            'cascades': [None] * 8
        }

        if self.theme:
            self.theme.load_ui_elements(self.card_width, self.card_height)

        self._font = None

    def _get_font(self):
        if not self._font:
            self._font = pygame.font.SysFont('consolas', 16)
        return self._font

    # === SLOT DRAWING (uses theme if available) ===

    def _draw_empty_slot(self, screen, x, y):
        rect = pygame.Rect(x, y, self.card_width, self.card_height)
        pygame.draw.rect(screen, (0, 100, 0), rect, border_radius=8)
        pygame.draw.rect(screen, (150, 150, 150), rect, width=2, border_radius=8)

    def _draw_freecell_slot(self, screen, x, y):
        if self.theme and self.theme.freecell_img:
            screen.blit(self.theme.freecell_img, (x, y))
        else:
            self._draw_empty_slot(screen, x, y)

    def _draw_foundation_slot(self, screen, x, y, suit):
        if self.theme and self.theme.foundation_img.get(suit):
            screen.blit(self.theme.foundation_img[suit], (x, y))
        else:
            self._draw_empty_slot(screen, x, y)

    # === TOP AREA: free cells + foundations ===

    def _draw_top_area(self, screen, screen_width, state):
        center_gap = 80
        block_width = 4 * self.card_width + 3 * self.spacing
        total_top_width = (2 * block_width) + center_gap
        start_x = (screen_width - total_top_width) // 2
        start_y = 40

        # Free cells
        for i in range(4):
            col_x = start_x + i * (self.card_width + self.spacing)
            self._draw_freecell_slot(screen, col_x, start_y)
            rect = pygame.Rect(col_x, start_y, self.card_width, self.card_height)
            self.hitbox['free_cells'][i] = rect

            card = state.free_cells[i]
            if card is not None:
                img_key = (card.rank, card.suit)
                if img_key in self.deck:
                    screen.blit(self.deck[img_key],
                                self.deck[img_key].get_rect(topleft=(col_x, start_y)))

        # Foundations
        fnd_x = start_x + block_width + center_gap
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        for i in range(4):
            col_x = fnd_x + i * (self.card_width + self.spacing)
            self._draw_foundation_slot(screen, col_x, start_y, suits[i])
            rect = pygame.Rect(col_x, start_y, self.card_width, self.card_height)
            self.hitbox['foundations'][i] = rect

            pile = state.foundations[suits[i]]
            if pile:
                top = pile[-1]
                img_key = (top.rank, top.suit)
                if img_key in self.deck:
                    screen.blit(self.deck[img_key],
                                self.deck[img_key].get_rect(topleft=(col_x, start_y)))

        # Foundation counter
        font = self._get_font()
        count = state.foundation_count()
        txt = font.render(f"{count}/52", True, (220, 220, 100))
        cx = start_x + block_width + center_gap // 2 - txt.get_width() // 2
        screen.blit(txt, (cx, start_y + self.card_height + 5))

    # === CASCADES ===

    def _draw_cascades(self, screen, screen_width, state):
        total_w = 8 * self.card_width + 7 * self.spacing
        start_x = (screen_width - total_w) // 2
        start_y = 220

        self.hitbox['cascades'] = [[] for _ in range(8)]

        for i, cascade in enumerate(state.cascades):
            col_x = start_x + i * (self.card_width + self.spacing)

            if not cascade:
                empty_rect = pygame.Rect(col_x, start_y, self.card_width, self.card_height)
                self.hitbox['cascades'][i].append(empty_rect)
            else:
                for j, card in enumerate(cascade):
                    card_y = start_y + j * self.vertical_spacing
                    img_key = (card.rank, card.suit)
                    if img_key in self.deck:
                        card_img = self.deck[img_key]
                        card_rect = card_img.get_rect(topleft=(col_x, card_y))
                        screen.blit(card_img, card_rect)
                        self.hitbox['cascades'][i].append(card_rect)

    # === PUBLIC ===

    def draw_board(self, screen, screen_width, screen_height, state):
        """Draw only the board (no buttons, no panels)."""
        self._draw_top_area(screen, screen_width, state)
        self._draw_cascades(screen, screen_width, state)