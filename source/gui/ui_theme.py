# gui/ui_theme.py
"""
Shared UI drawing utilities — professional FreeCell visual theme.
Consistent colour palette, polished buttons, animated notifications, info panels.
"""
import pygame

# --- Colour palette ---

C_PANEL_BG        = (10, 15, 24)
C_PANEL_BORDER    = (55, 85, 128)
C_PANEL_BORDER_HI = (85, 135, 210)
C_TITLE_BAR       = (25, 40, 70)

C_TEXT_PRIMARY    = (232, 232, 238)
C_TEXT_DIM        = (145, 158, 172)
C_TEXT_GOLD       = (255, 208, 65)
C_TEXT_GREEN      = (75, 225, 130)
C_TEXT_RED        = (225, 75, 70)
C_TEXT_BLUE       = (100, 180, 255)
C_TEXT_PURPLE     = (195, 135, 255)
C_TEXT_ORANGE     = (255, 165, 55)

# Button base colours
BTN = {
    'bfs':   (25, 70, 150),
    'dfs':   (28, 118, 65),
    'ucs':   (115, 35, 138),
    'astar': (155, 78, 25),
    'reset': (112, 88, 25),
    'menu':  (75, 48, 100),
    'undo':  (68, 68, 125),
    'hint':  (32, 112, 65),
}

# --- Helpers ---

def _lighten(color, amount):
    return tuple(min(v + amount, 255) for v in color)

def _darken(color, amount):
    return tuple(max(v - amount, 0) for v in color)

def _alpha_surf(w, h, color_rgba):
    """Create a Surface filled with an RGBA colour."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(color_rgba)
    return s

def _rounded_alpha_surf(w, h, color_rgba, radius=8):
    """Create a rounded-rect SRCALPHA surface."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, color_rgba, s.get_rect(), border_radius=radius)
    return s


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC DRAWING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def draw_button(screen, rect, label, base_color, font, mouse_pos=None):
    """
    Polished rounded button:
    • Drop shadow
    • Top-half highlight (fake gradient)
    • Hover: brighter fill + outer glow ring
    • 1 px border
    """
    is_hover = bool(mouse_pos and rect.collidepoint(mouse_pos))
    color    = _lighten(base_color, 42) if is_hover else base_color

    # 1. Drop shadow
    sh = _rounded_alpha_surf(rect.width, rect.height, (0, 0, 0, 65))
    screen.blit(sh, (rect.x + 2, rect.y + 4))

    # 2. Main fill
    pygame.draw.rect(screen, color, rect, border_radius=8)

    # 3. Top-half highlight (simulates a subtle gradient)
    hi_h = max(5, rect.height // 2 - 2)
    hi_a = 38 if is_hover else 24
    hi   = _alpha_surf(rect.width - 4, hi_h, (255, 255, 255, hi_a))
    screen.blit(hi, (rect.x + 2, rect.y + 2))

    # 4. Crisp border
    pygame.draw.rect(screen, _lighten(base_color, 72), rect, width=1, border_radius=8)

    # 5. Outer glow ring on hover
    if is_hover:
        gr = pygame.Rect(rect.x - 2, rect.y - 2, rect.width + 4, rect.height + 4)
        glow = pygame.Surface((gr.width, gr.height), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*_lighten(base_color, 90), 80),
                         glow.get_rect(), width=2, border_radius=10)
        screen.blit(glow, gr.topleft)

    # 6. Label
    txt = font.render(label, True, (255, 255, 255))
    screen.blit(txt, txt.get_rect(center=rect.center))


def draw_panel(screen, x, y, w, h, alpha=200, border_color=None,
               title=None, title_font=None, title_color=None):
    """
    Translucent dark panel with an optional title bar.
    """
    # Background
    bg = _rounded_alpha_surf(w, h, (*C_PANEL_BG, alpha))
    screen.blit(bg, (x, y))

    # Border
    bc = border_color or C_PANEL_BORDER
    pygame.draw.rect(screen, bc, (x, y, w, h), width=1, border_radius=8)

    # Optional title bar
    if title and title_font:
        bar_h = 26
        bar = _alpha_surf(w - 2, bar_h, (*C_TITLE_BAR, 200))
        screen.blit(bar, (x + 1, y + 1))
        pygame.draw.line(screen, bc, (x + 1, y + bar_h + 1), (x + w - 2, y + bar_h + 1))
        tc  = title_color or C_TEXT_GOLD
        txt = title_font.render(title, True, tc)
        screen.blit(txt, (x + 8, y + (bar_h - txt.get_height()) // 2 + 1))


def draw_notification(screen, msg, timer, max_timer, scr_w, scr_h, font):
    """
    Animated toast notification:
    • Slides up from bottom on appear  (first ~14 frames)
    • Fades out near end               (last ~22 frames)
    • Hint → green   |   Error → red
    """
    if timer <= 0:
        return

    is_hint = "Hint" in msg or msg.startswith("hint")

    if is_hint:
        bg_c   = (18, 50, 30)
        brd_c  = (55, 190, 105)
        txt_c  = (140, 255, 165)
        icon   = "\u2022  "          # bullet
    else:
        bg_c   = (50, 16, 16)
        brd_c  = (200, 55, 50)
        txt_c  = (255, 175, 170)
        icon   = "\u26a0  "          # warning ▲

    # Alpha (fade-out)
    fade_f = 22
    alpha  = int(230 * min(timer / fade_f, 1.0))

    # Slide-in (ease-out quad)
    slide_f = 14
    if timer > max_timer - slide_f:
        prog  = (max_timer - timer) / slide_f
        eased = 1.0 - (1.0 - prog) ** 2
    else:
        eased = 1.0

    msg_w = max(360, len(msg) * 9 + 90)
    msg_h = 46
    x     = scr_w // 2 - msg_w // 2
    base_y = scr_h - 115
    y      = base_y + int((1.0 - eased) * 55)

    # Background rounded rect
    bg_surf = _rounded_alpha_surf(msg_w, msg_h, (*bg_c, min(alpha, 215)), radius=6)
    screen.blit(bg_surf, (x, y))

    # Border
    bd = pygame.Surface((msg_w, msg_h), pygame.SRCALPHA)
    pygame.draw.rect(bd, (*brd_c, alpha), bd.get_rect(), width=1, border_radius=6)
    screen.blit(bd, (x, y))

    # Top accent strip (3 px)
    strip = _alpha_surf(msg_w, 3, (*brd_c, alpha))
    screen.blit(strip, (x, y))

    # Text
    txt = font.render(icon + msg, True, txt_c)
    screen.blit(txt, txt.get_rect(center=(x + msg_w // 2, y + msg_h // 2)))


def draw_win_overlay(screen, scr_w, scr_h, text, font_big):
    """Full-screen tinted overlay with centred win/status text."""
    # Dim the whole screen
    dim = _alpha_surf(scr_w, scr_h, (0, 0, 0, 110))
    screen.blit(dim, (0, 0))

    txt  = font_big.render(text, True, C_TEXT_GOLD)
    tw, th = txt.get_width(), txt.get_height()
    pad_x, pad_y = 60, 28
    bx = scr_w // 2 - tw // 2 - pad_x
    by = scr_h // 2 - th // 2 - pad_y

    # Outer glow (stack a couple of faint rects)
    for off, a in [(6, 30), (3, 55)]:
        glow = _rounded_alpha_surf(tw + pad_x * 2 + off * 2, th + pad_y * 2 + off * 2,
                                   (*C_TEXT_GOLD, a), radius=18)
        screen.blit(glow, (bx - off, by - off))

    # Panel
    draw_panel(screen, bx, by, tw + pad_x * 2, th + pad_y * 2,
               alpha=225, border_color=C_TEXT_GOLD)

    screen.blit(txt, (scr_w // 2 - tw // 2, scr_h // 2 - th // 2))


def draw_solving_overlay(screen, scr_w, scr_h, text, font_big):
    """Centred overlay for 'Solving...' state."""
    txt  = font_big.render(text, True, C_TEXT_GOLD)
    tw, th = txt.get_width(), txt.get_height()
    pad_x, pad_y = 40, 20
    bx = scr_w // 2 - tw // 2 - pad_x
    by = scr_h // 2 - th // 2 - pad_y

    draw_panel(screen, bx, by, tw + pad_x * 2, th + pad_y * 2,
               alpha=210, border_color=C_TEXT_GOLD)
    screen.blit(txt, (scr_w // 2 - tw // 2, scr_h // 2 - th // 2))