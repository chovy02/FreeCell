#gui/board_view.py
import pygame

class BoardView:
    def __init__(self, deck):
        self.deck = deck

        self.card_width = 100
        self.card_height = 140
        self.spacing = 20

        self.vertical_spacing = 35

        self.hitbox = {
            'free_cells': [None] * 4,
            'foundations': [None] * 4,
            'cascades': [None] * 8
        }


    def draw_empty_slot(self, screen, x, y):
        rect = pygame.Rect(x, y, self.card_width, self.card_height)
        pygame.draw.rect(screen, (0, 100, 0), rect, border_radius=8)
        pygame.draw.rect(screen, (150, 150, 150), rect, width=2, border_radius=8)

    def draw_cascades(self, screen, screen_width, state):
        total_cascades_width = (8 * self.card_width) + (7 * self.spacing)
        start_x = (screen_width - total_cascades_width) // 2
        start_y = 220

        for i, cascade in enumerate(state.cascades):
            col_x = start_x + i * (self.card_width + self.spacing)

            if len(cascade) == 0:
                empty_rect = pygame.Rect(col_x, start_y, self.card_width, self.card_height)
                self.hitbox['cascades'][i] = empty_rect

            else:
                for j, card in enumerate(cascade):
                    card_y = start_y + (j * self.vertical_spacing)
                    img_key = (card.rank, card.suit)

                    if img_key in self.deck:
                        card_img = self.deck[img_key]
                        card_rect = card_img.get_rect(topleft=(col_x, card_y))
                        screen.blit(card_img, card_rect)

                    if j == len(cascade) - 1:
                        self.hitbox['cascades'][i] = card_rect

    def draw_top_area(self, screen, screen_width, state):
        #Draw free cells and foundations
        center_gap = 80

        block_width = 4 * self.card_width + 3 * self.spacing

        total_top_width = (2 * block_width) + center_gap

        start_x = (screen_width - total_top_width) // 2
        start_y = 40

        # Draw free cells
        for i in range(4):
            col_x = start_x + i * (self.card_width + self.spacing)
            self.draw_empty_slot(screen, col_x, start_y)
            card = state.free_cells[i]

            rect = pygame.Rect(col_x, start_y, self.card_width, self.card_height)
            self.hitbox['free_cells'][i] = rect

            if card is not None:
                img_key = (card.rank, card.suit)
                if img_key in self.deck:
                    card_img = self.deck[img_key]
                    card_rect = card_img.get_rect(topleft=(col_x, start_y))
                    screen.blit(card_img, card_rect)

        # Draw foundations
        foundation_start_x = start_x + block_width + center_gap
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        for i in range(4):
            col_x = foundation_start_x + i * (self.card_width + self.spacing)
            self.draw_empty_slot(screen, col_x, start_y)

            rect = pygame.Rect(col_x, start_y, self.card_width, self.card_height)
            self.hitbox['foundations'][i] = rect

            suit = suits[i]
            foundation_pile = state.foundations[suit]

            if (len(foundation_pile) > 0):
                top_card = foundation_pile[-1]
                img_key = (top_card.rank, top_card.suit)
                if img_key in self.deck:
                    card_img = self.deck[img_key]
                    card_rect = card_img.get_rect(topleft=(col_x, start_y))
                    screen.blit(card_img, card_rect)



    def draw(self, screen, screen_width, screen_height, state):
        self.draw_top_area(screen, screen_width, state)
        self.draw_cascades(screen, screen_width, state)