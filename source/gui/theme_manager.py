#gui/thememanager.py
import os
import pygame

class ThemeManager:
    def __init__(self):
        self.original_background = None
        self.background_img = None

        self.freecell_img = None
        self.foundation_img = {
            'hearts': None,
            'diamonds': None,  
            'clubs': None,
            'spades': None
        }

    
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_folder = os.path.join(self.current_dir, "..", "assets", "backgrounds")

        self.COLOR_BACKGROUND_DEFAULT = (0, 128, 0)
        self.COLOR_EMPTY_SLOT = (0, 100, 0) 
        self.COLOR_SLOT_BORDER = (150, 150, 150) 

    def load_background(self, filepath, screen_width, screen_height):
        path = os.path.join(self.assets_folder, filepath)
        try:
            self.original_background = pygame.image.load(path).convert()
            self.resize_background(screen_width, screen_height)

        except FileNotFoundError:
            print(f"Background image not found at {path}. Using solid color background.")
            self.original_background = None
            self.background_img = None

    def resize_background(self, screen_width, screen_height):
        if self.original_background:
            self.background_img = pygame.transform.smoothscale(self.original_background, (screen_width, screen_height))

    def draw_background(self, screen):
        # Draw background image if available, otherwise fill with solid color
        if self.background_img:
            screen.blit(self.background_img, (0, 0))
        else:
            screen.fill(self.COLOR_BACKGROUND_DEFAULT)

    def load_ui_elements(self, card_width, card_height):
        # FreeCell
        try:
            freecell_path = os.path.join(self.assets_folder, "freecell.png")
            freecell_raw = pygame.image.load(freecell_path).convert_alpha()
            self.freecell_img = pygame.transform.smoothscale(freecell_raw, (card_width, card_height))

        except FileNotFoundError:
            print(f"FreeCell image not found at {freecell_path}. Using empty slot color.")
            self.freecell_img = None

        # Foundation
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        for suit in suits:
            foundation_path = os.path.join(self.assets_folder, f"foundation_{suit}.png")
            try:
                foundation_raw = pygame.image.load(foundation_path).convert_alpha()
                self.foundation_img[suit] = pygame.transform.smoothscale(foundation_raw, (card_width, card_height))

            except FileNotFoundError:
                print(f"Foundation image for {suit} not found at {foundation_path}. Using empty slot color.")
                self.foundation_img[suit] = None
