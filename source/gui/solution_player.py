# gui/solution_player.py
"""Animates solver solution moves on the board."""

from core.move_generator import compute_animation_steps, describe_move, _apply_inplace


class SolutionPlayer:
    def __init__(self):
        self.steps = []
        self.current_step = 0
        self.playing = False
        self.timer = 0
        self.delay = 3

        self.move_log = []
        self.initial_state = None

        self.animating = False
        self.anim_cards = []
        self.anim_pos = (0, 0)
        self.anim_target = (0, 0)
        self.anim_progress = 0.0
        self.anim_speed = 0.12
        self.current_move = None

    def start(self, initial_state, solver_moves):
        """All solvers now use same move format - no special cases needed."""
        self.initial_state = initial_state.clone()
        self.steps = compute_animation_steps(initial_state, solver_moves)
        self.current_step = 0
        self.playing = True
        self.timer = 0
        self.move_log = []
        self.animating = False

    def stop(self):
        self.playing = False
        self.animating = False

    def update(self, state, board_view):
        if not self.playing:
            return

        if self.animating:
            self.anim_progress += self.anim_speed
            if self.anim_progress >= 1.0:
                self.anim_progress = 1.0
                self.animating = False

                src_type, src_idx, dst_type, dst_idx, num = self.current_move
                if src_type == 'cascade':
                    state.cascades[src_idx].extend(self.anim_cards)
                elif src_type == 'freecell':
                    state.free_cells[src_idx] = self.anim_cards[0]

                _apply_inplace(state, self.current_move)
                desc = describe_move(self.current_move)
                self.move_log.append(f"{self.current_step + 1}. {desc}")
                self.current_step += 1
        else:
            self.timer += 1
            if self.timer < self.delay:
                return
            self.timer = 0

            if self.current_step < len(self.steps):
                self.current_move = self.steps[self.current_step]
                self._start_animation(state, board_view)
            else:
                self.playing = False

    def _start_animation(self, state, board_view):
        src_type, src_idx, dst_type, dst_idx, num = self.current_move

        if src_type == 'cascade':
            rects = board_view.hitbox['cascades'][src_idx]
            if len(rects) >= num:
                self.anim_pos = rects[-num].topleft
            elif rects:
                self.anim_pos = rects[0].topleft
            else:
                self.anim_pos = (0, 0)
        elif src_type == 'freecell':
            self.anim_pos = board_view.hitbox['free_cells'][src_idx].topleft
        else:
            self.anim_pos = (0, 0)

        if dst_type == 'cascade':
            target_list = board_view.hitbox['cascades'][dst_idx]
            if not state.cascades[dst_idx]:
                self.anim_target = target_list[0].topleft if target_list else (0, 0)
            else:
                last_rect = target_list[-1]
                self.anim_target = (last_rect.x, last_rect.y + board_view.vertical_spacing)
        elif dst_type == 'freecell':
            self.anim_target = board_view.hitbox['free_cells'][dst_idx].topleft
        elif dst_type == 'foundation':
            suits = ['hearts', 'diamonds', 'clubs', 'spades']
            fnd_index = suits.index(dst_idx)
            self.anim_target = board_view.hitbox['foundations'][fnd_index].topleft

        self.anim_cards = []
        if src_type == 'cascade':
            self.anim_cards = state.cascades[src_idx][-num:]
            state.cascades[src_idx] = state.cascades[src_idx][:-num]
        elif src_type == 'freecell':
            self.anim_cards = [state.free_cells[src_idx]]
            state.free_cells[src_idx] = None

        self.animating = True
        self.anim_progress = 0.0

    def draw(self, screen, deck, board_view):
        if not self.animating or not self.anim_cards:
            return

        sx, sy = self.anim_pos
        tx, ty = self.anim_target
        p = self.anim_progress
        eased_p = 1 - (1 - p) * (1 - p)

        cur_x = sx + (tx - sx) * eased_p
        cur_y = sy + (ty - sy) * eased_p

        for i, card in enumerate(self.anim_cards):
            img_key = (card.rank, card.suit)
            if img_key in deck:
                img = deck[img_key]
                dy = cur_y + i * board_view.vertical_spacing
                screen.blit(img, (cur_x, dy))

    def get_info(self):
        return {
            'playing': self.playing,
            'current_step': self.current_step,
            'total_steps': len(self.steps),
        }