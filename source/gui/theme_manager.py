#gui/thememanager.py
import os
import pygame

class ThemeManager:
    def __init__(self):
        self.original_background = None
        self.background_img = None

        self.COLOR_BACKGROUND_DEFAULT = (0, 128, 0) #Green background
        self.COLOR_EMPTY_SLOT = (0, 100, 0) #Darker green for empty slots
        self.COLOR_SLOT_BORDER = (150, 150, 150) #Gray border for empty slots

    def load_background(self, filepath, screen_width, screen_height):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_folder = os.path.join(current_dir, "..", "assets", "backgrounds")
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