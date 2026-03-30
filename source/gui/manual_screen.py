# gui/manual_screen.py
import pygame
from .board_view import BoardView
from .game_controller import GameController
from core.state import State
from .manual_animator import ManualAnimator
from .dealing_animator import DealingAnimator
from .manual_solver_helper import ManualSolverHelper
from .ui_theme import (
    BTN, C_TEXT_PRIMARY, C_TEXT_DIM, C_TEXT_GOLD, C_TEXT_GREEN,
    draw_button, draw_panel, draw_notification, draw_win_overlay
)


class ManualScreen:
    def __init__(self, deck, theme, state, screen_w=1280, screen_h=720):
        self.deck = deck
        self.theme = theme
        self.state = state
        self.initial_state = state.clone()

        self.board_view = BoardView(deck, theme)
        self.controller = GameController()
        self.animator   = ManualAnimator()

        # Deal animation — board_view needs one draw pass first to set hitbox,
        # so we defer DealingAnimator creation to first draw() call.
        self._screen_w    = screen_w
        self._screen_h    = screen_h
        self._deal_anim   = None
        self._deal_inited = False

        self.history = []
        self._save_state()
        self.invalid_msg   = ""
        self.invalid_timer = 0
        self.NOTIF_MAX     = 150   # frames
        self.won = False

        self.font      = pygame.font.SysFont('consolas', 16)
        self.font_big  = pygame.font.SysFont('consolas', 46, bold=True)
        self.font_btn  = pygame.font.SysFont('consolas', 15, bold=True)
        self.font_label= pygame.font.SysFont('consolas', 12)
        self.btn_rects = {}
        self.ai_helper = ManualSolverHelper(self)

    # ─── STATE MANAGEMENT ──────────────────────────────────────────────

    def _save_state(self):
        self.history.append(self.state.clone())

    def _undo(self):
        if len(self.history) > 1:
            self.history.pop()
            self.state = self.history[-1].clone()

    def _reset(self):
        self.state   = self.initial_state.clone()
        self.history = [self.state.clone()]
        self.won     = False

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
                self.won = True

    # ─── EVENT HANDLING ────────────────────────────────────────────────

    def handle_event(self, event):
        # Skip deal with any click / space
        if self._deal_anim and not self._deal_anim.done:
            if event.type == pygame.MOUSEBUTTONDOWN or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                self._deal_anim.skip()
            return None

        if self.animator.is_animating():
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

    # ─── DRAWING ───────────────────────────────────────────────────────

    def draw(self, screen, width, height):
        self.theme.draw_background(screen)

        # ── First frame: init board_view layout, then create deal animator ──
        if not self._deal_inited:
            self.board_view.draw_board(screen, width, height, self.state)
            self._deal_inited = True
            self._deal_anim = DealingAnimator(
                self.deck, self.state, self.board_view, width, height)
            self.theme.draw_background(screen)

        # ── AI Helper active → let it take over the entire screen ──
        if self.ai_helper.active:
            self.ai_helper.draw(screen, width, height)
            return

        # ── Choose which state to render ──
        if self._deal_anim and not self._deal_anim.done:
            display_state = self._deal_anim.get_display_state()
            self._deal_anim.update()
        else:
            display_state = self.state

        self.board_view.draw_board(screen, width, height, display_state)
        self._draw_buttons(screen, width, height)

        # Normal card animations and drag (only after deal)
        if not (self._deal_anim and not self._deal_anim.done):
            self.animator.update()
            self._draw_dragging(screen)
            self.animator.draw(screen, self.deck, self.board_view.vertical_spacing)

        self._draw_notification(screen, width, height)

        # Deal animation overlay (flying cards)
        if self._deal_anim and not self._deal_anim.done:
            self._deal_anim.draw(screen)
            hint = self.font_label.render("Click or Space to skip", True, (140, 140, 140))
            screen.blit(hint, hint.get_rect(center=(width // 2, height - 95)))

        if self.won:
            draw_win_overlay(screen, width, height, "YOU WIN!", self.font_big)

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

        # Subtle backing strip
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