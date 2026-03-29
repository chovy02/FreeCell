# gui/ai_screen.py
import pygame
import os
from .board_view import BoardView
from .solver_runner import SolverRunner
from .solution_player import SolutionPlayer
from .dealing_animator import DealingAnimator
from core.state import State
from .ui_theme import (
    BTN, C_PANEL_BG, C_PANEL_BORDER, C_PANEL_BORDER_HI,
    C_TEXT_PRIMARY, C_TEXT_DIM, C_TEXT_GOLD, C_TEXT_GREEN,
    C_TEXT_RED, C_TEXT_BLUE, C_TEXT_ORANGE, C_TEXT_PURPLE,
    draw_button, draw_panel, draw_win_overlay, draw_solving_overlay,
    _lighten, _alpha_surf, _rounded_alpha_surf
)


# ─── Colour aliases for algorithm tags ───────────────────────────────
ALGO_COLORS = {
    'BFS':   C_TEXT_BLUE,
    'DFS':   C_TEXT_GREEN,
    'UCS':   C_TEXT_PURPLE,
    'A*':    C_TEXT_ORANGE,
}


class AIScreen:
    def __init__(self, deck, theme, state, screen_w=1280, screen_h=720):
        self.deck  = deck
        self.theme = theme
        self.state = state
        self.initial_state = state.clone()

        self.board_view  = BoardView(deck, theme)
        self.solver      = SolverRunner()
        self.player      = SolutionPlayer()
        self.solver_info = None

        self.font      = pygame.font.SysFont('consolas', 13)
        self.font_btn  = pygame.font.SysFont('consolas', 14, bold=True)
        self.font_big  = pygame.font.SysFont('consolas', 46, bold=True)
        self.font_move = pygame.font.SysFont('consolas', 15, bold=True)
        self.font_stat = pygame.font.SysFont('consolas', 12)
        self.font_head = pygame.font.SysFont('consolas', 13, bold=True)
        self.font_tag  = pygame.font.SysFont('consolas', 18, bold=True)

        self.btn_rects      = {}
        self.playback_rects = {}
        self.btn_imgs       = {}
        self._load_button_images()

        # Deal animation
        self._screen_w    = screen_w
        self._screen_h    = screen_h
        self._deal_anim   = None
        self._deal_inited = False

    # ─── ASSETS ────────────────────────────────────────────────────────

    def _load_button_images(self):
        current_dir  = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        btn_dir      = os.path.join(project_root, 'assets', 'buttons')
        btn_size     = (56, 56)
        files = {
            'start': 'fast_rewind.png',
            'back':  'step_backward.png',
            'play':  'continue.png',
            'pause': 'pause.png',
            'next':  'step_forward.png',
            'end':   'fast_forward.png',
        }
        for key, filename in files.items():
            path = os.path.join(btn_dir, filename)
            try:
                img = pygame.image.load(path).convert_alpha()
                self.btn_imgs[key] = pygame.transform.smoothscale(img, btn_size)
            except Exception as e:
                print(f"Could not load {filename}: {e}")
                self.btn_imgs[key] = None

    # ─── ACTIONS ───────────────────────────────────────────────────────

    def _reset(self):
        self.state       = self.initial_state.clone()
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

    # ─── EVENTS ────────────────────────────────────────────────────────

    def handle_event(self, event):
        # Skip deal with any click / space
        if self._deal_anim and not self._deal_anim.done:
            if event.type == pygame.MOUSEBUTTONDOWN or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                self._deal_anim.skip()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.solver.cancel()
                return "MENU"
            return None

        if event.type == pygame.KEYDOWN:
            k = event.key
            if k == pygame.K_ESCAPE:                    return "MENU"
            elif k == pygame.K_b: self._run_solver('bfs')
            elif k == pygame.K_d: self._run_solver('dfs')
            elif k == pygame.K_u: self._run_solver('ucs')
            elif k == pygame.K_a: self._run_solver('astar')
            elif k == pygame.K_r: self._reset()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.playback_rects.items():
                if rect.collidepoint(event.pos):
                    if key == 'start': self.player.fast_rewind_start()
                    elif key == 'back': self.player.step_backward()
                    elif key == 'play': self.player.toggle_play()
                    elif key == 'next': self.player.step_forward()
                    elif key == 'end':  self.player.fast_forward_end()
                    return None

            for key, rect in self.btn_rects.items():
                if rect.collidepoint(event.pos):
                    if key in ('bfs', 'dfs', 'ucs', 'astar'):
                        self._run_solver(key)
                    elif key == 'reset': self._reset()
                    elif key == 'menu':
                        self.solver.cancel()
                        return "MENU"
                    return None
        return None

    def update(self):
        self.player.update(self.state, self.board_view)
        if self.solver.solving:
            self.solver_info = self.solver.get_status()

    # ─── DRAW ──────────────────────────────────────────────────────────

    def draw(self, screen, width, height):
        self.theme.draw_background(screen)

        # ── First frame: init layout then create deal animator ──
        if not self._deal_inited:
            self.board_view.draw_board(screen, width, height, self.state)
            self._deal_inited = True
            self._deal_anim = DealingAnimator(self.deck, self.state, self.board_view, width, height)
            self.theme.draw_background(screen)

        # ── Choose which state to render ──
        dealing = self._deal_anim and not self._deal_anim.done
        if dealing:
            display_state = self._deal_anim.get_display_state()
            self._deal_anim.update()
        else:
            display_state = self.state

        self.board_view.draw_board(screen, width, height, display_state)

        if not dealing:
            self.player.draw(screen, self.deck, self.board_view)

        self._draw_buttons(screen, width, height)
        self._draw_info_panel(screen, width, height)

        if not dealing:
            if self.solver.solving:
                draw_solving_overlay(screen, width, height, "Solving…", self.font_big)
            elif self.state.is_goal() and not self.player.playing:
                draw_win_overlay(screen, width, height, "SOLVED!", self.font_big)

            if self.solver_info and self.solver_info.get('solved'):
                self._draw_playback_controls(screen, width, height)
                self._draw_move_board(screen, width, height)

        # Deal animation overlay
        if dealing:
            self._deal_anim.draw(screen)
            hint = self.font_stat.render("Click or Space to skip", True, (140, 140, 140))
            screen.blit(hint, hint.get_rect(center=(width // 2, height - 50)))

    # ─── SOLVER BUTTONS (bottom-left 2×3 grid) ────────────────────────

    def _draw_buttons(self, screen, width, height):
        btn_w, btn_h, gap = 78, 34, 6
        sx = 20
        sy = height - 82

        buttons = [
            ('BFS',   'bfs',   BTN['bfs']),
            ('DFS',   'dfs',   BTN['dfs']),
            ('UCS',   'ucs',   BTN['ucs']),
            ('A*',    'astar', BTN['astar']),
            ('Reset', 'reset', BTN['reset']),
            ('Menu',  'menu',  BTN['menu']),
        ]

        total_w = 3 * btn_w + 2 * gap + 16
        total_h = 2 * btn_h + gap + 16
        draw_panel(screen, sx - 8, sy - 8, total_w, total_h, alpha=155)

        mouse = pygame.mouse.get_pos()
        for idx, (label, key, color) in enumerate(buttons):
            row = idx // 3
            col = idx % 3
            x   = sx + col * (btn_w + gap)
            y   = sy + row * (btn_h + gap)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.btn_rects[key] = rect
            draw_button(screen, rect, label, color, self.font_btn, mouse)

    # ─── INFO PANEL (bottom-right) ─────────────────────────────────────

    def _draw_info_panel(self, screen, width, height):
        info = self.solver_info

        if not info:
            # Minimal hint strip
            hint = self.font_stat.render("B=BFS  D=DFS  U=UCS  A=A*  R=Reset", True, C_TEXT_DIM)
            screen.blit(hint, (width - hint.get_width() - 18, height - 30))
            return

        # ── determine content ──
        algo    = info.get('algorithm', '?').upper().replace('STAR', '*')
        solved  = info.get('solved', False)
        status  = info.get('status_text', '')
        t       = info.get('time', 0)
        mem     = info.get('memory_mb', 0)
        exp     = info.get('expanded', 0)
        sol_len = info.get('solution_length', 0)

        algo_col    = ALGO_COLORS.get(algo, C_TEXT_GOLD)
        status_text = status or ("SOLVED" if solved else "NOT FOUND")
        status_col  = C_TEXT_GREEN if solved else C_TEXT_RED
        if status:
            status_col = C_TEXT_GOLD

        pl_step = pl_total = 0
        if self.player.playing:
            pl_info = self.player.get_info()
            pl_step = pl_info['current_step']
            pl_total = pl_info['total_steps']

        # ── panel sizing ──
        pw = 192
        row_h = 18
        rows = 5
        ph   = 32 + rows * row_h + 8      # title bar 32px + rows + padding
        px   = width - pw - 16
        py   = height - ph - 16

        draw_panel(screen, px, py, pw, ph, alpha=210,
                   title=f"  {algo}", title_font=self.font_head,
                   title_color=algo_col)

        # ── rows ──
        ry = py + 36    # start below title bar

        def stat_row(label, value, val_color=C_TEXT_PRIMARY):
            nonlocal ry
            lbl_s = self.font_stat.render(label, True, C_TEXT_DIM)
            val_s = self.font_stat.render(str(value), True, val_color)
            screen.blit(lbl_s, (px + 10, ry))
            screen.blit(val_s, (px + pw - val_s.get_width() - 10, ry))
            ry += row_h

        stat_row("Status",   status_text,          status_col)
        stat_row("Time",     f"{t:.2f}s",           C_TEXT_PRIMARY)
        stat_row("Memory",   f"{mem:.0f} MB",        C_TEXT_PRIMARY)
        stat_row("Expanded", f"{exp:,}",             C_TEXT_BLUE)
        stat_row("Moves",    str(sol_len),           C_TEXT_GOLD)

        # Divider
        pygame.draw.line(screen, C_PANEL_BORDER, (px + 6, ry), (px + pw - 6, ry))
        ry += 5

    # ─── PLAYBACK CONTROLS (icon buttons, right side) ──────────────────

    def _draw_playback_controls(self, screen, width, height):
        btn_w, btn_h = 56, 56
        gap          = 6

        cluster_w = btn_w * 2 + gap
        cluster_h = btn_h * 3 + gap * 2
        rm        = 12
        x_left    = width - rm - cluster_w
        x_right   = x_left + btn_w + gap
        x_center  = x_left + (cluster_w - btn_w) // 2
        y_top     = (height - cluster_h) // 2
        y_mid     = y_top + btn_h + gap
        y_bot     = y_mid + btn_h + gap

        is_playing = self.player.target_step > self.player.current_step
        play_icon  = self.btn_imgs.get('pause' if is_playing else 'play')

        btns = [
            (play_icon,                    'play',  x_center, y_top),
            (self.btn_imgs.get('back'),    'back',  x_left,   y_mid),
            (self.btn_imgs.get('next'),    'next',  x_right,  y_mid),
            (self.btn_imgs.get('start'),   'start', x_left,   y_bot),
            (self.btn_imgs.get('end'),     'end',   x_right,  y_bot),
        ]

        # Semi-transparent backing panel
        pad = 10
        draw_panel(screen, x_left - pad, y_top - pad,
                   cluster_w + pad * 2, cluster_h + pad * 2, alpha=140)

        mouse = pygame.mouse.get_pos()
        for img, key, x, y in btns:
            if not img:
                continue
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.playback_rects[key] = rect
            is_hov  = rect.collidepoint(mouse)
            y_off   = 2 if is_hov else 0

            if is_hov:
                # Subtle circular glow
                glow = pygame.Surface((btn_w + 8, btn_h + 8), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 255, 255, 35),
                                   (btn_w // 2 + 4, btn_h // 2 + 4), btn_w // 2 + 2)
                screen.blit(glow, (x - 4, y + y_off - 4))

            screen.blit(img, (x, y + y_off))

    # ─── MOVE BOARD (pill chips along bottom center) ────────────────────

    def _draw_move_board(self, screen, width, height):
        if not self.player.move_strings:
            return

        VISIBLE   = 9
        chip_w    = 48
        chip_h    = 28
        chip_gap  = 4
        total_w   = VISIBLE * chip_w + (VISIBLE - 1) * chip_gap
        sx        = (width - total_w) // 2
        sy        = height - chip_h - 10

        cur_idx   = self.player.get_current_move_index()
        total_mv  = len(self.player.move_strings)

        # Window centering
        start_idx = max(0, cur_idx - VISIBLE // 2)
        end_idx   = min(total_mv, start_idx + VISIBLE)
        if end_idx - start_idx < VISIBLE:
            start_idx = max(0, end_idx - VISIBLE)

        # Backing strip — transparent
        strip_h = chip_h + 14
        strip   = pygame.Surface((total_w + 24, strip_h), pygame.SRCALPHA)
        pygame.draw.rect(strip, (8, 12, 22, 70), strip.get_rect(), border_radius=10)
        pygame.draw.rect(strip, (*C_PANEL_BORDER, 40), strip.get_rect(),
                         width=1, border_radius=10)
        screen.blit(strip, (sx - 12, sy - 7))

        for i in range(start_idx, end_idx):
            mv_str = self.player.move_strings[i]
            c      = i - start_idx
            cx     = sx + c * (chip_w + chip_gap)

            is_current = (i == cur_idx)
            is_done    = (i < cur_idx)

            if is_current:
                chip_color = (35, 130, 75)
                border_c   = C_TEXT_GREEN
                text_c     = (200, 255, 215)
                chip_alpha = 200
            elif is_done:
                chip_color = (30, 40, 58)
                border_c   = C_PANEL_BORDER
                text_c     = (180, 185, 195)
                chip_alpha = 120
            else:
                chip_color = (18, 24, 36)
                border_c   = (35, 45, 62)
                text_c     = (90, 100, 115)
                chip_alpha = 100

            chip_rect = pygame.Rect(cx, sy, chip_w, chip_h)

            # Chip fill — transparent
            chip_surf = pygame.Surface((chip_w, chip_h), pygame.SRCALPHA)
            pygame.draw.rect(chip_surf, (*chip_color, chip_alpha), chip_surf.get_rect(), border_radius=6)
            screen.blit(chip_surf, chip_rect.topleft)

            # Chip border
            border_surf = pygame.Surface((chip_w, chip_h), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, (*border_c, chip_alpha), border_surf.get_rect(), width=1, border_radius=6)
            screen.blit(border_surf, chip_rect.topleft)

            # Glow for current chip
            if is_current:
                glow = pygame.Surface((chip_w + 4, chip_h + 4), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*C_TEXT_GREEN, 40),
                                 glow.get_rect(), width=2, border_radius=8)
                screen.blit(glow, (cx - 2, sy - 2))

            # Move label
            txt = self.font_move.render(mv_str, True, text_c)
            screen.blit(txt, txt.get_rect(center=chip_rect.center))

        # Step counter (small, right of strip)
        if total_mv > 0:
            prog = f"{min(cur_idx, total_mv)}/{total_mv}"
            prog_s = self.font_stat.render(prog, True, C_TEXT_DIM)
            screen.blit(prog_s, (sx + total_w + 18, sy + chip_h // 2 - prog_s.get_height() // 2))