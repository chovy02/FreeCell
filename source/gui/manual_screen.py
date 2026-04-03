# gui/manual_screen.py
import pygame
from .board_view import BoardView
from .game_controller import GameController
from core.state import State
from .manual_animator import ManualAnimator
from .dealing_animator import DealingAnimator
from .manual_solver_helper import ManualSolverHelper
from .win_animator import WinAnimator
from .ui_theme import (
    BTN, C_PANEL_BG, C_PANEL_BORDER, C_TEXT_PRIMARY, C_TEXT_DIM,
    C_TEXT_GOLD, C_TEXT_GREEN, C_TEXT_RED,
    draw_button, draw_panel, draw_notification,
    _alpha_surf, _rounded_alpha_surf
)

_BTN_MENU  = (75, 48, 100)
_BTN_RESET = (112, 88, 25)
_BTN_UNDO  = (68, 68, 125)


class ManualScreen:
    def __init__(self, deck, theme, state, screen_w=1280, screen_h=720):
        self.deck = deck
        self.theme = theme
        self.state = state
        self.initial_state = state.clone()

        self.board_view = BoardView(deck, theme)
        self.controller = GameController()
        self.animator   = ManualAnimator()

        self._screen_w    = screen_w
        self._screen_h    = screen_h
        self._deal_anim   = None
        self._deal_inited = False

        self.history = []
        self._save_state()
        self.invalid_msg   = ""
        self.invalid_timer = 0
        self.NOTIF_MAX     = 150

        # Win state: 0=inactive, 1=bouncing anim, 2=overlay
        self.won = False
        self._win_anim = None
        self._win_phase = 0

        # Game-over (stuck) state
        self.stuck = False
        self._stuck_timer = 0
        self._STUCK_FADE_IN = 30

        # Overlay button rects (win/stuck screens)
        self._overlay_btn_rects = {}

        self.font       = pygame.font.SysFont('consolas', 16)
        self.font_big   = pygame.font.SysFont('consolas', 46, bold=True)
        self.font_btn   = pygame.font.SysFont('consolas', 15, bold=True)
        self.font_label = pygame.font.SysFont('consolas', 12)
        self.font_sub   = pygame.font.SysFont('consolas', 18)
        self.btn_rects  = {}
        self.ai_helper  = ManualSolverHelper(self)

    # --- State management ---

    def _save_state(self):
        self.history.append(self.state.clone())

    def _undo(self):
        if len(self.history) > 1:
            self.history.pop()
            self.state = self.history[-1].clone()
            self.won = False
            self._win_anim = None
            self._win_phase = 0
            self.stuck = False
            self._stuck_timer = 0

    def _reset(self):
        self.state   = self.initial_state.clone()
        self.history = [self.state.clone()]
        self.won     = False
        self._win_anim = None
        self._win_phase = 0
        self.stuck = False
        self._stuck_timer = 0

    def _show_invalid(self, msg):
        self.invalid_msg   = msg
        self.invalid_timer = self.NOTIF_MAX

    def _hint(self):
        from core.move_generator import get_valid_moves
        moves = get_valid_moves(self.state)
        if moves:
            src_type, src_idx, dst_type, dst_idx, num = moves[0]
            src = f"Col {src_idx+1}" if src_type == 'cascade' else f"FC {src_idx+1}"
            if dst_type == 'cascade':
                dst = f"Col {dst_idx+1}"
            elif dst_type == 'freecell':
                dst = f"FC {dst_idx+1}"
            else:
                dst = "Foundation"
            self._show_invalid(f"Hint: {src} → {dst}")
        else:
            self._show_invalid("No valid moves available!")

    def _check_auto_foundation(self):
        from core.move_generator import _can_fnd, is_safe_auto
        suits_order = ['hearts', 'diamonds', 'clubs', 'spades']

        for i, cascade in enumerate(self.state.cascades):
            if cascade and _can_fnd(self.state, cascade[-1]) and is_safe_auto(self.state, cascade[-1]):
                card = cascade.pop()
                rects   = self.board_view.hitbox['cascades'][i]
                s_pos   = rects[-1].topleft if rects else (0, 0)
                fnd_idx = suits_order.index(card.suit)
                e_pos   = self.board_view.hitbox['foundations'][fnd_idx].topleft

                def apply(c=card):
                    self.state.foundations[c.suit].append(c)
                self.animator.add_animation([card], s_pos, e_pos, apply,
                                            on_complete=self._check_auto_foundation)
                return

        for i, card in enumerate(self.state.free_cells):
            if card and _can_fnd(self.state, card) and is_safe_auto(self.state, card):
                self.state.free_cells[i] = None
                s_pos   = self.board_view.hitbox['free_cells'][i].topleft
                fnd_idx = suits_order.index(card.suit)
                e_pos   = self.board_view.hitbox['foundations'][fnd_idx].topleft

                def apply(c=card):
                    self.state.foundations[c.suit].append(c)
                self.animator.add_animation([card], s_pos, e_pos, apply,
                                            on_complete=self._check_auto_foundation)
                return

        if len(self.history) == 0 or self.state.get_key() != self.history[-1].get_key():
            self._save_state()
            if self.state.is_goal():
                self._trigger_win()
            elif not self.stuck:
                self._check_stuck()

    def _trigger_win(self):
        self.won = True
        self._win_phase = 1
        self._win_anim = WinAnimator(
            self.deck, self.state, self.board_view,
            self._screen_w, self._screen_h
        )

    def _check_stuck(self):
        from core.move_generator import get_valid_moves
        if not get_valid_moves(self.state):
            self.stuck = True
            self._stuck_timer = 0

    def _handle_overlay_click(self, pos, allowed_keys):
        for key, rect in self._overlay_btn_rects.items():
            if key in allowed_keys and rect.collidepoint(pos):
                return key
        return None

    # --- Events ---

    def handle_event(self, event):
        if self._deal_anim and not self._deal_anim.done:
            if event.type == pygame.MOUSEBUTTONDOWN or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                self._deal_anim.skip()
            return None

        if self.animator.is_animating():
            return None

        # Win phase 1: bouncing cards — click/space to skip
        if self._win_phase == 1:
            if event.type == pygame.MOUSEBUTTONDOWN or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                self._win_phase = 2
                self._win_anim = None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "MENU"
            return None

        # Win phase 2: overlay with buttons
        if self._win_phase == 2:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return "MENU"
                elif event.key == pygame.K_r:    self._reset()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = self._handle_overlay_click(event.pos, ('menu', 'reset'))
                if action == 'menu':  return "MENU"
                if action == 'reset': self._reset()
            return None

        # Stuck overlay with buttons
        if self.stuck:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return "MENU"
                elif event.key == pygame.K_z:    self._undo()
                elif event.key == pygame.K_r:    self._reset()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = self._handle_overlay_click(event.pos, ('menu', 'reset', 'undo'))
                if action == 'menu':  return "MENU"
                if action == 'reset': self._reset()
                if action == 'undo':  self._undo()
            return None

        if self.ai_helper.handle_event(event):
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: return "MENU"
            elif event.key == pygame.K_z:    self._undo()
            elif event.key == pygame.K_r:    self._reset()
            elif event.key == pygame.K_h:    self._hint()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.btn_rects.items():
                if rect.collidepoint(event.pos):
                    if key == 'undo':  self._undo()
                    elif key == 'reset': self._reset()
                    elif key == 'hint':  self._hint()
                    elif key == 'menu':  return "MENU"
                    return None

        if not self.won:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
                self.controller.handle_event(event, self.state, self.board_view,
                                             self.animator,
                                             on_move_complete=self._check_auto_foundation)
                if self.controller.last_error:
                    self._show_invalid(self.controller.last_error)
                    self.controller.last_error = ""

        return None

    # --- Drawing ---

    def draw(self, screen, width, height):
        self._screen_w = width
        self._screen_h = height
        self.theme.draw_background(screen)

        if not self._deal_inited:
            self.board_view.draw_board(screen, width, height, self.state)
            self._deal_inited = True
            self._deal_anim = DealingAnimator(
                self.deck, self.state, self.board_view, width, height)
            self.theme.draw_background(screen)

        if self.ai_helper.active:
            self.ai_helper.draw(screen, width, height)
            return

        dealing = self._deal_anim and not self._deal_anim.done
        if dealing:
            display_state = self._deal_anim.get_display_state()
            self._deal_anim.update()
        else:
            display_state = self.state

        self.board_view.draw_board(screen, width, height, display_state)
        self._draw_buttons(screen, width, height)

        if not dealing:
            self.animator.update()
            self._draw_dragging(screen)
            self.animator.draw(screen, self.deck, self.board_view.vertical_spacing)

        self._draw_notification(screen, width, height)

        if dealing:
            self._deal_anim.draw(screen)
            hint = self.font_label.render("Click or Space to skip", True, (140, 140, 140))
            screen.blit(hint, hint.get_rect(center=(width // 2, height - 95)))
            return

        # Win phase 1: bouncing cards
        if self._win_phase == 1 and self._win_anim:
            self._win_anim.update()
            self._win_anim.draw(screen)
            if self._win_anim.done:
                self._win_phase = 2
                self._win_anim = None
            else:
                hint = self.font_label.render("Click or Space to skip", True, (140, 140, 140))
                screen.blit(hint, hint.get_rect(center=(width // 2, height - 30)))

        # Win phase 2: victory overlay
        if self._win_phase == 2:
            self._draw_win_screen(screen, width, height)

        # Game-over overlay
        if self.stuck and not self.won:
            self._stuck_timer += 1
            self._draw_stuck_overlay(screen, width, height)

    # --- Win overlay ---

    def _draw_win_screen(self, screen, width, height):
        dim = _alpha_surf(width, height, (0, 0, 0, 130))
        screen.blit(dim, (0, 0))

        pw, ph = 420, 280
        px = width // 2 - pw // 2
        py = height // 2 - ph // 2

        for off, a in [(8, 20), (4, 45)]:
            glow = _rounded_alpha_surf(pw + off * 2, ph + off * 2,
                                       (*C_TEXT_GOLD, a), radius=18)
            screen.blit(glow, (px - off, py - off))

        draw_panel(screen, px, py, pw, ph, alpha=230, border_color=C_TEXT_GOLD)

        title = self.font_big.render("YOU WIN!", True, C_TEXT_GOLD)
        screen.blit(title, title.get_rect(center=(width // 2, py + 55)))

        moves_count = len(self.history) - 1
        fnd_count = self.state.foundation_count()
        stats = self.font_sub.render(
            f"Moves: {moves_count}    Cards: {fnd_count}/52", True, C_TEXT_PRIMARY)
        screen.blit(stats, stats.get_rect(center=(width // 2, py + 115)))

        mouse = pygame.mouse.get_pos()
        btn_w, btn_h, gap = 150, 46, 20
        total_btn_w = 2 * btn_w + gap
        bx = width // 2 - total_btn_w // 2
        by = py + 170

        strip = pygame.Surface((total_btn_w + 24, btn_h + 16), pygame.SRCALPHA)
        pygame.draw.rect(strip, (0, 0, 0, 50), strip.get_rect(), border_radius=10)
        screen.blit(strip, (bx - 12, by - 8))

        r_play = pygame.Rect(bx, by, btn_w, btn_h)
        r_menu = pygame.Rect(bx + btn_w + gap, by, btn_w, btn_h)
        self._overlay_btn_rects['reset'] = r_play
        self._overlay_btn_rects['menu']  = r_menu

        draw_button(screen, r_play, "Play Again [R]", _BTN_RESET, self.font_btn, mouse)
        draw_button(screen, r_menu, "Menu",           _BTN_MENU,  self.font_btn, mouse)

    # --- Game-over overlay ---

    def _draw_stuck_overlay(self, screen, width, height):
        progress = min(1.0, self._stuck_timer / self._STUCK_FADE_IN)
        dim_alpha = int(140 * progress)
        dim = _alpha_surf(width, height, (0, 0, 0, dim_alpha))
        screen.blit(dim, (0, 0))

        if progress < 0.3:
            return

        content_alpha = min(255, int(255 * (progress - 0.3) / 0.7))

        pw, ph = 440, 280
        px = width // 2 - pw // 2
        py = height // 2 - ph // 2

        panel = _rounded_alpha_surf(pw, ph, (*C_PANEL_BG, min(content_alpha, 230)), radius=12)
        screen.blit(panel, (px, py))

        border = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(border, (*C_TEXT_RED, min(content_alpha, 180)),
                         border.get_rect(), width=2, border_radius=12)
        screen.blit(border, (px, py))

        title = self.font_big.render("GAME OVER", True, C_TEXT_RED)
        title.set_alpha(content_alpha)
        screen.blit(title, title.get_rect(center=(width // 2, py + 50)))

        sub = self.font_sub.render("No valid moves remaining", True, C_TEXT_DIM)
        sub.set_alpha(content_alpha)
        screen.blit(sub, sub.get_rect(center=(width // 2, py + 100)))

        moves_count = len(self.history) - 1
        fnd_count = self.state.foundation_count()
        stats = self.font_label.render(
            f"Moves: {moves_count}    Foundation: {fnd_count}/52", True, C_TEXT_DIM)
        stats.set_alpha(content_alpha)
        screen.blit(stats, stats.get_rect(center=(width // 2, py + 135)))

        # Buttons appear after fade-in
        if content_alpha < 200:
            return

        mouse = pygame.mouse.get_pos()
        btn_w, btn_h, gap = 130, 46, 14
        total_btn_w = 3 * btn_w + 2 * gap
        bx = width // 2 - total_btn_w // 2
        by = py + 175

        strip = pygame.Surface((total_btn_w + 24, btn_h + 16), pygame.SRCALPHA)
        pygame.draw.rect(strip, (0, 0, 0, 50), strip.get_rect(), border_radius=10)
        screen.blit(strip, (bx - 12, by - 8))

        r_undo  = pygame.Rect(bx, by, btn_w, btn_h)
        r_reset = pygame.Rect(bx + btn_w + gap, by, btn_w, btn_h)
        r_menu  = pygame.Rect(bx + 2 * (btn_w + gap), by, btn_w, btn_h)
        self._overlay_btn_rects['undo']  = r_undo
        self._overlay_btn_rects['reset'] = r_reset
        self._overlay_btn_rects['menu']  = r_menu

        draw_button(screen, r_undo,  "Undo [Z]",  _BTN_UNDO,  self.font_btn, mouse)
        draw_button(screen, r_reset, "Reset [R]",  _BTN_RESET, self.font_btn, mouse)
        draw_button(screen, r_menu,  "Menu",       _BTN_MENU,  self.font_btn, mouse)

    # --- Bottom bar ---

    def _draw_buttons(self, screen, width, height):
        btn_h  = 40
        btn_w  = 108
        gap    = 10
        labels = [
            ('Undo  [Z]', 'undo',  BTN['undo']),
            ('Hint  [H]', 'hint',  BTN['hint']),
            ('Reset [R]', 'reset', BTN['reset']),
            ('Menu',      'menu',  BTN['menu']),
        ]
        total = len(labels) * btn_w + (len(labels) - 1) * gap
        sx    = (width - total) // 2
        sy    = height - btn_h - 12
        mouse = pygame.mouse.get_pos()

        strip_surf = pygame.Surface((total + 32, btn_h + 18), pygame.SRCALPHA)
        strip_surf.fill((0, 0, 0, 55))
        screen.blit(strip_surf, (sx - 16, sy - 8))

        for idx, (label, key, color) in enumerate(labels):
            x    = sx + idx * (btn_w + gap)
            rect = pygame.Rect(x, sy, btn_w, btn_h)
            self.btn_rects[key] = rect
            draw_button(screen, rect, label, color, self.font_btn, mouse)

    def _draw_dragging(self, screen):
        for i, card in enumerate(self.controller.dragging_cards):
            img_key = (card.rank, card.suit)
            if img_key in self.deck:
                img = self.deck[img_key]
                dx  = self.controller.drag_pos[0]
                dy  = self.controller.drag_pos[1] + i * self.board_view.vertical_spacing
                screen.blit(img, img.get_rect(topleft=(dx, dy)))

    def _draw_notification(self, screen, width, height):
        if self.invalid_timer > 0:
            self.invalid_timer -= 1
            draw_notification(screen, self.invalid_msg, self.invalid_timer,
                              self.NOTIF_MAX, width, height, self.font)