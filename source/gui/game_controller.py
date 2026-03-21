# gui/game_controller.py
import pygame
from core.rules import Rules

class GameController:
    def __init__(self):
        self.dragging_cards = []
        self.source_location = None
        self.drag_pos = (0, 0)
        self.mouse_offset = (0, 0)
        self.mouse_down_pos = (0, 0)
        self.has_dragged = False
        self.last_error = ""  # Error message for display

    def handle_event(self, event, state, board_view, animator=None, on_move_complete=None):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.last_error = ""
            self._handle_mouse_down(event.pos, state, board_view)
        elif event.type == pygame.MOUSEMOTION and self.dragging_cards:
            self._handle_mouse_motion(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._handle_mouse_up(event.pos, state, board_view, animator, on_move_complete)

    def _get_slot_pos(self, board_view, state, loc_type, index):
        if loc_type == 'cascade':
            rects = board_view.hitbox['cascades'][index]
            if not state.cascades[index]:
                return rects[0].topleft if rects else (0, 0)
            else:
                last_rect = rects[-1]
                return (last_rect.x, last_rect.y + board_view.vertical_spacing)
        elif loc_type in ('free_cell', 'freecell'):
            return board_view.hitbox['free_cells'][index].topleft
        elif loc_type == 'foundation':
            return board_view.hitbox['foundations'][index].topleft
        return (0, 0)

    def _find_cascade_column(self, mouse_pos, board_view):
        """Find which cascade column the mouse is over (by x-coordinate area)."""
        for i, rects in enumerate(board_view.hitbox['cascades']):
            if not rects:
                continue
            first_rect = rects[0]
            # Column area: full width of card, from top of cascade to bottom of screen
            col_left = first_rect.x
            col_right = first_rect.x + board_view.card_width
            col_top = first_rect.y
            if col_left <= mouse_pos[0] <= col_right and mouse_pos[1] >= col_top:
                return i
        return -1

    def _handle_mouse_down(self, mouse_pos, state, board_view):
        self.mouse_down_pos = mouse_pos
        self.has_dragged = False

        # Check cascades
        for i, cascade_rects in enumerate(board_view.hitbox['cascades']):
            cascade = state.cascades[i]
            if len(cascade) == 0:
                continue
            for j in range(len(cascade_rects) - 1, -1, -1):
                rect = cascade_rects[j]
                if rect and rect.collidepoint(mouse_pos):
                    moving_cards = cascade[j:]
                    # Check valid sequence first
                    if not Rules.is_valid_sequence(moving_cards):
                        self.last_error = "Cards must alternate red/black in descending order"
                        return
                    # Check max movable
                    max_m = Rules.max_movable_cards(state)
                    if len(moving_cards) > max_m:
                        self.last_error = f"Can only move {max_m} card{'s' if max_m > 1 else ''} (need more free cells/columns)"
                        return
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
            self.drag_pos = (mouse_pos[0] + self.mouse_offset[0],
                             mouse_pos[1] + self.mouse_offset[1])
            if (abs(mouse_pos[0] - self.mouse_down_pos[0]) > 5 or
                    abs(mouse_pos[1] - self.mouse_down_pos[1]) > 5):
                self.has_dragged = True

    def _handle_mouse_up(self, mouse_pos, state, board_view, animator, on_move_complete):
        if not self.dragging_cards:
            return

        is_click = not self.has_dragged
        if is_click and animator:
            if self._attempt_auto_move(state, board_view, animator, on_move_complete):
                return

        # --- IMPROVED HITBOX: use overlap area + column detection ---
        drag_rect = pygame.Rect(self.drag_pos[0], self.drag_pos[1],
                                board_view.card_width, board_view.card_height)
        best_target = None
        max_area = 0

        # Check cascade columns (broader area - entire column width)
        col_idx = self._find_cascade_column(mouse_pos, board_view)
        if col_idx >= 0:
            cascade_rects = board_view.hitbox['cascades'][col_idx]
            if cascade_rects:
                target_rect = cascade_rects[-1]
                # Expand hitbox: include area below last card
                expanded = pygame.Rect(target_rect.x, target_rect.y,
                                       board_view.card_width,
                                       board_view.card_height + 200)
                if expanded.colliderect(drag_rect):
                    clip = expanded.clip(drag_rect)
                    area = clip.width * clip.height
                    if area > max_area:
                        max_area = area
                        best_target = ('cascade', col_idx)

        # Also check direct overlap with cascade rects (fallback)
        for i, cascade_rects in enumerate(board_view.hitbox['cascades']):
            target_rect = cascade_rects[-1] if cascade_rects else None
            if target_rect and target_rect.colliderect(drag_rect):
                clip = target_rect.clip(drag_rect)
                area = clip.width * clip.height
                if area > max_area:
                    max_area = area
                    best_target = ('cascade', i)

        # Check free cells
        for i, rect in enumerate(board_view.hitbox['free_cells']):
            if rect and rect.colliderect(drag_rect):
                clip = rect.clip(drag_rect)
                area = clip.width * clip.height
                if area > max_area:
                    max_area = area
                    best_target = ('free_cell', i)

        # Check foundations
        suits_order = ['hearts', 'diamonds', 'clubs', 'spades']
        for i, rect in enumerate(board_view.hitbox['foundations']):
            if rect and rect.colliderect(drag_rect):
                clip = rect.clip(drag_rect)
                area = clip.width * clip.height
                if area > max_area:
                    max_area = area
                    best_target = ('foundation', i)

        dropped = False

        if best_target and animator:
            loc_type, index = best_target
            end_pos = self._get_slot_pos(board_view, state, loc_type, index)
            cards_to_move = self.dragging_cards[:]

            if loc_type == 'cascade':
                if self.source_location == ('cascade', index):
                    self._return_card_to_source(state)
                    dropped = True
                elif Rules.can_move_to_cascade(state, self.dragging_cards, index):
                    def apply(c=cards_to_move, idx=index):
                        state.cascades[idx].extend(c)
                    animator.add_animation(cards_to_move, self.drag_pos, end_pos, apply,
                                           on_complete=on_move_complete)
                    self.dragging_cards, self.source_location = [], None
                    dropped = True
                else:
                    # Invalid move - generate helpful error
                    cascade = state.cascades[index]
                    if cascade:
                        target = cascade[-1]
                        bottom = self.dragging_cards[0]
                        if bottom.color == target.color:
                            self.last_error = f"Must alternate colors: {bottom} cannot go on {target}"
                        else:
                            self.last_error = f"Must be descending: {bottom} cannot go on {target}"
                    else:
                        max_m = Rules.max_movable_cards(state, index)
                        if len(self.dragging_cards) > max_m:
                            self.last_error = f"Can move max {max_m} cards to empty column"

            elif loc_type == 'free_cell':
                if self.source_location == ('free_cell', index):
                    self._return_card_to_source(state)
                    dropped = True
                elif Rules.can_move_to_freecell(state, self.dragging_cards, index):
                    def apply(c=cards_to_move, idx=index):
                        state.free_cells[idx] = c[0]
                    animator.add_animation(cards_to_move, self.drag_pos, end_pos, apply,
                                           on_complete=on_move_complete)
                    self.dragging_cards, self.source_location = [], None
                    dropped = True
                else:
                    if len(self.dragging_cards) > 1:
                        self.last_error = "Free cell can only hold 1 card"
                    elif state.free_cells[index] is not None:
                        self.last_error = "Free cell is already occupied"

            elif loc_type == 'foundation':
                suit = suits_order[index]
                if Rules.can_move_to_foundation(state, self.dragging_cards, suit):
                    def apply(c=cards_to_move, s=suit):
                        state.foundations[s].append(c[0])
                    animator.add_animation(cards_to_move, self.drag_pos, end_pos, apply,
                                           on_complete=on_move_complete)
                    self.dragging_cards, self.source_location = [], None
                    dropped = True
                else:
                    if len(self.dragging_cards) > 1:
                        self.last_error = "Only 1 card can go to foundation"
                    else:
                        card = self.dragging_cards[0]
                        fnd = state.foundations[suit]
                        if card.suit != suit:
                            self.last_error = f"{card} doesn't match {suit} foundation"
                        elif not fnd and Rules.RANK_VALUES[card.rank] != 1:
                            self.last_error = "Foundation must start with Ace"
                        else:
                            self.last_error = "Card must be next in sequence"

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

    def _attempt_auto_move(self, state, board_view, animator, on_move_complete):
        from core.move_generator import _can_fnd, get_valid_moves, _apply_inplace

        loc_type, index = self.source_location
        if loc_type == 'cascade':
            state.cascades[index].extend(self.dragging_cards)
        elif loc_type == 'free_cell':
            state.free_cells[index] = self.dragging_cards[0]

        num_cards = len(self.dragging_cards)
        bottom_card = self.dragging_cards[0]
        mapped_loc = 'freecell' if loc_type == 'free_cell' else 'cascade'
        best_move = None

        if num_cards == 1 and _can_fnd(state, bottom_card):
            best_move = (mapped_loc, index, 'foundation', bottom_card.suit, 1)

        if not best_move:
            valid_moves = get_valid_moves(state)
            possible = [m for m in valid_moves
                        if m[0] == mapped_loc and m[1] == index and m[4] == num_cards]
            for m in possible:
                if m[2] == 'cascade':
                    best_move = m
                    break
            if not best_move:
                for m in possible:
                    if m[2] == 'freecell':
                        best_move = m
                        break

        if best_move:
            start_pos = self.drag_pos
            dst_type, dst_idx = best_move[2], best_move[3]
            target_idx = dst_idx
            if dst_type == 'foundation':
                target_idx = ['hearts', 'diamonds', 'clubs', 'spades'].index(dst_idx)
            end_pos = self._get_slot_pos(board_view, state, dst_type, target_idx)

            if loc_type == 'cascade':
                del state.cascades[index][-num_cards:]
            elif loc_type == 'free_cell':
                state.free_cells[index] = None

            cards_to_move = self.dragging_cards[:]
            src_loc_copy = self.source_location

            def apply(move=best_move, src_loc=src_loc_copy, cards=cards_to_move):
                if src_loc[0] == 'cascade':
                    state.cascades[src_loc[1]].extend(cards)
                elif src_loc[0] == 'free_cell':
                    state.free_cells[src_loc[1]] = cards[0]
                _apply_inplace(state, move)

            animator.add_animation(cards_to_move, start_pos, end_pos, apply,
                                   on_complete=on_move_complete)
            self.dragging_cards, self.source_location = [], None
            return True

        if loc_type == 'cascade':
            del state.cascades[index][-num_cards:]
        elif loc_type == 'free_cell':
            state.free_cells[index] = None
        return False