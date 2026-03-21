# gui/solution_player.py
"""Animates solver solution moves on the board."""

from core.move_generator import compute_animation_steps, describe_move, _apply_inplace


class SolutionPlayer:
    def __init__(self):
        self.steps = []          
        self.current_step = 0
        self.playing = False
        self.timer = 0
        self.delay = 3           # Đã giảm delay để hoạt ảnh nối tiếp nhau nhanh hơn

        self.move_log = []       
        self.initial_state = None

        # --- ANIMATION PROPERTIES ---
        self.animating = False
        self.anim_cards = []
        self.anim_pos = (0, 0)
        self.anim_target = (0, 0)
        self.anim_progress = 0.0
        self.anim_speed = 0.12    # Tốc độ bay (0.12 = khoảng 8 khung hình mỗi nước đi)
        self.current_move = None

    def start(self, initial_state, solver_moves, is_astar=False):
        """Compute animation steps and start playback."""
        self.initial_state = initial_state.clone()
        # Nếu là A*, dùng thẳng kết quả (không qua auto_move nữa)
        if is_astar:
            self.steps = solver_moves
        else:
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
        """Called every frame. Tách biệt logic chờ và logic chạy animation."""
        if not self.playing:
            return

        # Nếu đang trong quá trình bay
        if self.animating:
            self.anim_progress += self.anim_speed
            if self.anim_progress >= 1.0:
                self.anim_progress = 1.0
                self.animating = False

                # 1. Khôi phục lại bài vào nguồn trước khi chạy logic move gốc
                src_type, src_idx, dst_type, dst_idx, num = self.current_move
                if src_type == 'cascade':
                    state.cascades[src_idx].extend(self.anim_cards)
                elif src_type == 'freecell':
                    state.free_cells[src_idx] = self.anim_cards[0]

                # 2. Áp dụng logic chuẩn của game
                _apply_inplace(state, self.current_move)
                desc = describe_move(self.current_move)
                self.move_log.append(f"{self.current_step + 1}. {desc}")
                self.current_step += 1
        else:
            # Nghỉ một chút xíu giữa các nước đi
            self.timer += 1
            if self.timer < self.delay:
                return
            self.timer = 0

            # Bắt đầu nước đi mới
            if self.current_step < len(self.steps):
                self.current_move = self.steps[self.current_step]
                self._start_animation(state, board_view)
            else:
                self.playing = False

    def _start_animation(self, state, board_view):
        """Tính toán tọa độ và lấy lá bài ra khỏi state để bay."""
        src_type, src_idx, dst_type, dst_idx, num = self.current_move

        # --- Lấy tọa độ Bắt đầu ---
        if src_type == 'cascade':
            if len(board_view.hitbox['cascades'][src_idx]) >= num:
                self.anim_pos = board_view.hitbox['cascades'][src_idx][-num].topleft
            else:
                self.anim_pos = board_view.hitbox['cascades'][src_idx][0].topleft
        elif src_type == 'freecell':
            self.anim_pos = board_view.hitbox['free_cells'][src_idx].topleft
        else:
            self.anim_pos = (0, 0)

        # --- Lấy tọa độ Đích đến ---
        if dst_type == 'cascade':
            target_list = board_view.hitbox['cascades'][dst_idx]
            if not state.cascades[dst_idx]: # Nếu cột đích đang trống
                self.anim_target = target_list[0].topleft
            else:
                last_rect = target_list[-1]
                self.anim_target = (last_rect.x, last_rect.y + board_view.vertical_spacing)
        elif dst_type == 'freecell':
            self.anim_target = board_view.hitbox['free_cells'][dst_idx].topleft
        elif dst_type == 'foundation':
            suits = ['hearts', 'diamonds', 'clubs', 'spades']
            fnd_index = suits.index(dst_idx)
            self.anim_target = board_view.hitbox['foundations'][fnd_index].topleft

        # --- Tạm thời XÓA lá bài khỏi state để board_view không vẽ ---
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
        """Vẽ lá bài đang bay đè lên trên cùng của màn hình."""
        if not self.animating or not self.anim_cards:
            return

        sx, sy = self.anim_pos
        tx, ty = self.anim_target

        # Hiệu ứng Ease-Out Quad: Giảm tốc khi gần đến đích giống Microsoft Freecell
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