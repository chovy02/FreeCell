# gui/board_view.py
"""Draws the FreeCell board: cascades, free cells, foundations."""
import pygame


class BoardView:
    def __init__(self, deck, theme=None):
        self.deck   = deck
        self.theme  = theme

        self.card_width       = 100
        self.card_height      = 140
        self.spacing          = 20
        self.vertical_spacing = 35

        self.hitbox = {
            'free_cells':  [None] * 4,
            'foundations': [None] * 4,
            'cascades':    [None] * 8,
        }

        if self.theme:
            self.theme.load_ui_elements(self.card_width, self.card_height)

        self._font = None

    def _get_font(self):
        if not self._font:
            self._font = pygame.font.SysFont('consolas', 16)
        return self._font

    # ─── SLOT HELPERS ──────────────────────────────────────────────────

    def _draw_plain_slot(self, screen, x, y):
        """Fallback slot (no image asset): dark fill + thin white border."""
        rect = pygame.Rect(x, y, self.card_width, self.card_height)
        pygame.draw.rect(screen, (18, 38, 18), rect, border_radius=10)
        pygame.draw.rect(screen, (195, 195, 195), rect, width=1, border_radius=10)

    def _draw_freecell_slot(self, screen, x, y):
        if self.theme and self.theme.freecell_img:
            screen.blit(self.theme.freecell_img, (x, y))
        else:
            self._draw_plain_slot(screen, x, y)

    def _draw_foundation_slot(self, screen, x, y, suit):
        if self.theme and self.theme.foundation_img.get(suit):
            screen.blit(self.theme.foundation_img[suit], (x, y))
        else:
            self._draw_plain_slot(screen, x, y)

    def _draw_empty_cascade_slot(self, screen, x, y):
        """
        Empty cascade column looks identical to a freecell slot —
        reuses the freecell image asset so all empty slots are visually
        consistent (white-border card frame).
        """
        if self.theme and self.theme.freecell_img:
            screen.blit(self.theme.freecell_img, (x, y))
        else:
            self._draw_plain_slot(screen, x, y)

    # ─── TOP AREA ──────────────────────────────────────────────────────

    def _draw_top_area(self, screen, screen_width, state):
        center_gap  = 80
        block_width = 4 * self.card_width + 3 * self.spacing
        total_w     = 2 * block_width + center_gap
        start_x     = (screen_width - total_w) // 2
        start_y     = 40

        # Free cells
        for i in range(4):
            col_x = start_x + i * (self.card_width + self.spacing)
            self._draw_freecell_slot(screen, col_x, start_y)
            self.hitbox['free_cells'][i] = pygame.Rect(col_x, start_y, self.card_width, self.card_height)
            card = state.free_cells[i]
            if card is not None and (card.rank, card.suit) in self.deck:
                screen.blit(self.deck[(card.rank, card.suit)], (col_x, start_y))

        # Foundations
        fnd_x = start_x + block_width + center_gap
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        for i in range(4):
            col_x = fnd_x + i * (self.card_width + self.spacing)
            self._draw_foundation_slot(screen, col_x, start_y, suits[i])
            self.hitbox['foundations'][i] = pygame.Rect(col_x, start_y, self.card_width, self.card_height)
            pile = state.foundations[suits[i]]
            if pile and (pile[-1].rank, pile[-1].suit) in self.deck:
                screen.blit(self.deck[(pile[-1].rank, pile[-1].suit)], (col_x, start_y))

        # Foundation counter pill (centred between the two blocks)
        font   = self._get_font()
        count  = state.foundation_count()
        txt    = font.render(f"{count}/52", True, (220, 220, 100))
        cx     = start_x + block_width + center_gap // 2
        pw, ph = txt.get_width() + 18, txt.get_height() + 6
        px, py = cx - pw // 2, start_y + self.card_height + 6

        pill = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(pill, (0, 0, 0, 110), pill.get_rect(), border_radius=10)
        screen.blit(pill, (px, py))
        pygame.draw.rect(screen, (80, 80, 60), (px, py, pw, ph), width=1, border_radius=10)
        screen.blit(txt, (px + 9, py + 3))

    # ─── CASCADES ──────────────────────────────────────────────────────

    def _draw_cascades(self, screen, screen_width, state):
        total_w = 8 * self.card_width + 7 * self.spacing
        start_x = (screen_width - total_w) // 2
        start_y = 220

        self.hitbox['cascades'] = [[] for _ in range(8)]

        for i, cascade in enumerate(state.cascades):
            col_x = start_x + i * (self.card_width + self.spacing)

            if not cascade:
                self._draw_empty_cascade_slot(screen, col_x, start_y)
                self.hitbox['cascades'][i].append(
                    pygame.Rect(col_x, start_y, self.card_width, self.card_height))
            else:
                for j, card in enumerate(cascade):
                    card_y  = start_y + j * self.vertical_spacing
                    img_key = (card.rank, card.suit)
                    if img_key in self.deck:
                        img  = self.deck[img_key]
                        rect = img.get_rect(topleft=(col_x, card_y))
                        screen.blit(img, rect)
                        self.hitbox['cascades'][i].append(rect)

    # ─── PUBLIC ────────────────────────────────────────────────────────

    def draw_board(self, screen, screen_width, screen_height, state):
        self._draw_top_area(screen, screen_width, state)
        self._draw_cascades(screen, screen_width, state)