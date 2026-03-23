#core/state.py
import random
from .card import Card
from utils.dealer import Dealer

class State:
    SUITS = ['hearts', 'diamonds', 'clubs', 'spades']

    def __init__(self):
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {'hearts': [], 'diamonds': [], 'clubs': [], 'spades': []}

    def initialize_game(self, seed):
        # Reset
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {'hearts': [], 'diamonds': [], 'clubs': [], 'spades': []}
        
        deck = Dealer.get_deck(seed)

        self.initial_deck = deck # Save for reset

        for i, card_data in enumerate(deck):
            col_index = i % 8
            rank, suit = card_data
            card = Card(rank, suit)
            self.cascades[col_index].append(card)

    def clone(self):
        new = State.__new__(State)
        new.cascades = [list(c) for c in self.cascades]
        new.free_cells = list(self.free_cells)
        new.foundations = {s: list(f) for s, f in self.foundations.items()}
        return new

    def get_key(self):
        cas = tuple(sorted(tuple(hash(c) for c in col) for col in self.cascades))
        fc = tuple(sorted(hash(c) if c is not None else 0 for c in self.free_cells))
        fnd = tuple(len(self.foundations[s]) for s in self.SUITS)
        return (cas, fc, fnd)

    def is_goal(self):
        return all(len(self.foundations[s]) == 13 for s in self.SUITS)

    def foundation_count(self):
        return sum(len(self.foundations[s]) for s in self.SUITS)
    
    def reset_to_start(self):
        #Reset the state
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {'hearts': [], 'diamonds': [], 'clubs': [], 'spades': []}
        
        # Use the saved deck
        for i, card_data in enumerate(self.initial_deck):
            col_index = i % 8
            rank, suit = card_data
            self.cascades[col_index].append(Card(rank, suit))