import sys
import pygame
import random
from .asset_manager import CardLoader
from .theme_manager import ThemeManager
from .menu_view import MenuView
from .manual_screen import ManualScreen
from .ai_screen import AIScreen
from core.state import State

# Danh sách các màn không thể giải được cần loại bỏ
EXCLUDED_SEEDS = {11982, 146692, 186216, 455889, 495505, 512118, 517776, 781948}

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE | pygame.WINDOWMAXIMIZED)
        pygame.display.set_caption("FreeCell")

        self.width  = self.screen.get_width()
        self.height = self.screen.get_height()
        self.clock  = pygame.time.Clock()
        self.running = True

        self.theme = ThemeManager()
        self.theme.load_background("background.png", self.width, self.height)

        loader   = CardLoader()
        self.deck = loader.load_cards()

        self.current_screen = "MENU"
        self.menu           = MenuView(self.theme, self.width, self.height)
        self.manual_screen  = None
        self.ai_screen      = None

    def _get_valid_random_seed(self):
        """Tạo seed ngẫu nhiên < 1.000.000 và không nằm trong danh sách loại trừ"""
        while True:
            seed = random.randrange(1000000)
            if seed not in EXCLUDED_SEEDS:
                return seed

    def _start_game(self, mode):
        state = State()
        random_seed = self._get_valid_random_seed()
        print(f"Khởi tạo màn chơi với Seed: {random_seed}") # In ra để tiện theo dõi
        
        state.initialize_game(random_seed)

        w, h = self.width, self.height

        if mode == "MANUAL":
            self.manual_screen = ManualScreen(self.deck, self.theme, state, w, h)
            self.current_screen = "MANUAL"
        elif mode == "AI":
            self.ai_screen = AIScreen(self.deck, self.theme, state, w, h)
            self.current_screen = "AI"

    def _handle_resize(self, w, h):
        self.width  = w
        self.height = h
        self.theme.resize_background(w, h)
        self.menu.update_layout(w, h)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                if event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event.w, event.h)

                if self.current_screen == "MENU":
                    result = self.menu.handle_event(event)
                    if result == "QUIT":
                        self.running = False
                    elif result:
                        self._start_game(result)

                elif self.current_screen == "MANUAL":
                    result = self.manual_screen.handle_event(event)
                    if result == "MENU":
                        self.current_screen = "MENU"

                elif self.current_screen == "AI":
                    result = self.ai_screen.handle_event(event)
                    if result == "MENU":
                        self.current_screen = "MENU"

            if self.current_screen == "AI" and self.ai_screen:
                self.ai_screen.update()

            if self.current_screen == "MENU":
                self.menu.draw(self.screen)
            elif self.current_screen == "MANUAL":
                self.manual_screen.draw(self.screen, self.width, self.height)
            elif self.current_screen == "AI":
                self.ai_screen.draw(self.screen, self.width, self.height)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()