# utils/dealer.py

class Dealer:
    RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    SUITS = ['clubs', 'diamonds', 'hearts', 'spades'] # 0=C, 1=D, 2=H, 3=S

    @staticmethod
    def get_deck(seed):
        #Shuffle
        
        # Init a card list from 51 to 0 (51 = K Spades, 0 = A Clubs)
        cards = list(range(51, -1, -1))
        
        # 2. Random Numbering Generation (LCG)
        max_int32 = 0x7FFFFFFF
        current_seed = seed & max_int32
        
        rnd = []
        for _ in range(52):
            current_seed = (current_seed * 214013 + 2531011) & max_int32
            rnd.append(current_seed >> 16)
            
        # 3. Shuffle
        for i in range(52):
            r = rnd[i]
            # Shuffle Algorithm
            j = 51 - (r % (52 - i))
            
            # Exchange two cards
            cards[i], cards[j] = cards[j], cards[i]
            
        # 4. Convert number to (Rank, Suit)
        deck = []
        for c in cards:
            rank = Dealer.RANKS[c // 4]
            suit = Dealer.SUITS[c % 4]
            deck.append((rank, suit))
            
        return deck