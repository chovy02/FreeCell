#gui/app.py
import sys
import pygame
from .asset_manager import CardLoader
from .board_view import BoardView
from core.state import State
from .game_controller import GameController

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE | pygame.WINDOWMAXIMIZED)
        pygame.display.set_caption("FreeCell")

        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()

        self.clock = pygame.time.Clock()
        self.running = True

        loader = CardLoader()
        self.deck = loader.load_cards()

        self.board_view = BoardView(self.deck)

        self.state = State()
        self.state.initialize_game()

        self.game_controller = GameController()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

                if event.type == pygame.VIDEORESIZE:
                    self.screen_width = event.w
                    self.screen_height = event.h

                if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP]:
                    self.game_controller.handle_event(event, self.state, self.board_view)

            self.screen.fill((0, 255, 0))

            self.board_view.draw(self.screen, self.screen_width, self.screen_height, self.state)

            #Draw dragged card on top of everything else
            if len(self.game_controller.dragging_cards) > 0:
                for i, card in enumerate(self.game_controller.dragging_cards):
                    img_key = (card.rank, card.suit)
                    if img_key in self.deck:
                        card_img = self.deck[img_key]

                        draw_x = self.game_controller.drag_pos[0]
                        draw_y = self.game_controller.drag_pos[1] + (i * self.board_view.vertical_spacing)

                        card_rect = card_img.get_rect(topleft=(draw_x, draw_y))
                        self.screen.blit(card_img, card_rect)

            pygame.display.flip()

            self.clock.tick(60)

        pygame.quit()
        sys.exit()