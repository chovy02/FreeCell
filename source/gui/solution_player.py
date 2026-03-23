# gui/solution_player.py
import pygame
from core.move_generator import auto_to_foundation, _apply_inplace, describe_move

class SolutionPlayer:
    def __init__(self):
        self.steps = []
        self.move_strings = [] 
        self.milestones = []   # Mảng chứa các "cột mốc" để gộp bước chính và bước auto
        self.current_step = 0
        self.target_step = 0   
        
        self.delay_timer = 0
        self.delay_frames = 5  
        
        self.animating = False
        self.anim_direction = 1 
        self.anim_cards = []
        self.anim_pos = (0, 0)
        self.anim_target = (0, 0)
        self.anim_progress = 0.0
        
        self.speed_normal = 0.12 
        self.speed_fast = 0.6    # Nhanh gấp 5 lần khi tua đầu/cuối
        self.current_speed = self.speed_normal
        self.current_move = None

    def start(self, initial_state, solver_moves):
        # Trả lại hàm clone() để bảo vệ trạng thái gốc khi Reset
        self.initial_state = initial_state.clone() 
        state = initial_state.clone()
        
        self.steps = []
        self.move_strings = [] # CHỈ lưu chuỗi hiển thị của bước chính
        self.milestones = []
        
        # 1. Các bước Auto ban đầu
        initial_auto = auto_to_foundation(state)
        self.steps.extend(initial_auto)
        self.milestones.append(len(self.steps)) # Cột mốc 0
        
        # 2. Các bước của Solver
        for move in solver_moves:
            _apply_inplace(state, move)
            self.steps.append(move)
            self.move_strings.append(describe_move(move)) # Ghi nhận bước chính lên bảng
            
            # Các bước Auto đi kèm ngay sau bước chính
            auto_moves = auto_to_foundation(state)
            self.steps.extend(auto_moves)
            
            # Đánh dấu cột mốc tiếp theo
            self.milestones.append(len(self.steps)) 
            
        self.current_step = 0
        # Ngay khi start, tự động cho chạy các bước auto ban đầu
        self.target_step = self.milestones[0] 
        self.animating = False
        self.anim_cards = []

    def stop(self):
        self.target_step = self.current_step
        self.animating = False

    # --- CÁC HÀM ĐIỀU KHIỂN NÚT BẤM ---
    def toggle_play(self):
        if self.target_step > self.current_step: 
            self.target_step = self.current_step # Pause
        else: 
            self.target_step = self.milestones[-1] # Play
            self.current_speed = self.speed_normal

    def step_forward(self):
        if not self.animating:
            # Bay toàn bộ các bước cho đến cột mốc tiếp theo
            for m in self.milestones:
                if m > self.current_step:
                    self.target_step = m
                    self.current_speed = self.speed_normal
                    break

    def step_backward(self):
        if not self.animating:
            # Hoàn tác toàn bộ các bước lui về cột mốc trước đó
            for m in reversed(self.milestones):
                if m < self.current_step:
                    self.target_step = m
                    self.current_speed = self.speed_normal
                    break

    def fast_forward_end(self):
        self.target_step = self.milestones[-1]
        self.current_speed = self.speed_fast

    def fast_rewind_start(self):
        self.target_step = 0 # Tua lui về trạng thái nguyên thủy
        self.current_speed = self.speed_fast

    def is_playing(self):
        return self.target_step != self.current_step or self.animating

    def get_current_move_index(self):
        """Hàm này giúp Bảng nước đi biết đang ở bước chính số mấy để sáng đèn"""
        for i in range(len(self.milestones) - 1):
            if self.current_step < self.milestones[i+1]:
                return i
        return len(self.move_strings) # Chạy xong hết

    # --- LOGIC CẬP NHẬT TRẠNG THÁI ---
    def update(self, state, board_view):
        if self.animating:
            self.anim_progress += self.current_speed
            if self.anim_progress >= 1.0:
                self.anim_progress = 1.0
                self._finish_animation(state)
        else:
            if self.current_step != self.target_step:
                self.delay_timer += 1
                wait_time = 0 if self.current_speed == self.speed_fast else self.delay_frames
                
                if self.delay_timer >= wait_time:
                    self.delay_timer = 0
                    if self.current_step < self.target_step:
                        self._start_forward_animation(state, board_view)
                    elif self.current_step > self.target_step:
                        self._start_backward_animation(state, board_view)

    def _start_forward_animation(self, state, board_view):
        self.current_move = self.steps[self.current_step]
        src_type, src_idx, dst_type, dst_idx, num = self.current_move

        if src_type == 'cascade':
            rects = board_view.hitbox['cascades'][src_idx]
            self.anim_pos = rects[-num].topleft if len(rects) >= num else rects[0].topleft
        elif src_type == 'freecell':
            self.anim_pos = board_view.hitbox['free_cells'][src_idx].topleft
        
        self.anim_cards = []
        if src_type == 'cascade':
            self.anim_cards = state.cascades[src_idx][-num:]
            state.cascades[src_idx] = state.cascades[src_idx][:-num]
        elif src_type == 'freecell':
            self.anim_cards = [state.free_cells[src_idx]]
            state.free_cells[src_idx] = None

        if dst_type == 'cascade':
            target_list = board_view.hitbox['cascades'][dst_idx]
            if not state.cascades[dst_idx]:
                self.anim_target = target_list[0].topleft if target_list else (0,0)
            else:
                last_rect = target_list[-1]
                self.anim_target = (last_rect.x, last_rect.y + board_view.vertical_spacing)
        elif dst_type == 'freecell':
            self.anim_target = board_view.hitbox['free_cells'][dst_idx].topleft
        elif dst_type == 'foundation':
            fnd_index = ['hearts', 'diamonds', 'clubs', 'spades'].index(dst_idx)
            self.anim_target = board_view.hitbox['foundations'][fnd_index].topleft

        self.anim_direction = 1
        self.animating = True
        self.anim_progress = 0.0

    def _start_backward_animation(self, state, board_view):
        self.current_move = self.steps[self.current_step - 1]
        src_type, src_idx, dst_type, dst_idx, num = self.current_move

        self.anim_cards = []
        if dst_type == 'cascade':
            self.anim_cards = state.cascades[dst_idx][-num:]
            state.cascades[dst_idx] = state.cascades[dst_idx][:-num]
        elif dst_type == 'freecell':
            self.anim_cards = [state.free_cells[dst_idx]]
            state.free_cells[dst_idx] = None
        elif dst_type == 'foundation':
            self.anim_cards = [state.foundations[dst_idx][-1]]
            state.foundations[dst_idx].pop()

        if dst_type == 'cascade':
            target_list = board_view.hitbox['cascades'][dst_idx]
            if len(target_list) > 0:
                self.anim_pos = (target_list[-1].x, target_list[-1].y + board_view.vertical_spacing)
            else:
                self.anim_pos = (0, 0) 
        elif dst_type == 'freecell':
            self.anim_pos = board_view.hitbox['free_cells'][dst_idx].topleft
        elif dst_type == 'foundation':
            fnd_index = ['hearts', 'diamonds', 'clubs', 'spades'].index(dst_idx)
            self.anim_pos = board_view.hitbox['foundations'][fnd_index].topleft

        if src_type == 'cascade':
            rects = board_view.hitbox['cascades'][src_idx]
            self.anim_target = rects[-1].topleft if rects else (0,0)
        elif src_type == 'freecell':
            self.anim_target = board_view.hitbox['free_cells'][src_idx].topleft

        self.anim_direction = -1
        self.animating = True
        self.anim_progress = 0.0

    def _finish_animation(self, state):
        self.animating = False
        src_type, src_idx, dst_type, dst_idx, num = self.current_move

        if self.anim_direction == 1:
            if dst_type == 'cascade':
                state.cascades[dst_idx].extend(self.anim_cards)
            elif dst_type == 'freecell':
                state.free_cells[dst_idx] = self.anim_cards[0]
            elif dst_type == 'foundation':
                state.foundations[dst_idx].append(self.anim_cards[0])
            self.current_step += 1
        else: 
            if src_type == 'cascade':
                state.cascades[src_idx].extend(self.anim_cards)
            elif src_type == 'freecell':
                state.free_cells[src_idx] = self.anim_cards[0]
            self.current_step -= 1

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
                dy = cur_y + i * board_view.vertical_spacing
                screen.blit(deck[img_key], (cur_x, dy))

    @property
    def playing(self):
        return self.is_playing()

    def get_info(self):
        return {
            'playing': self.is_playing(),
            'current_step': self.current_step,
            'total_steps': len(self.steps),
        }