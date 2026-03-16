#gui/app.py
import sys
import pygame
from .asset_manager import CardLoader
from .board_view import BoardView
from core.state import State

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

            self.screen.fill((0, 255, 0))

            self.board_view.draw(self.screen, self.screen_width, self.screen_height, self.state)

            pygame.display.flip()

            self.clock.tick(60)

        pygame.quit()
        sys.exit()