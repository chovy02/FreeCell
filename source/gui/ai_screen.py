# gui/ai_screen.py
import pygame
from .board_view import BoardView
from .solver_runner import SolverRunner
from .solution_player import SolutionPlayer
from core.state import State


class AIScreen:
    def __init__(self, deck, theme, state):
        self.deck = deck
        self.theme = theme
        self.state = state
        self.initial_state = state.clone()

        self.board_view = BoardView(deck, theme)
        self.solver = SolverRunner()
        self.player = SolutionPlayer()

        self.solver_info = None

        self.font = pygame.font.SysFont('consolas', 13)
        self.font_btn = pygame.font.SysFont('consolas', 15)
        self.font_big = pygame.font.SysFont('consolas', 42, bold=True)
        self.font_move = pygame.font.SysFont('consolas', 16, bold=True) # Font cho bảng move
        self.font_ctrl = pygame.font.SysFont('arial', 20, bold=True)

        self.btn_rects = {}
        self.playback_rects = {} # Quản lý riêng 5 nút Playback

    def _reset(self):
        self.state = self.initial_state.clone()
        self.solver_info = None
        self.player.stop()

    def _run_solver(self, algorithm):
        if self.solver.solving:
            return
        self._reset()
        self.solver.run(algorithm, self.initial_state, self._on_solved)

    def _on_solved(self, result):
        self.solver_info = result
        if result['solved']:
            self.state = self.initial_state.clone()
            self.player.start(self.initial_state, result['moves'])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.solver.cancel()
                return "MENU"
            elif event.key == pygame.K_b:
                self._run_solver('bfs')
            elif event.key == pygame.K_d:
                self._run_solver('dfs')
            elif event.key == pygame.K_u:
                self._run_solver('ucs')
            elif event.key == pygame.K_a:
                self._run_solver('astar')
            elif event.key == pygame.K_r:
                self._reset()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.playback_rects.items():
                if rect.collidepoint(event.pos):
                    if key == 'start': self.player.fast_rewind_start()
                    elif key == 'back': self.player.step_backward()
                    elif key == 'play': self.player.toggle_play()
                    elif key == 'next': self.player.step_forward()
                    elif key == 'end': self.player.fast_forward_end()
                    return None
                
            for key, rect in self.btn_rects.items():
                if rect.collidepoint(event.pos):
                    if key in ('bfs', 'dfs', 'ucs', 'astar'):
                        self._run_solver(key)
                    elif key == 'reset':
                        self._reset()
                    elif key == 'menu':
                        self.solver.cancel()
                        return "MENU"
                    return None
        return None

    def update(self):
        self.player.update(self.state, self.board_view)

        if self.solver.solving:
            self.solver_info = self.solver.get_status()

    def draw(self, screen, width, height):
        self.theme.draw_background(screen)
        self.board_view.draw_board(screen, width, height, self.state)

        self.player.draw(screen, self.deck, self.board_view)
        self._draw_buttons(screen, width, height)
        self._draw_info_panel(screen, width, height)

        if self.solver.solving:
            self._draw_overlay(screen, width, height, "Solving...", (255, 255, 100))
        elif self.state.is_goal() and not self.player.playing:
            self._draw_overlay(screen, width, height, "SOLVED!", (0, 255, 100))

        # When solved, draw the playback buttons
        if self.solver_info and self.solver_info.get('solved', False):
            self._draw_playback_controls(screen, width, height)
            self._draw_move_board(screen, width, height)

    def _draw_buttons(self, screen, width, height):
        # Đặt các nút thành lưới 2 hàng x 3 cột ở góc dưới bên trái
        btn_w, btn_h, gap = 75, 30, 6
        sx = 20
        sy = height - 85
        buttons = [
            ('BFS', 'bfs', (50, 90, 160)),
            ('DFS', 'dfs', (50, 140, 80)),
            ('UCS', 'ucs', (140, 50, 160)),
            ('A*', 'astar', (180, 90, 40)),
            ('Reset', 'reset', (130, 100, 40)),
            ('Menu', 'menu', (100, 60, 110)),
        ]
        mouse = pygame.mouse.get_pos()
        for idx, (label, key, color) in enumerate(buttons):
            row = idx // 3
            col = idx % 3
            x = sx + col * (btn_w + gap)
            y = sy + row * (btn_h + gap)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.btn_rects[key] = rect
            
            c = tuple(min(v + 30, 255) for v in color) if rect.collidepoint(mouse) else color
            pygame.draw.rect(screen, c, rect, border_radius=6)
            txt = self.font_btn.render(label, True, (255, 255, 255))
            screen.blit(txt, (x + (btn_w - txt.get_width()) // 2,
                              y + (btn_h - txt.get_height()) // 2))

    def _draw_info_panel(self, screen, width, height):
        info = self.solver_info
        if not info:
            hint = "B=BFS D=DFS U=UCS A=A* R=Reset"
            txt = self.font.render(hint, True, (180, 180, 180))
            screen.blit(txt, (width - txt.get_width() - 20, height - 35))
            return
            
        pw = 185
        lines = []
        algo = info.get('algorithm', '?')
        solved = info.get('solved', False)
        status = info.get('status_text', '')
        
        lines.append((f"{algo.upper()}", (200, 200, 255)))
        if status:
            lines.append((status, (255, 200, 80)))
        elif solved:
            lines.append(("SOLVED", (0, 220, 80)))
        else:
            lines.append(("NOT FOUND", (220, 60, 60)))
            
        lines.append((f"{info.get('time',0):.2f}s", (200, 200, 200)))
        lines.append((f"Memory:{info.get('memory_mb',0):.0f}MB", (200, 200, 200)))
        lines.append((f"Expanded:{info.get('expanded',0):,}", (200, 200, 200)))
        lines.append((f"Moves:{info.get('solution_length',0)}", (220, 220, 130)))
        
        if self.player.playing:
            p = self.player.get_info()
            lines.append((f"Step:{p['current_step']}/{p['total_steps']}", (100, 200, 255)))
            
        ph = len(lines) * 17 + 8
        px = width - pw - 20 # Canh lề phải
        py = height - ph - 15 # Canh lề dưới
        
        surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        surf.fill((10, 10, 20, 180))
        screen.blit(surf, (px, py))
        
        for i, (text, color) in enumerate(lines):
            txt = self.font.render(text, True, color)
            screen.blit(txt, (px + 6, py + 4 + i * 17))

    def _draw_playback_controls(self, screen, width, height):
        btn_y = height - 55
        btn_h, btn_w, gap = 45, 60, 15
        play_label = "||" if self.player.target_step > self.player.current_step else "►"
        buttons = [
            ('|<', 'start'), ('<', 'back'), 
            (play_label, 'play'), 
            ('>', 'next'), ('>|', 'end')
        ]
        
        total = len(buttons) * btn_w + (len(buttons) - 1) * gap
        sx = (width - total) // 2
        mouse = pygame.mouse.get_pos()

        for idx, (label, key) in enumerate(buttons):
            x = sx + idx * (btn_w + gap)
            rect = pygame.Rect(x, btn_y, btn_w, btn_h)
            self.playback_rects[key] = rect
            
            is_hover = rect.collidepoint(mouse)
            base_color = (46, 204, 113) if key == 'play' else (52, 152, 219)
            
            # Hover lún xuống tương tự các nút trên
            if is_hover:
                draw_color = tuple(min(255, c + 40) for c in base_color)
                y_offset = 2
            else:
                draw_color = base_color
                y_offset = 0
            # Bóng đổ

            # Nút chính và viền
            main_rect = pygame.Rect(x, btn_y + y_offset, btn_w, btn_h)
            pygame.draw.rect(screen, draw_color, main_rect, border_radius=6)
            #pygame.draw.rect(screen, (255, 255, 255), main_rect, width=2, border_radius=20)

            # Text 
            txt = self.font_ctrl.render(label, True, (255, 255, 255))
            
            text_x = x + (btn_w - txt.get_width()) // 2
            text_y = btn_y + y_offset + (btn_h - txt.get_height()) // 2 - 2
            
            screen.blit(txt, (text_x, text_y))

    def _draw_move_board(self, screen, width, height):
        # Thiết kế dạng Sliding Window: Chỉ hiện 1 dòng hiển thị khoảng 9 bước gần nhất
        if not self.player.move_strings: return

        visible_moves = 9 # Số lượng bước hiển thị
        cell_w, cell_h = 45, 25
        start_x = (width - visible_moves * cell_w) // 2
        start_y = height - 95 # Nằm ngay trên cụm nút Playback
        
        current_idx = self.player.get_current_move_index()
        total_moves = len(self.player.move_strings)
        
        # Tính toán để focus vào bước hiện tại
        start_idx = max(0, current_idx - visible_moves // 2)
        end_idx = min(total_moves, start_idx + visible_moves)
        if end_idx - start_idx < visible_moves:
            start_idx = max(0, end_idx - visible_moves)

        # Nền mờ cho bảng
        bg_rect = pygame.Rect(start_x - 10, start_y - 5, visible_moves * cell_w + 20, cell_h + 10)
        surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        surf.fill((10, 10, 20, 180))
        screen.blit(surf, bg_rect.topleft)

        for i in range(start_idx, end_idx):
            move_str = self.player.move_strings[i]
            c = i - start_idx
            x = start_x + c * cell_w
            y = start_y
            
            # Màu sắc: Xanh lục = Đang ở bước này, Trắng = Đã qua, Xám = Chưa tới
            if i == current_idx: color = (100, 255, 100)
            elif i < current_idx: color = (220, 220, 220) 
            else: color = (120, 120, 120) 

            txt = self.font_move.render(move_str, True, color)
            screen.blit(txt, (x + (cell_w - txt.get_width())//2, y + (cell_h - txt.get_height())//2))
            
            # Viền báo hiệu bước hiện tại
            if i == current_idx:
                pygame.draw.rect(screen, (80, 200, 80), (x, y, cell_w, cell_h), 2, border_radius=4)


    def _draw_overlay(self, screen, width, height, text, color):
        txt = self.font_big.render(text, True, color)
        x = width // 2 - txt.get_width() // 2
        y = height // 2 - txt.get_height() // 2
        bg = pygame.Surface((txt.get_width() + 50, txt.get_height() + 30), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 190))
        screen.blit(bg, (x - 25, y - 15))
        screen.blit(txt, (x, y))