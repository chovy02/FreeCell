# gui/game_controller.py
import pygame
from core.rules import Rules

class GameController:
    def __init__(self):
        self.dragging_cards = [] # Card being dragged
        self.source_location = None # Source pile (cascade, free cell, foundation)
        self.drag_pos = (0, 0) # Current mouse position while dragging
        self.mouse_offset = (0, 0) # Offset from mouse to top-left of card when dragging
        self.mouse_down_pos = (0, 0) # Lưu vị trí click chuột
        self.has_dragged = False # Cờ đánh dấu xem người chơi có đang "kéo thả" hay không

    def handle_event(self, event, state, board_view):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left click
            self._handle_mouse_down(event.pos, state, board_view)

        elif event.type == pygame.MOUSEMOTION and self.dragging_cards:
            self._handle_mouse_motion(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._handle_mouse_up(event.pos, state, board_view)

    def _handle_mouse_down(self, mouse_pos, state, board_view):
        self.mouse_down_pos = mouse_pos
        self.has_dragged = False # Reset lại trạng thái mỗi lần nhấn chuột xuống
        
        # Check cascades
        for i, cascade_rects in enumerate(board_view.hitbox['cascades']):
            cascade = state.cascades[i]
            if len(cascade) == 0:
                continue
            
            for j in range(len(cascade_rects) - 1, -1, -1):
                rect = cascade_rects[j]
                if rect and rect.collidepoint(mouse_pos):
                    moving_cards = cascade[j:]
                    if Rules.is_valid_sequence(moving_cards) and len(moving_cards) <= Rules.max_movable_cards(state):
                        self.dragging_cards = moving_cards
                        state.cascades[i] = cascade[:j]
                        self.source_location = ('cascade', i)
                        self.mouse_offset = (rect.x - mouse_pos[0], rect.y - mouse_pos[1])
                        self.drag_pos = (rect.x, rect.y)
                    return
                
        # Check free cells
        for i, rect in enumerate(board_view.hitbox['free_cells']):
            if rect and rect.collidepoint(mouse_pos):
                if state.free_cells[i] is not None:
                    card = state.free_cells[i]
                    self.dragging_cards = [card]
                    state.free_cells[i] = None
                    self.source_location = ('free_cell', i)
                    self.mouse_offset = (rect.x - mouse_pos[0], rect.y - mouse_pos[1])
                    self.drag_pos = (rect.x, rect.y)
                    return
                
    def _handle_mouse_motion(self, mouse_pos):
        if self.dragging_cards:
            self.drag_pos = (mouse_pos[0] + self.mouse_offset[0], mouse_pos[1] + self.mouse_offset[1])
            # Nếu chuột bị kéo đi xa hơn 5 pixel so với lúc click, xác nhận đây là hành động KÉO THẢ
            if abs(mouse_pos[0] - self.mouse_down_pos[0]) > 5 or abs(mouse_pos[1] - self.mouse_down_pos[1]) > 5:
                self.has_dragged = True

    def _handle_mouse_up(self, mouse_pos, state, board_view):
        if not self.dragging_cards:
            return
        
        # Chỉ kích hoạt tính năng Tự Xếp Bài (Auto-move) nếu bài CHƯA bị kéo đi (tức là Click)
        is_click = not self.has_dragged
        
        if is_click:
            if self._attempt_auto_move(state):
                return

        # ---- XỬ LÝ KÉO THẢ (DRAG & DROP) BẰNG DIỆN TÍCH ----
        drag_rect = pygame.Rect(self.drag_pos[0], self.drag_pos[1], board_view.card_width, board_view.card_height)
        
        best_target = None
        max_area = 0

        # Kiểm tra va chạm với Cascades
        for i, cascade_rects in enumerate(board_view.hitbox['cascades']):
            target_rect = cascade_rects[-1] if cascade_rects else None
            if target_rect and target_rect.colliderect(drag_rect):
                clip = target_rect.clip(drag_rect)
                area = clip.width * clip.height
                if area > max_area:
                    max_area = area
                    best_target = ('cascade', i)

        # Kiểm tra va chạm với Free Cells
        for i, rect in enumerate(board_view.hitbox['free_cells']):
            if rect and rect.colliderect(drag_rect):
                clip = rect.clip(drag_rect)
                area = clip.width * clip.height
                if area > max_area:
                    max_area = area
                    best_target = ('free_cell', i)

        # Kiểm tra va chạm với Foundations
        suits_order = ['hearts', 'diamonds', 'clubs', 'spades']
        for i, rect in enumerate(board_view.hitbox['foundations']):
            if rect and rect.colliderect(drag_rect):
                clip = rect.clip(drag_rect)
                area = clip.width * clip.height
                if area > max_area:
                    max_area = area
                    best_target = ('foundation', i)

        dropped = False

        if best_target:
            loc_type, index = best_target

            if loc_type == 'cascade':
                if self.source_location == ('cascade', index):
                    self._return_card_to_source(state)
                    dropped = True
                elif Rules.can_move_to_cascade(state, self.dragging_cards, index):
                    state.cascades[index].extend(self.dragging_cards)
                    self.dragging_cards = []
                    self.source_location = None
                    dropped = True

            elif loc_type == 'free_cell':
                if self.source_location == ('free_cell', index):
                    self._return_card_to_source(state)
                    dropped = True
                elif Rules.can_move_to_freecell(state, self.dragging_cards, index):
                    state.free_cells[index] = self.dragging_cards[0]
                    self.dragging_cards = []
                    self.source_location = None
                    dropped = True

            elif loc_type == 'foundation':
                suit = suits_order[index]
                if Rules.can_move_to_foundation(state, self.dragging_cards, suit):
                    state.foundations[suit].append(self.dragging_cards[0])
                    self.dragging_cards = []
                    self.source_location = None
                    dropped = True

        if not dropped:
            self._return_card_to_source(state)

    def _return_card_to_source(self, state):
        loc_type, index = self.source_location

        if loc_type == 'cascade':
            state.cascades[index].extend(self.dragging_cards)
        elif loc_type == 'free_cell':
            state.free_cells[index] = self.dragging_cards[0]

        self.dragging_cards = []
        self.source_location = None

    def _attempt_auto_move(self, state):
        from core.move_generator import _can_fnd, get_valid_moves, _apply_inplace
        
        loc_type, index = self.source_location
        if loc_type == 'cascade':
            state.cascades[index].extend(self.dragging_cards)
        elif loc_type == 'free_cell':
            state.free_cells[index] = self.dragging_cards[0]
            
        num_cards = len(self.dragging_cards)
        bottom_card = self.dragging_cards[0]
        mapped_loc_type = 'freecell' if loc_type == 'free_cell' else 'cascade'
        best_move = None
        
        # 1. Ưu tiên lên Foundation
        if num_cards == 1 and _can_fnd(state, bottom_card):
            best_move = (mapped_loc_type, index, 'foundation', bottom_card.suit, 1)
            
        if not best_move:
            valid_moves = get_valid_moves(state)
            possible_moves = [m for m in valid_moves 
                              if m[0] == mapped_loc_type and m[1] == index and m[4] == num_cards]
            
            # 2. Ưu tiên Cascade (Cột)
            for m in possible_moves:
                if m[2] == 'cascade':
                    best_move = m
                    break
                    
            # 3. Ưu tiên Freecell (Ô trống)
            if not best_move:
                for m in possible_moves:
                    if m[2] == 'freecell':
                        best_move = m
                        break
                        
        if best_move:
            _apply_inplace(state, best_move)
            self.dragging_cards = []
            self.source_location = None
            return True
            
        if loc_type == 'cascade':
            del state.cascades[index][-num_cards:]
        elif loc_type == 'free_cell':
            state.free_cells[index] = None
            
        return False