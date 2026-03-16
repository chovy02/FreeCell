#gui/app.py
import sys
import pygame
from .asset_manager import CardLoader

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("FreeCell")
        self.clock = pygame.time.Clock()
        self.running = True

        loader = CardLoader()
        self.deck = loader.load_cards()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.screen.fill((0, 255, 0))

            # Draw Cards

            if ('A', 'hearts') in self.deck:
                self.screen.blit(self.deck[('A', 'hearts')], (50, 50))

            if ('J', 'hearts') in self.deck:
                self.screen.blit(self.deck[('J', 'hearts')], (160, 50))

            pygame.display.flip()

            self.clock.tick(60)

        pygame.quit()
        sys.exit()