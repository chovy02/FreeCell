# gui/manual_animator.py
import pygame

class ManualAnimator:
    def __init__(self):
        self.queue = []
        self.current_anim = None
        self.anim_speed = 0.12  # Tốc độ bay (giống SolutionPlayer)

    def add_animation(self, cards, start_pos, end_pos, apply_func, on_complete=None):
        """Thêm một animation vào hàng đợi."""
        self.queue.append({
            'cards': cards,
            'start_pos': start_pos,
            'end_pos': end_pos,
            'progress': 0.0,
            'apply_func': apply_func,      # Hàm thay đổi State
            'on_complete': on_complete     # Hàm gọi sau khi bay xong (để check dây chuyền)
        })

    def is_animating(self):
        return self.current_anim is not None or len(self.queue) > 0

    def update(self):
        """Cập nhật tiến trình bay mỗi frame."""
        if not self.current_anim and self.queue:
            self.current_anim = self.queue.pop(0)

        if self.current_anim:
            self.current_anim['progress'] += self.anim_speed
            if self.current_anim['progress'] >= 1.0:
                # 1. Thẻ đã đến đích, áp dụng logic vào State thực tế
                if self.current_anim['apply_func']:
                    self.current_anim['apply_func']()
                
                # 2. Gọi hàm callback (Ví dụ: để tiếp tục check Auto Foundation)
                if self.current_anim['on_complete']:
                    self.current_anim['on_complete']()
                    
                self.current_anim = None
                return True
        return False

    def draw(self, screen, deck, vertical_spacing):
        """Vẽ thẻ bài đang bay."""
        if not self.current_anim:
            return

        sx, sy = self.current_anim['start_pos']
        tx, ty = self.current_anim['end_pos']
        p = self.current_anim['progress']
        
        # Hiệu ứng Ease-Out Quad: bay chậm dần khi tới gần đích
        eased_p = 1 - (1 - p) * (1 - p)
        cur_x = sx + (tx - sx) * eased_p
        cur_y = sy + (ty - sy) * eased_p

        for i, card in enumerate(self.current_anim['cards']):
            img_key = (card.rank, card.suit)
            if img_key in deck:
                img = deck[img_key]
                dy = cur_y + i * vertical_spacing
                screen.blit(img, (cur_x, dy))