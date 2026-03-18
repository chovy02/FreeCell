#gui/gamecontroller.py
import pygame
from core.rules import Rules

class GameController:
    def __init__(self):
        self.dragging_cards = [] #Card being dragged
        self.source_location = None #Source pile (cascade, free cell, foundation)
        self.drag_pos = (0, 0) #Current mouse position while dragging
        self.mouse_offset = (0, 0) #Offset from mouse to top-left of card when dragging

    def handle_event(self, event, state, board_view):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: #Left click
            self._handle_mouse_down(event.pos, state, board_view)

        elif event.type == pygame.MOUSEMOTION and self.dragging_cards is not None:
            self._handle_mouse_motion(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._handle_mouse_up(event.pos, state, board_view)

    def _handle_mouse_down(self, mouse_pos, state, board_view):
        for i, rect in enumerate(board_view.hitbox['cascades']):
            if rect and rect.collidepoint(mouse_pos):
                if len(state.cascades[i]) > 0:
                    card = state.cascades[i].pop()
                    self.dragging_cards = [card]
                    self.source_location = ('cascade', i)
                    self.mouse_offset = (rect.x - mouse_pos[0], rect.y - mouse_pos[1])
                    self.drag_pos = (rect.x, rect.y)
                    return
                
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

    def _handle_mouse_up(self, mouse_pos, state, board_view):
        if not self.dragging_cards:
            return
        
        dropped = False

        if not dropped:
            for i, rect in enumerate(board_view.hitbox['cascades']):
                if rect and rect.collidepoint(mouse_pos):
                    if self.source_location == ('cascade', i):
                        self._return_card_to_source(state)
                        dropped = True
                        break

                    if Rules.can_move_to_cascade(state, self.dragging_cards, i):
                        state.cascades[i].extend(self.dragging_cards)
                        self.dragging_cards = []
                        self.source_location = None
                        dropped = True
                        break

        if not dropped:
            for i, rect in enumerate(board_view.hitbox['free_cells']):
                if rect and rect.collidepoint(mouse_pos):
                    if self.source_location == ('free_cell', i):
                        self._return_card_to_source(state)
                        dropped = True
                        break

                    if Rules.can_move_to_freecell(state, self.dragging_cards, i):
                        state.free_cells[i] = self.dragging_cards[0]
                        self.dragging_cards = []
                        self.source_location = None
                        dropped = True
                        break

        if not dropped:
            suits_order = ['hearts', 'diamonds', 'clubs', 'spades']
            for i, rect in enumerate(board_view.hitbox['foundations']):
                if rect and rect.collidepoint(mouse_pos):
                    suit = suits_order[i]
                    if Rules.can_move_to_foundation(state, self.dragging_cards, suit):
                        state.foundations[suit].append(self.dragging_cards[0])
                        self.dragging_cards = []
                        self.source_location = None
                        dropped = True
                        break

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
                
                
