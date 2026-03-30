# gui/menu_view.py
"""
Professional FreeCell menu.
Design: dark translucent centre card, large suit watermarks, elegant
golden dividers, polished buttons, pulsing border — no particle spam.
"""
import os
import math
import pygame
from .ui_theme import (
    C_TEXT_GOLD, C_TEXT_DIM, C_TEXT_PRIMARY,
    draw_button, _alpha_surf, _rounded_alpha_surf
)

BTN_MANUAL = (28, 100, 218)
BTN_AI     = (155, 78, 25)

GOLD       = (195, 155, 45)
GOLD_DIM   = (110, 82, 22)


class MenuView:
    def __init__(self, theme, width, height):
        self.theme  = theme
        self.width  = width
        self.height = height
        self.tick   = 0

        self.font_btn    = pygame.font.SysFont('Arial', 30, bold=True)
        self.font_suit_lg= pygame.font.SysFont('Arial', 160, bold=True)   # watermark
        self.font_suit_sm= pygame.font.SysFont('Arial', 36,  bold=True)   # corner glyphs
        self.font_ver    = pygame.font.SysFont('consolas', 13)
        self.font_footer = pygame.font.SysFont('consolas', 12)

        current_dir        = os.path.dirname(os.path.abspath(__file__))
        self.assets_folder = os.path.join(current_dir, "..", "assets", "backgrounds")
        self._load_logo()
        self._build_watermarks()

        self.rect_manual = None
        self.rect_ai     = None
        self.update_layout(width, height)

    # ── assets ─────────────────────────────────────────────────────────

    def _load_logo(self):
        TARGET_W = 400
        try:
            raw = pygame.image.load(
                os.path.join(self.assets_folder, "logo.png")).convert_alpha()
            w, h = raw.get_size()
            self.logo_img = pygame.transform.smoothscale(
                raw, (TARGET_W, int(TARGET_W * h / w)))
        except FileNotFoundError:
            self.logo_img = None

    def _build_watermarks(self):
        """Pre-render large translucent suit glyphs used as background art."""
        self._wm = {}
        pairs = [('♣', (30, 30, 30)), ('♥', (80, 10, 10)),
                 ('♠', (30, 30, 30)), ('♦', (80, 10, 10))]
        for sym, col in pairs:
            s = self.font_suit_lg.render(sym, True, col)
            s.set_alpha(55)
            self._wm[sym] = s

    # ── layout ─────────────────────────────────────────────────────────

    def update_layout(self, width, height):
        self.width  = width
        self.height = height
        btn_w, btn_h = 340, 60
        cx       = (width  - btn_w) // 2
        btn_top  = height // 2 + 10
        self.rect_manual = pygame.Rect(cx, btn_top,      btn_w, btn_h)
        self.rect_ai     = pygame.Rect(cx, btn_top + 80, btn_w, btn_h)

    # ── events ─────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect_manual and self.rect_manual.collidepoint(event.pos):
                return "MANUAL"
            if self.rect_ai and self.rect_ai.collidepoint(event.pos):
                return "AI"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "QUIT"
        return None

    # ── draw ───────────────────────────────────────────────────────────

    def draw(self, screen):
        self.tick += 1
        w, h = self.width, self.height
        cx   = w // 2

        self.theme.draw_background(screen)
        self._draw_vignette(screen, w, h)

        # ── Panel dimensions (needed for watermark positions) ────────
        panel_w, panel_h = 480, 440
        px = cx - panel_w // 2
        py = h  // 2 - panel_h // 2 - 20

        # ── Four suit watermarks inside panel corners ─────────────────
        wm_pairs = [
            ('♣', px + 20,            py + 30),
            ('♦', px + panel_w - 175, py + 30),
            ('♥', px + 20,            py + panel_h - 180),
            ('♠', px + panel_w - 175, py + panel_h - 180),
        ]
        for sym, sx, sy in wm_pairs:
            s = self._wm[sym]
            screen.blit(s, (sx, sy))

        # ── Centre panel (drawn on top of watermarks) ─────────────────
        # Lighter alpha = 130 so background/watermarks bleed through subtly
        panel_surf = _rounded_alpha_surf(panel_w, panel_h, (8, 8, 18, 130), radius=12)
        screen.blit(panel_surf, (px, py))

        # Pulsing gold border
        pulse_a = int(90 + 50 * math.sin(self.tick * 0.035))
        border_s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(border_s, (*GOLD, pulse_a),
                         border_s.get_rect(), width=2, border_radius=12)
        screen.blit(border_s, (px, py))

        # Inner subtle second border (static, darker)
        inner_s = pygame.Surface((panel_w - 8, panel_h - 8), pygame.SRCALPHA)
        pygame.draw.rect(inner_s, (*GOLD_DIM, 80),
                         inner_s.get_rect(), width=1, border_radius=10)
        screen.blit(inner_s, (px + 4, py + 4))

        # ── Corner suit glyphs (inside panel) ────────────────────────
        corners = [
            ('♣', px + 18,       py + 16,       (180, 180, 180)),
            ('♦', px + panel_w - 18, py + 16,   (200, 60, 60)),
            ('♠', px + 18,       py + panel_h - 16, (180, 180, 180)),
            ('♥', px + panel_w - 18, py + panel_h - 16, (200, 60, 60)),
        ]
        for sym, sx, sy, col in corners:
            gs = self.font_suit_sm.render(sym, True, col)
            gs.set_alpha(140)
            screen.blit(gs, gs.get_rect(center=(sx, sy)))

        # ── Logo ─────────────────────────────────────────────────────
        logo_cy = py + 120
        if self.logo_img:
            lr = self.logo_img.get_rect(center=(cx, logo_cy))
            screen.blit(self.logo_img, lr)
        else:
            fb = pygame.font.SysFont('Arial', 58, bold=True)
            t  = fb.render("FREECELL", True, C_TEXT_GOLD)
            screen.blit(t, t.get_rect(center=(cx, logo_cy)))

        # ── Buttons ──────────────────────────────────────────────────
        mouse = pygame.mouse.get_pos()
        draw_button(screen, self.rect_manual, "Manual Play",   BTN_MANUAL, self.font_btn, mouse)
        draw_button(screen, self.rect_ai,     "AI Auto Solve", BTN_AI,     self.font_btn, mouse)

        # ── Footer ───────────────────────────────────────────────────
        foot = self.font_footer.render(
            "ESC — Quit          BFS / DFS / UCS / A*", True, (65, 65, 65))
        screen.blit(foot, foot.get_rect(center=(cx, h - 20)))

    # ── helpers ────────────────────────────────────────────────────────

    def _draw_vignette(self, screen, w, h):
        vig = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(5, 0, -1):
            a  = int(55 * (1 - (i / 5) ** 1.6))
            rx = int(w * i / 5)
            ry = int(h * i / 5)
            vig.fill((0, 0, 0, a), pygame.Rect(0, 0, w, h))
            pygame.draw.ellipse(vig, (0, 0, 0, 0),
                                ((w - rx) // 2, (h - ry) // 2, rx, ry))
        screen.blit(vig, (0, 0))

    def _draw_ornament(self, screen, cx, y, arm):
        """Thin horizontal rule with small diamond centre."""
        surf = pygame.Surface((arm * 2, 2), pygame.SRCALPHA)
        for x in range(arm):
            a = int(160 * (1 - x / arm) ** 1.5)
            surf.set_at((arm - 1 - x, 0), (*GOLD, a))
            surf.set_at((arm - 1 - x, 1), (*GOLD_DIM, a // 2))
            surf.set_at((arm + x,     0), (*GOLD, a))
            surf.set_at((arm + x,     1), (*GOLD_DIM, a // 2))
        screen.blit(surf, (cx - arm, y - 1))
        # Centre dot
        pygame.draw.circle(screen, GOLD, (cx, y), 3)

    def _draw_divider(self, screen, cx, y, arm):
        """Decorative divider: fading line + diamond shape at centre."""
        surf = pygame.Surface((arm * 2, 1), pygame.SRCALPHA)
        for x in range(arm):
            a = int(180 * (1 - x / arm))
            surf.set_at((arm - 1 - x, 0), (*GOLD, a))
            surf.set_at((arm + x,     0), (*GOLD, a))
        screen.blit(surf, (cx - arm, y))
        # Diamond
        d = 5
        pts = [(cx, y - d), (cx + d, y), (cx, y + d), (cx - d, y)]
        pygame.draw.polygon(screen, GOLD, pts)


def _rounded_alpha_surf(w, h, color_rgba, radius=8):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, color_rgba, s.get_rect(), border_radius=radius)
    return s