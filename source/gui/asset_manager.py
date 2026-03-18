#gui/asset_manager.py
import pygame
import os

class CardLoader:
    def __init__ (self, card_size = (100, 140)):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_folders = os.path.join(current_dir, "..", "assets", "cards")
        self.card_size = card_size
        self.card_images = {}

    def load_cards(self):

        # Define suits and ranks
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

        for suit in suits:
            for rank in ranks:
                # Auto-generate the filename based on suit and rank
                filename = f"{rank}_of_{suit}.png"
                path = os.path.join(self.assets_folders, filename)

                try:
                    # Download and scale the image
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, self.card_size)

                    # Store the image in the dictionary with a key is a tupe of (rank, suit)
                    self.card_images[(rank, suit)] = img

                except FileNotFoundError:
                    print(f"Warning: Card image '{filename}' not found in '{self.assets_folders}'.")
    
        return self.card_images

