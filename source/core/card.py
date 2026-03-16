#core/card.py

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    @property
    def color(self):
        if self.suit in ['hearts', 'diamonds']:
            return 'red'
        else:
            return 'black'
        
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))
                    
    def __repr__(self):
        return f"{self.rank}_{self.suit}"