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
        btn_y = height - 50
        btn_h, btn_w, gap = 30, 80, 5
        buttons = [
            ('BFS [B]', 'bfs', (50, 90, 160)),
            ('DFS [D]', 'dfs', (50, 140, 80)),
            ('UCS [U]', 'ucs', (140, 50, 160)),
            ('A*  [A]', 'astar', (180, 90, 40)),
            ('Reset[R]', 'reset', (130, 100, 40)),
            ('Menu', 'menu', (100, 60, 110)),
        ]
        sx = 20
        mouse = pygame.mouse.get_pos()
        for idx, (label, key, color) in enumerate(buttons):
            x = sx + idx * (btn_w + gap)
            rect = pygame.Rect(x, btn_y, btn_w, btn_h)
            self.btn_rects[key] = rect
            c = tuple(min(v + 30, 255) for v in color) if rect.collidepoint(mouse) else color
            pygame.draw.rect(screen, c, rect, border_radius=6)
            txt = self.font_btn.render(label, True, (255, 255, 255))
            screen.blit(txt, (x + (btn_w - txt.get_width()) // 2,
                              btn_y + (btn_h - txt.get_height()) // 2))

    def _draw_info_panel(self, screen, width, height):
        info = self.solver_info
        if not info:
            hint = "B=BFS D=DFS U=UCS A=A* R=Reset"
            txt = self.font.render(hint, True, (180, 180, 180))
            screen.blit(txt, (width // 2 - txt.get_width() // 2, height - 90))
            return
        pw = 185
        lines = []
        algo = info.get('algorithm', '?')
        solved = info.get('solved', False)
        status = info.get('status_text', '')
        lines.append((f"{algo}", (200, 200, 255)))
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
        px = width - pw - 5
        py = height - 65 - ph
        surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        surf.fill((10, 10, 20, 180))
        screen.blit(surf, (px, py))
        for i, (text, color) in enumerate(lines):
            txt = self.font.render(text, True, color)
            screen.blit(txt, (px + 4, py + 4 + i * 17))

    def _draw_playback_controls(self, screen, width, height):
        """Vẽ 5 nút tua ở chính giữa cạnh dưới màn hình"""
        btn_y = height - 60
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
            
            # Hover effect
            color = (80, 200, 80) if key == 'play' else (60, 120, 200)
            if rect.collidepoint(mouse): color = tuple(min(v + 30, 255) for v in color)
            
            pygame.draw.rect(screen, color, rect, border_radius=20) # Bo tròn như cái viên thuốc
            txt = self.font_big.render(label, True, (255, 255, 255))
            screen.blit(txt, (x + (btn_w - txt.get_width()) // 2, btn_y + (btn_h - txt.get_height()) // 2 - 5))

    def _draw_move_board(self, screen, width, height):
        """Vẽ lưới các move, tô màu xanh bước hiện tại"""
        if not self.player.move_strings: return

        cols = 10
        cell_w, cell_h = 45, 25
        start_x = (width - cols * cell_w) // 2
        start_y = height - 160 # Nằm trên các nút Playback
        
        # Nền mờ cho bảng
        rows = (len(self.player.move_strings) // cols) + 1
        bg_rect = pygame.Rect(start_x - 10, start_y - 10, cols * cell_w + 20, rows * cell_h + 20)
        surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        surf.fill((10, 10, 20, 180))
        screen.blit(surf, bg_rect.topleft)

        current_idx = self.player.get_current_move_index()

        for i, move_str in enumerate(self.player.move_strings):
            r = i // cols
            c = i % cols
            x = start_x + c * cell_w
            y = start_y + r * cell_h
            
            # Màu sắc: Xanh lục = Đang ở bước này, Trắng = Đã qua, Xám = Chưa tới
            if i == current_idx:
                color = (100, 255, 100) # Đèn sáng
            elif i < current_idx:
                color = (255, 255, 255) 
            else:
                color = (120, 120, 120) 

            txt = self.font_move.render(move_str, True, color)
            screen.blit(txt, (x + (cell_w - txt.get_width())//2, y))



    def _draw_overlay(self, screen, width, height, text, color):
        txt = self.font_big.render(text, True, color)
        x = width // 2 - txt.get_width() // 2
        y = height // 2 - txt.get_height() // 2
        bg = pygame.Surface((txt.get_width() + 50, txt.get_height() + 30), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 190))
        screen.blit(bg, (x - 25, y - 15))
        screen.blit(txt, (x, y))