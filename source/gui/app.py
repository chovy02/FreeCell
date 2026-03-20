# gui/app.py
import sys
import pygame
from .asset_manager import CardLoader
from .board_view import BoardView
from core.state import State
from .game_controller import GameController
from .theme_manager import ThemeManager
from solvers.A_star import AStarSolver # Thêm dòng Import này

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE | pygame.WINDOWMAXIMIZED)
        pygame.display.set_caption("FreeCell")

        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()

        self.clock = pygame.time.Clock()

        self.theme = ThemeManager()
        self.theme.load_background("background.png", self.screen_width, self.screen_height)

        self.running = True

        loader = CardLoader()
        self.deck = loader.load_cards()

        self.board_view = BoardView(self.deck, self.theme)

        self.state = State()
        self.state.initialize_game()

        self.game_controller = GameController()
        
        # --- THÊM BIẾN CHO A* ---
        self.auto_moves = []
        self.last_move_time = 0

    def apply_auto_move(self, move):
        """Hàm trợ giúp: thực hiện trực tiếp Move lên State thật của trò chơi"""
        m_type, src, dst, count = move
        moving_cards = []
        
        if m_type.startswith('c_'):
            moving_cards = self.state.cascades[src][-count:]
            self.state.cascades[src] = self.state.cascades[src][:-count]
        elif m_type.startswith('f_'):
            moving_cards = [self.state.free_cells[src]]
            self.state.free_cells[src] = None

        if m_type.endswith('_found'):
            self.state.foundations[dst].extend(moving_cards)
        elif m_type.endswith('_f'):
            self.state.free_cells[dst] = moving_cards[0]
        elif m_type.endswith('_c'):
            self.state.cascades[dst].extend(moving_cards)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        
                    # --- XỬ LÝ PHÍM 'A' TẠI ĐÂY ---
                    if event.key == pygame.K_a:
                        if not self.auto_moves:
                            # Khởi tạo thuật toán và chạy
                            solver = AStarSolver(self.state)
                            self.auto_moves = solver.solve()

                if event.type == pygame.VIDEORESIZE:
                    self.screen_width = event.w
                    self.screen_height = event.h
                    self.theme.resize_background(self.screen_width, self.screen_height)

                if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP]:
                    # Chặn người chơi thao tác khi hệ thống đang giải
                    if not self.auto_moves:
                        self.game_controller.handle_event(event, self.state, self.board_view)

            # --- THỰC HIỆN AUTO PLAY ---
            if self.auto_moves:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_move_time > 300: # Delay 300ms cho mỗi lượt di chuyển
                    next_move = self.auto_moves.pop(0)
                    self.apply_auto_move(next_move)
                    self.last_move_time = current_time

            self.theme.draw_background(self.screen)
            self.board_view.draw(self.screen, self.screen_width, self.screen_height, self.state)

            # Draw dragged card on top of everything else
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