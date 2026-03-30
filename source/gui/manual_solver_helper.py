# gui/manual_solver_helper.py
import pygame
import os
from .solver_runner import SolverRunner
from .solution_player import SolutionPlayer
from .ui_theme import (
    C_PANEL_BORDER, C_TEXT_PRIMARY, C_TEXT_DIM, C_TEXT_GOLD, C_TEXT_GREEN,
    C_TEXT_RED, C_TEXT_BLUE, C_TEXT_ORANGE, C_TEXT_PURPLE,
    draw_panel, draw_solving_overlay, draw_win_overlay
)

ALGO_COLORS = {
    'BFS':   C_TEXT_BLUE,
    'DFS':   C_TEXT_GREEN,
    'UCS':   C_TEXT_PURPLE,
    'A*':    C_TEXT_ORANGE,
}

class ManualSolverHelper:
    def __init__(self, manual_screen):
        self.ms = manual_screen
        self.solver = SolverRunner()
        self.player = SolutionPlayer()
        self.solver_info = None
        
        self.active = False
        self.snapshot_state = None
        
        self.font_stat = pygame.font.SysFont('consolas', 12)
        self.font_head = pygame.font.SysFont('consolas', 13, bold=True)
        self.font_move = pygame.font.SysFont('consolas', 15, bold=True)
        self.font_big  = pygame.font.SysFont('consolas', 46, bold=True)
        
        self.playback_rects = {}
        self.btn_imgs = {}
        self._load_button_images()

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
            except Exception:
                self.btn_imgs[key] = None

    def handle_event(self, event):
        dealing = self.ms._deal_anim and not self.ms._deal_anim.done
        if dealing or self.ms.animator.is_animating():
            return False

        if self.active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.cancel()
                return True 
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self.playback_rects.items():
                    if rect.collidepoint(event.pos):
                        if key == 'start': self.player.fast_rewind_start()
                        elif key == 'back': self.player.step_backward()
                        elif key == 'play': self.player.toggle_play()
                        elif key == 'next': self.player.step_forward()
                        elif key == 'end':  self.player.fast_forward_end()
                        return True
                return True  # Block all clicks when helper is active

        if not self.active and event.type == pygame.KEYDOWN:
            k = event.key
            if k == pygame.K_b: self._run_solver('bfs'); return True
            elif k == pygame.K_d: self._run_solver('dfs'); return True
            elif k == pygame.K_u: self._run_solver('ucs'); return True
            elif k == pygame.K_a: self._run_solver('astar'); return True
            
        return False

    def _run_solver(self, algorithm):
        if self.solver.solving: return
        self.active = True
        self.snapshot_state = self.ms.state.clone()
        self.solver.run(algorithm, self.snapshot_state, self._on_solved)

    def _on_solved(self, result):
        self.solver_info = result
        if result['solved']:
            self.ms.state = self.snapshot_state.clone()
            self.player.start(self.snapshot_state, result['moves'])

    def cancel(self):
        self.solver.cancel()
        self.player.stop()
        self.active = False
        self.solver_info = None
        if self.snapshot_state:
            self.ms.state = self.snapshot_state.clone()

    def update(self):
        if not self.active: return
        self.player.update(self.ms.state, self.ms.board_view)
        if self.solver.solving:
            self.solver_info = self.solver.get_status()

    # ─── DRAW — takes over entire screen like AI screen ────────────────

    def draw(self, screen, width, height):
        if not self.active:
            return

        self.update()

        # 1. Vẽ lại toàn bộ màn hình (background + board) — không dùng dim overlay
        self.ms.theme.draw_background(screen)
        self.ms.board_view.draw_board(screen, width, height, self.ms.state)

        # 2. Vẽ animation thẻ bài đang bay (từ SolutionPlayer)
        if self.solver_info and self.solver_info.get('solved'):
            self.player.draw(screen, self.ms.deck, self.ms.board_view)

        # 3. Info Panel — luôn hiển thị khi có solver_info
        self._draw_info_panel(screen, width, height)

        # 4. Overlay trạng thái
        if self.solver.solving:
            draw_solving_overlay(screen, width, height, "Solving…", self.font_big)
        else:
            if self.solver_info and self.solver_info.get('solved'):
                # Playback controls + Move board
                self._draw_playback_controls(screen, width, height)
                self._draw_move_board(screen, width, height)

                # Win overlay khi đã giải xong và không còn đang play
                if self.ms.state.is_goal() and not self.player.playing:
                    draw_win_overlay(screen, width, height, "SOLVED!", self.font_big)

        # 5. Gợi ý thoát — đặt ở vị trí không bị đè
        hint = self.font_stat.render(
            "Press ESC to exit AI Helper & continue playing", True, C_TEXT_DIM)
        screen.blit(hint, hint.get_rect(center=(width // 2, height - 65)))

    # ─── INFO PANEL (bottom-right) ────────────────────────────────────

    def _draw_info_panel(self, screen, width, height):
        info = self.solver_info
        if not info: return

        algo    = info.get('algorithm', '?').upper().replace('STAR', '*')
        solved  = info.get('solved', False)
        status  = info.get('status_text', '')
        t       = info.get('time', 0)
        mem     = info.get('memory_mb', 0)
        exp     = info.get('expanded', 0)
        sol_len = info.get('solution_length', 0)

        algo_col    = ALGO_COLORS.get(algo, C_TEXT_GOLD)
        status_text = status or ("SOLVED" if solved else "NO SOLUTION")
        status_col  = C_TEXT_GREEN if solved else C_TEXT_RED
        if status: 
            status_col = C_TEXT_GOLD

        pw, row_h, rows = 192, 18, 5
        ph   = 32 + rows * row_h + 8      
        px   = width - pw - 16
        py   = height - ph - 16

        draw_panel(screen, px, py, pw, ph, alpha=210,
                   title=f"  Helper: {algo}", title_font=self.font_head,
                   title_color=algo_col)

        ry = py + 36    
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

        pygame.draw.line(screen, C_PANEL_BORDER, (px + 6, ry), (px + pw - 6, ry))

    # ─── PLAYBACK CONTROLS (icon buttons, right side) ──────────────────

    def _draw_playback_controls(self, screen, width, height):
        btn_w, btn_h, gap = 56, 56, 6
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

        pad = 10
        draw_panel(screen, x_left - pad, y_top - pad,
                   cluster_w + pad * 2, cluster_h + pad * 2, alpha=140)

        mouse = pygame.mouse.get_pos()
        for img, key, x, y in btns:
            if not img: continue
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.playback_rects[key] = rect
            is_hov  = rect.collidepoint(mouse)
            y_off   = 2 if is_hov else 0

            if is_hov:
                glow = pygame.Surface((btn_w + 8, btn_h + 8), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 255, 255, 35),
                                   (btn_w // 2 + 4, btn_h // 2 + 4), btn_w // 2 + 2)
                screen.blit(glow, (x - 4, y + y_off - 4))
            screen.blit(img, (x, y + y_off))

    # ─── MOVE BOARD (pill chips along bottom center) ────────────────────

    def _draw_move_board(self, screen, width, height):
        if not self.player.move_strings: return

        VISIBLE, chip_w, chip_h, chip_gap = 9, 48, 28, 4
        total_w   = VISIBLE * chip_w + (VISIBLE - 1) * chip_gap
        sx        = (width - total_w) // 2
        sy        = height - chip_h - 10

        cur_idx   = self.player.get_current_move_index()
        total_mv  = len(self.player.move_strings)

        start_idx = max(0, cur_idx - VISIBLE // 2)
        end_idx   = min(total_mv, start_idx + VISIBLE)
        if end_idx - start_idx < VISIBLE:
            start_idx = max(0, end_idx - VISIBLE)

        strip_h = chip_h + 14
        strip = pygame.Surface((total_w + 24, strip_h), pygame.SRCALPHA)
        pygame.draw.rect(strip, (8, 12, 22, 165), strip.get_rect(), border_radius=10)
        pygame.draw.rect(strip, (*C_PANEL_BORDER, 120), strip.get_rect(),
                         width=1, border_radius=10)
        screen.blit(strip, (sx - 12, sy - 7))

        for i in range(start_idx, end_idx):
            mv_str = self.player.move_strings[i]
            c      = i - start_idx
            cx     = sx + c * (chip_w + chip_gap)

            is_current, is_done = (i == cur_idx), (i < cur_idx)

            if is_current:
                chip_color, border_c, text_c = (35, 130, 75), C_TEXT_GREEN, (200, 255, 215)
            elif is_done:
                chip_color, border_c, text_c = (30, 40, 58), C_PANEL_BORDER, (180, 185, 195)
            else:
                chip_color, border_c, text_c = (18, 24, 36), (35, 45, 62), (90, 100, 115)

            chip_rect = pygame.Rect(cx, sy, chip_w, chip_h)

            chip_surf = pygame.Surface((chip_w, chip_h), pygame.SRCALPHA)
            pygame.draw.rect(chip_surf, (*chip_color, 230), chip_surf.get_rect(),
                             border_radius=6)
            screen.blit(chip_surf, chip_rect.topleft)

            pygame.draw.rect(screen, border_c, chip_rect, width=1, border_radius=6)

            if is_current:
                glow = pygame.Surface((chip_w + 4, chip_h + 4), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*C_TEXT_GREEN, 55), glow.get_rect(),
                                 width=2, border_radius=8)
                screen.blit(glow, (cx - 2, sy - 2))

            txt = self.font_move.render(mv_str, True, text_c)
            screen.blit(txt, txt.get_rect(center=chip_rect.center))

        if total_mv > 0:
            prog = f"{min(cur_idx, total_mv)}/{total_mv}"
            prog_s = self.font_stat.render(prog, True, C_TEXT_DIM)
            screen.blit(prog_s, (sx + total_w + 18,
                                 sy + chip_h // 2 - prog_s.get_height() // 2))