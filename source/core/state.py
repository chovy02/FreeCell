#core/state.py
import random
from .card import Card

class State:
    def __init__(self):
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {'hearts': [], 'diamonds': [], 'clubs': [], 'spades': []}

    def initialize_game(self):
        # Init a random game
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