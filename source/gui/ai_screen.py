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

        # Fonts
        self.font = pygame.font.SysFont('consolas', 13)
        self.font_btn = pygame.font.SysFont('consolas', 15)
        self.font_big = pygame.font.SysFont('consolas', 42, bold=True)

        self.btn_rects = {}

    def _reset(self):
        self.state = self.initial_state.clone()
        self.solver_info = None
        self.player.stop()
        self.player.move_log = []

    def _run_solver(self, algorithm):
        if self.solver.solving:
            return
        self._reset()
        self.solver.run(algorithm, self.initial_state, self._on_solved)

    def _on_solved(self, result):
        """Callback when solver finishes."""
        self.solver_info = result
        if result['solved']:
            self.state = self.initial_state.clone()
            # Kiểm tra xem có phải A* không để báo cho Player
            is_astar = (result.get('algorithm') == 'A*')
            self.player.start(self.initial_state, result['moves'], is_astar=is_astar)
            

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
            for key, rect in self.btn_rects.items():
                if rect.collidepoint(event.pos):
                    if key == 'bfs':
                        self._run_solver('bfs')
                    elif key == 'dfs':
                        self._run_solver('dfs')
                    elif key == 'ucs':
                        self._run_solver('ucs')
                    elif key == 'astar':
                        self._run_solver('astar')
                    elif key == 'reset':
                        self._reset()
                    elif key == 'menu':
                        self.solver.cancel()
                        return "MENU"
                    return None
        return None

    def update(self):
        if self.player.playing:
            self.player.update(self.state, self.board_view)

        # Update solver_info status
        if self.solver.solving:
            self.solver_info = self.solver.get_status()
            
            # THÊM DÒNG NÀY: 
            # Ép luồng UI ngủ 50ms (mili-giây) mỗi vòng lặp để nhường CPU cho A*
            pygame.time.wait(50)

    def draw(self, screen, width, height):
        self.theme.draw_background(screen)
        self.board_view.draw_board(screen, width, height, self.state)

        self.player.draw(screen, self.deck, self.board_view)

        self._draw_buttons(screen, width, height)
        self._draw_info_panel(screen, width, height)
        self._draw_move_log(screen, width, height)
        
        if self.solver.solving:
            self._draw_overlay(screen, width, height, "Solving...", (255, 255, 100))
        elif self.state.is_goal() and not self.player.playing:
            self._draw_overlay(screen, width, height, "SOLVED!", (0, 255, 100))

    # === BUTTONS ===

    def _draw_buttons(self, screen, width, height):
        btn_y = height - 55
        btn_h, btn_w, gap = 38, 90, 10

        buttons = [
            ('BFS [B]', 'bfs', (50, 90, 160)),
            ('DFS [D]', 'dfs', (50, 140, 80)),
            ('UCS [U]', 'ucs', (140, 50, 160)),
            ('A*  [A]', 'astar', (180, 90, 40)),
            ('Reset[R]', 'reset', (130, 100, 40)),
            ('Menu', 'menu', (100, 60, 110)),
        ]

        total = len(buttons) * btn_w + (len(buttons) - 1) * gap
        sx = (width - total) // 2
        mouse = pygame.mouse.get_pos()

        for idx, (label, key, color) in enumerate(buttons):
            x = sx + idx * (btn_w + gap)
            rect = pygame.Rect(x, btn_y, btn_w, btn_h)
            self.btn_rects[key] = rect

            c = tuple(min(v + 30, 255) for v in color) if rect.collidepoint(mouse) else color
            pygame.draw.rect(screen, c, rect, border_radius=6)
            pygame.draw.rect(screen, (180, 180, 200), rect, 1, 6)

            txt = self.font_btn.render(label, True, (255, 255, 255))
            screen.blit(txt, (x + (btn_w - txt.get_width()) // 2,
                              btn_y + (btn_h - txt.get_height()) // 2))

    # === INFO PANEL (bottom-right, narrow) ===

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

    # === MOVE LOG (top-left) ===

    def _draw_move_log(self, screen, width, height):
        log = self.player.move_log
        if not log:
            return

        max_lines = 5
        recent = log[-max_lines:]
        pw = 170
        ph = len(recent) * 16 + 20
        px = 5
        py = height - 65 - ph

        surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        surf.fill((10, 10, 20, 180))
        screen.blit(surf, (px, py))

        title = self.font.render("Moves", True, (150, 150, 150))
        screen.blit(title, (px + 4, py + 2))

        for i, text in enumerate(recent):
            color = (130, 220, 130) if 'Fnd' in text else (190, 190, 190)
            txt = self.font.render(text, True, color)
            screen.blit(txt, (px + 4, py + 16 + i * 16))

    # === OVERLAY ===

    def _draw_overlay(self, screen, width, height, text, color):
        txt = self.font_big.render(text, True, color)
        x = width // 2 - txt.get_width() // 2
        y = height // 2 - txt.get_height() // 2
        bg = pygame.Surface((txt.get_width() + 50, txt.get_height() + 30), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 190))
        screen.blit(bg, (x - 25, y - 15))
        screen.blit(txt, (x, y))