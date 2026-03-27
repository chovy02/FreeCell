# gui/dealing_animator.py
"""
DealingAnimator — deals cards from an empty board one by one.

Strategy:
  • The real game state is HIDDEN from board_view during the animation.
  • DealingAnimator keeps its own "landed" state that grows as each card
    arrives.  The screen must call  animator.get_display_state()  instead
    of the real state when drawing the board.
  • Once done == True, the screen switches back to the real state normally.
"""
import pygame
import math
import random
from core.state import State
from core.card import Card


_DEAL_SPEED     = 0.075   # progress increment per frame
_DEAL_FAST_SPD  = 0.30    # speed when skipping
_LAUNCH_DELAY   = 3       # frames between successive card launches


# ── tiny back-of-card surface ─────────────────────────────────────────
def _make_back(w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (30, 60, 115), s.get_rect(), border_radius=8)
    pygame.draw.rect(s, (80, 130, 200), s.get_rect(), width=2, border_radius=8)
    # Cross-hatch pattern
    for i in range(0, w, 12):
        pygame.draw.line(s, (50, 90, 150, 90), (i, 0), (i, h))
    for j in range(0, h, 12):
        pygame.draw.line(s, (50, 90, 150, 90), (0, j), (w, j))
    return s


class _FlyingCard:
    __slots__ = ('face', 'back', 'start', 'end', 'delay',
                 'progress', 'speed', 'launched', 'finished', '_flip_done',
                 '_col', '_row', '_card')

    def __init__(self, face_img, back_img, start, end, delay):
        self.face      = face_img
        self.back      = back_img
        self.start     = start
        self.end       = end
        self.delay     = delay
        self.progress  = 0.0
        self.speed     = _DEAL_SPEED
        self.launched  = False
        self.finished  = False
        self._flip_done= False   # face revealed after halfway

    def update(self):
        if self.finished:
            return
        if self.delay > 0:
            self.delay -= 1
            return
        self.launched  = True
        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 1.0
            self.finished = True

    def draw(self, screen):
        if self.finished or not self.launched:
            return

        p     = self.progress
        eased = 1.0 - (1.0 - p) ** 2          # ease-out

        # Arc: rises then falls
        arc_y = -60 * math.sin(p * math.pi)

        sx, sy = self.start
        ex, ey = self.end
        cx = sx + (ex - sx) * eased
        cy = sy + (ey - sy) * eased + arc_y

        # Flip: card spins halfway, revealing face after p > 0.5
        flip_p   = max(0.0, (p - 0.5) / 0.5)
        scale_x  = abs(math.cos(p * math.pi))        # 1→0→1 (horizontal squeeze)
        scale_y  = 0.70 + 0.30 * eased              # grows as it lands
        use_face = (p >= 0.5)

        img = self.face if use_face else self.back
        w   = max(4, int(img.get_width()  * scale_x))
        h   = max(4, int(img.get_height() * scale_y))
        scaled = pygame.transform.smoothscale(img, (w, h))

        r = scaled.get_rect(center=(int(cx), int(cy)))
        screen.blit(scaled, r)


class DealingAnimator:
    """
    Usage
    -----
    animator = DealingAnimator(deck_images, real_state, board_view, w, h)

    # each frame:
    display_state = animator.get_display_state()   # use THIS for board_view
    board_view.draw_board(screen, w, h, display_state)
    animator.update()
    animator.draw(screen)                          # flying cards on top

    if animator.done:
        # use real_state again
    """

    def __init__(self, deck_images, real_state, board_view, screen_w, screen_h):
        self.deck_images = deck_images
        self.real_state  = real_state
        self.board_view  = board_view
        self.screen_w    = screen_w
        self.screen_h    = screen_h

        # "landed" state starts completely empty
        self._landed = State.__new__(State)
        self._landed.cascades    = [[] for _ in range(8)]
        self._landed.free_cells  = [None] * 4
        self._landed.foundations = {'hearts': [], 'diamonds': [], 'clubs': [], 'spades': []}

        self.cards : list[_FlyingCard] = []
        self.done  = False
        self._back = None   # lazy-created card back surface

        self._build()

    # ── BUILD ──────────────────────────────────────────────────────────

    def _build(self):
        bv  = self.board_view
        cw  = bv.card_width
        ch  = bv.card_height
        vs  = bv.vertical_spacing

        total_w = 8 * cw + 7 * bv.spacing
        col_sx  = (self.screen_w - total_w) // 2
        start_y = 220

        # Deck pile source: top-centre of the play area
        src_x = self.screen_w // 2 - cw // 2
        src_y = start_y - 80

        self._back = _make_back(cw, ch)

        self.cards = []
        delay_acc  = 0

        for col_i, cascade in enumerate(self.real_state.cascades):
            col_x = col_sx + col_i * (cw + bv.spacing)
            for row_j, card in enumerate(cascade):
                img_key = (card.rank, card.suit)
                face    = self.deck_images.get(img_key)
                if face is None:
                    continue
                end_x = col_x
                end_y = start_y + row_j * vs
                fc = _FlyingCard(face, self._back,
                                 (src_x, src_y), (end_x, end_y),
                                 delay_acc)
                # Store which column / row so we can land it
                fc._col = col_i
                fc._row = row_j
                fc._card = card
                self.cards.append(fc)
                delay_acc += _LAUNCH_DELAY

        if not self.cards:
            self.done = True

    # ── PUBLIC API ─────────────────────────────────────────────────────

    def get_display_state(self):
        """Return the partially-filled state for board_view to render."""
        return self._landed

    def skip(self):
        for c in self.cards:
            c.speed = _DEAL_FAST_SPD
            c.delay = min(c.delay, 1)

    def update(self):
        if self.done:
            return

        all_done = True
        for c in self.cards:
            was_finished = c.finished
            c.update()
            # Card just landed → add to landed state
            if c.finished and not was_finished:
                self._landed.cascades[c._col].append(c._card)
            if not c.finished:
                all_done = False

        if all_done:
            self.done = True

    def draw(self, screen):
        if self.done:
            return

        in_flight = [c for c in self.cards if c.launched and not c.finished]
        pending   = [c for c in self.cards if not c.launched and not c.finished]

        # Deck pile at source position while cards remain
        if pending or in_flight:
            first_pending = next((c for c in self.cards if not c.finished), None)
            if first_pending:
                sx, sy = first_pending.start
                cw = self.board_view.card_width
                ch = self.board_view.card_height
                count = len(pending)

                # Shadow
                sh = pygame.Surface((cw, ch), pygame.SRCALPHA)
                pygame.draw.rect(sh, (0, 0, 0, 50), sh.get_rect(), border_radius=8)
                screen.blit(sh, (sx + 3, sy + 5))

                # Stack layers (max 4)
                for off in range(min(4, count), 0, -1):
                    if self._back:
                        screen.blit(self._back, (sx - off, sy - off))

        # Flying cards
        for c in in_flight:
            c.draw(screen)