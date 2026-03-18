#core/rules.py

class Rules:

    RANK_VALUES = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}

    @staticmethod
    def is_valid_sequence(cards):
        if not cards:
            return False
        for i in range(len(cards) - 1):
            top_card = cards[i]
            bottom_card = cards[i + 1]

            if top_card.color == bottom_card.color:
                return False
            
            top_val = Rules.RANK_VALUES[top_card.rank]
            bottom_val = Rules.RANK_VALUES[bottom_card.rank]

            if top_val != bottom_val + 1:
                return False
            
        return True
    
    @staticmethod
    def max_movable_cards(state, target_cascade_index = None):
        empty_free_cells = sum(1 for cell in state.free_cells if cell is None)
        empty_cascades = sum(1 for i, cascade in enumerate(state.cascades) if len(cascade) == 0 and i != target_cascade_index)

        return (empty_free_cells + 1) * (2 ** empty_cascades)
    
    @staticmethod
    def can_move_to_cascade(state, moving_cards, cascade_index):
        if not moving_cards:
            return False
        
        if len(moving_cards) > 1 and not Rules.is_valid_sequence(moving_cards):
            return False
        
        max_cards = Rules.max_movable_cards(state, cascade_index)
        if len(moving_cards) > max_cards:
            return False
        
        bottom_moving_card = moving_cards[0]
        cascade = state.cascades[cascade_index]
        if len(cascade) == 0:
            return True
        
        target_card = cascade[-1]

        if bottom_moving_card.color == target_card.color:
            return False
        
        bottom_val = Rules.RANK_VALUES[bottom_moving_card.rank]
        target_val = Rules.RANK_VALUES[target_card.rank]

        return bottom_val == target_val - 1
    
    @staticmethod
    def can_move_to_freecell(state, moving_cards, freecell_index):
        if len(moving_cards) > 1:
            return False
        
        if state.free_cells[freecell_index] is not None:
            return False
        
        return True
    
    @staticmethod
    def can_move_to_foundation(state, moving_cards, suit):
        if len(moving_cards) > 1:
            return False
        
        card = moving_cards[0]
        if card.suit != suit:
            return False
        
        foundation = state.foundations[suit]
        card_val = Rules.RANK_VALUES[card.rank]

        if len(foundation) == 0:
            return card_val == 1
        
        top_card_val = Rules.RANK_VALUES[foundation[-1].rank]
        return card_val == top_card_val + 1