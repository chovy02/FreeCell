# gui/menuview.py
import pygame

class MenuView:
    def __init__(self, theme, width, height):
        self.theme = theme
        self.font_title = pygame.font.SysFont('Arial', 64, bold=True)
        self.font_button = pygame.font.SysFont('Arial', 32)

        # Define button locations
        self.rect_manual = None
        self.rect_bfs = None

        # Update layout
        self.update_layout(width, height)

    def update_layout(self, width, height):
        self.width = width
        self.height = height

        btn_width, btn_height = 300, 60
        center_x = (width - btn_width) // 2

        self.rect_manual = pygame.Rect(center_x, 350, btn_width, btn_height)
        self.rect_bfs = pygame.Rect(center_x, 450, btn_width, btn_height)

    def handle_event(self, event):
        # Return mode name
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect_manual.collidepoint(event.pos):
                return 'MANUAL'
            elif self.rect_bfs.collidepoint(event.pos):
                return 'BFS'
            
        return None
    
    def draw(self, screen):
        # Draw menu
        self.theme.draw_background(screen)

        # Draw title
        title_text = self.font_title.render("FreeCell Solitaire", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.width // 2, 200))
        screen.blit(title_text, title_rect)

        # Draw buttons
        pygame.draw.rect(screen, (40, 120, 255), self.rect_manual, border_radius = 10)
        pygame.draw.rect(screen, (255, 100, 40), self.rect_bfs, border_radius = 10)

        # Draw text on buttons
        text_manual = self.font_button.render("New Game (Manual)", True, (255, 255, 255))
        text_bfs = self.font_button.render("Auto Game (BFS)", True, (255, 255, 255))

        screen.blit(text_manual, text_manual.get_rect(center=self.rect_manual.center))
        screen.blit(text_bfs, text_bfs.get_rect(center=self.rect_bfs.center))