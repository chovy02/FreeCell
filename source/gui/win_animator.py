# gui/win_animator.py
"""
Microsoft FreeCell-style win animation: cards launch from foundations
and bounce around the screen with gravity, leaving fading trails.
"""
import pygame
import random
import math


class _BouncingCard:
    """A single card that flies out from a foundation and bounces."""
    __slots__ = ('img', 'x', 'y', 'vx', 'vy', 'gravity', 'bounce',
                 'life', 'max_life', 'trail', 'width', 'height')

    def __init__(self, img, x, y, vx, vy):
        self.img = img
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.gravity = 0.45
        self.bounce = 0.72
        self.width = img.get_width()
        self.height = img.get_height()
        self.life = 0
        self.max_life = random.randint(180, 300)
        self.trail = []  # [(x, y, alpha), ...]

    def update(self, screen_w, screen_h):
        self.life += 1
        if self.life > self.max_life:
            return False

        # Save trail position every 3 frames
        if self.life % 3 == 0:
            fade = max(0, 1.0 - self.life / self.max_life)
            self.trail.append((self.x, self.y, int(120 * fade)))
            if len(self.trail) > 12:
                self.trail.pop(0)

        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy

        # Bounce off bottom
        if self.y + self.height >= screen_h:
            self.y = screen_h - self.height
            self.vy = -abs(self.vy) * self.bounce
            if abs(self.vy) < 1.5:
                return False

        # Bounce off sides
        if self.x < -self.width or self.x > screen_w:
            return False

        return True

    def draw(self, screen):
        # Draw trail (fading afterimages)
        for tx, ty, alpha in self.trail:
            if alpha > 10:
                ghost = self.img.copy()
                ghost.set_alpha(alpha)
                screen.blit(ghost, (int(tx), int(ty)))

        # Draw main card
        fade = max(0, 1.0 - self.life / self.max_life)
        if fade < 1.0:
            card = self.img.copy()
            card.set_alpha(int(255 * fade))
            screen.blit(card, (int(self.x), int(self.y)))
        else:
            screen.blit(self.img, (int(self.x), int(self.y)))


class WinAnimator:
    def __init__(self, deck_images, state, board_view, screen_w, screen_h):
        self.deck = deck_images
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.cards = []
        self.done = False

        self._launch_queue = []
        self._launch_timer = 0
        self._launch_delay = 4  # frames between each card launch
        self._total_launched = 0

        self._build_launch_queue(state, board_view)

    def _build_launch_queue(self, state, board_view):
        """Queue all 52 cards from foundations, top to bottom, cycling suits."""
        suits_order = ['hearts', 'diamonds', 'clubs', 'spades']
        fnd_positions = {}
        for i, suit in enumerate(suits_order):
            rect = board_view.hitbox['foundations'][i]
            if rect:
                fnd_positions[suit] = (rect.x, rect.y)
            else:
                fnd_positions[suit] = (self.screen_w // 2, 40)

        # Build queue: cycle through suits, popping from top of each foundation
        # Reverse each foundation so we launch from King down to Ace
        piles = {}
        for suit in suits_order:
            piles[suit] = list(reversed(state.foundations[suit]))

        # Round-robin launch
        while any(piles[s] for s in suits_order):
            for suit in suits_order:
                if piles[suit]:
                    card = piles[suit].pop(0)
                    sx, sy = fnd_positions[suit]
                    self._launch_queue.append((card, sx, sy, suit))

        if not self._launch_queue:
            self.done = True

    def _launch_card(self, card, sx, sy, suit):
        img_key = (card.rank, card.suit)
        img = self.deck.get(img_key)
        if not img:
            return

        # Varied launch angles based on foundation position
        direction = 1 if sx < self.screen_w // 2 else -1
        # Add some randomness
        vx = direction * random.uniform(3.0, 8.0)
        vy = random.uniform(-12.0, -6.0)

        self.cards.append(_BouncingCard(img, sx, sy, vx, vy))

    def update(self):
        if self.done:
            return

        # Launch new cards from queue
        self._launch_timer += 1
        if self._launch_queue and self._launch_timer >= self._launch_delay:
            self._launch_timer = 0
            card, sx, sy, suit = self._launch_queue.pop(0)
            self._launch_card(card, sx, sy, suit)
            self._total_launched += 1

        # Update all bouncing cards
        alive = []
        for c in self.cards:
            if c.update(self.screen_w, self.screen_h):
                alive.append(c)
        self.cards = alive

        # Done when all launched and all expired
        if not self._launch_queue and not self.cards:
            self.done = True

    def draw(self, screen):
        for c in self.cards:
            c.draw(screen)