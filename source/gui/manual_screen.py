# gui/manual_screen.py
import pygame
from .board_view import BoardView
from .game_controller import GameController
from core.state import State
from .manual_animator import ManualAnimator


class ManualScreen:
    def __init__(self, deck, theme, state):
        self.deck = deck
        self.theme = theme
        self.state = state
        self.initial_state = state.clone()

        self.board_view = BoardView(deck, theme)
        self.controller = GameController()
        self.animator = ManualAnimator()

        self.history = []
        self._save_state()
        self.invalid_msg = ""
        self.invalid_timer = 0
        self.won = False
        self.font = pygame.font.SysFont('consolas', 16)
        self.font_big = pygame.font.SysFont('consolas', 42, bold=True)
        self.btn_rects = {}

    def _save_state(self):
        self.history.append(self.state.clone())

    def _undo(self):
        if len(self.history) > 1:
            self.history.pop()
            self.state = self.history[-1].clone()

    def _reset(self):
        self.state = self.initial_state.clone()
        self.history = [self.state.clone()]
        self.won = False

    def _show_invalid(self, msg):
        self.invalid_msg = msg
        self.invalid_timer = 150  # ~2.5 seconds

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
            self._show_invalid(f"Hint: {src} -> {dst}")
        else:
            self._show_invalid("No valid moves!")

    def _check_auto_foundation(self):
        """Auto-fly cards to foundation ONLY when truly safe."""
        from core.move_generator import _can_fnd, is_safe_auto
        suits_order = ['hearts', 'diamonds', 'clubs', 'spades']

        # Check cascades
        for i, cascade in enumerate(self.state.cascades):
            if cascade and _can_fnd(self.state, cascade[-1]) and is_safe_auto(self.state, cascade[-1]):
                card = cascade.pop()
                rects = self.board_view.hitbox['cascades'][i]
                start_pos = rects[-1].topleft if rects else (0, 0)
                fnd_idx = suits_order.index(card.suit)
                end_pos = self.board_view.hitbox['foundations'][fnd_idx].topleft

                def apply(c=card):
                    self.state.foundations[c.suit].append(c)
                self.animator.add_animation([card], start_pos, end_pos, apply,
                                            on_complete=self._check_auto_foundation)
                return

        # Check free cells
        for i, card in enumerate(self.state.free_cells):
            if card and _can_fnd(self.state, card) and is_safe_auto(self.state, card):
                self.state.free_cells[i] = None
                start_pos = self.board_view.hitbox['free_cells'][i].topleft
                fnd_idx = suits_order.index(card.suit)
                end_pos = self.board_view.hitbox['foundations'][fnd_idx].topleft

                def apply(c=card):
                    self.state.foundations[c.suit].append(c)
                self.animator.add_animation([card], start_pos, end_pos, apply,
                                            on_complete=self._check_auto_foundation)
                return

        # Chain done - save state for undo
        if len(self.history) == 0 or self.state.get_key() != self.history[-1].get_key():
            self._save_state()
            if self.state.is_goal():
                self.won = True

    def handle_event(self, event):
        if self.animator.is_animating():
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "MENU"
            elif event.key == pygame.K_z:
                self._undo()
            elif event.key == pygame.K_r:
                self._reset()
            elif event.key == pygame.K_h:
                self._hint()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.btn_rects.items():
                if rect.collidepoint(event.pos):
                    if key == 'undo':
                        self._undo()
                    elif key == 'reset':
                        self._reset()
                    elif key == 'hint':
                        self._hint()
                    elif key == 'menu':
                        return "MENU"
                    return None

        if not self.won:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
                self.controller.handle_event(event, self.state, self.board_view,
                                             self.animator,
                                             on_move_complete=self._check_auto_foundation)
                # Show controller error messages
                if self.controller.last_error:
                    self._show_invalid(self.controller.last_error)
                    self.controller.last_error = ""

        return None

    def draw(self, screen, width, height):
        self.animator.update()

        self.theme.draw_background(screen)
        self.board_view.draw_board(screen, width, height, self.state)
        self._draw_buttons(screen, width, height)
        self._draw_dragging(screen)
        self.animator.draw(screen, self.deck, self.board_view.vertical_spacing)
        self._draw_notification(screen, width, height)

        if self.won:
            self._draw_overlay(screen, width, height, "YOU WIN!", (255, 215, 0))

    def _draw_buttons(self, screen, width, height):
        btn_y = height - 55
        btn_h, btn_w, gap = 38, 100, 12
        buttons = [
            ('Undo [Z]', 'undo', (90, 90, 140)),
            ('Hint [H]', 'hint', (50, 130, 80)),
            ('Reset[R]', 'reset', (140, 100, 40)),
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
            txt = self.font.render(label, True, (255, 255, 255))
            screen.blit(txt, (x + (btn_w - txt.get_width()) // 2,
                              btn_y + (btn_h - txt.get_height()) // 2))

    def _draw_dragging(self, screen):
        for i, card in enumerate(self.controller.dragging_cards):
            img_key = (card.rank, card.suit)
            if img_key in self.deck:
                img = self.deck[img_key]
                dx = self.controller.drag_pos[0]
                dy = self.controller.drag_pos[1] + i * self.board_view.vertical_spacing
                screen.blit(img, img.get_rect(topleft=(dx, dy)))

    def _draw_notification(self, screen, width, height):
        if self.invalid_timer > 0:
            self.invalid_timer -= 1
            alpha = min(230, self.invalid_timer * 4)

            # Background bar
            msg_w = max(450, len(self.invalid_msg) * 10 + 40)
            surf = pygame.Surface((msg_w, 44), pygame.SRCALPHA)

            is_hint = "Hint" in self.invalid_msg
            bg_color = (20, 60, 40, min(200, alpha)) if is_hint else (80, 20, 20, min(200, alpha))
            surf.fill(bg_color)

            x = width // 2 - msg_w // 2
            y = height - 110
            screen.blit(surf, (x, y))

            # Border
            border_color = (80, 200, 120) if is_hint else (220, 80, 80)
            pygame.draw.rect(screen, border_color, (x, y, msg_w, 44), 1, 4)

            # Text
            text_color = (150, 255, 150) if is_hint else (255, 200, 200)
            txt = self.font.render(self.invalid_msg, True, text_color)
            screen.blit(txt, (x + msg_w // 2 - txt.get_width() // 2, y + 12))

    def _draw_overlay(self, screen, width, height, text, color):
        txt = self.font_big.render(text, True, color)
        x = width // 2 - txt.get_width() // 2
        y = height // 2 - txt.get_height() // 2
        bg = pygame.Surface((txt.get_width() + 60, txt.get_height() + 30), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 190))
        screen.blit(bg, (x - 30, y - 15))
        screen.blit(txt, (x, y))