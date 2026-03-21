#core/state.py
import random
from .card import Card

class State:
    SUITS = ['hearts', 'diamonds', 'clubs', 'spades']

    def __init__(self):
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {'hearts': [], 'diamonds': [], 'clubs': [], 'spades': []}

    def initialize_game(self):
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = [Card(rank, suit) for suit in suits for rank in ranks]
        random.shuffle(deck)
        for i in range(4):
            for j in range(7):
                if deck:
                    self.cascades[i].append(deck.pop())
        for i in range(4, 8):
            for j in range(6):
                if deck:
                    self.cascades[i].append(deck.pop())

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