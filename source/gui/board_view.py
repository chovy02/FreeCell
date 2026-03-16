#gui/board_view.py
import pygame

class BoardView:
    def __init__(self, deck):
        self.deck = deck

        self.card_width = 100
        self.card_height = 140
        self.spacing = 20

        self.vertical_spacing = 35

    def draw_cascades(self, screen, screen_width, state):
        total_cascades_width = (8 * self.card_width) + (7 * self.spacing)
        start_x = (screen_width - total_cascades_width) // 2
        start_y = 220

        for i, cascade in enumerate(state.cascades):
            col_x = start_x + i * (self.card_width + self.spacing)

            for j, card in enumerate(cascade):
                card_y = start_y + (j * self.vertical_spacing)
                img_key = (card.rank, card.suit)

                if img_key in self.deck:
                    card_img = self.deck[img_key]
                    card_rect = card_img.get_rect(topleft=(col_x, card_y))
                    screen.blit(card_img, card_rect)


    def draw(self, screen, screen_width, screen_height, state):
        self.draw_cascades(screen, screen_width, state)