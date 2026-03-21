# gui/menu_view.py
import pygame


class MenuView:
    def __init__(self, theme, width, height):
        self.theme = theme
        self.font_title = pygame.font.SysFont('Arial', 64, bold=True)
        self.font_sub = pygame.font.SysFont('Arial', 22)
        self.font_btn = pygame.font.SysFont('Arial', 30)

        self.rect_manual = None
        self.rect_ai = None
        self.update_layout(width, height)

    def update_layout(self, width, height):
        self.width = width
        self.height = height
        btn_w, btn_h = 320, 60
        cx = (width - btn_w) // 2
        self.rect_manual = pygame.Rect(cx, 350, btn_w, btn_h)
        self.rect_ai = pygame.Rect(cx, 440, btn_w, btn_h)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect_manual and self.rect_manual.collidepoint(event.pos):
                return "MANUAL"
            if self.rect_ai and self.rect_ai.collidepoint(event.pos):
                return "AI"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "QUIT"
        return None

    def _draw_btn(self, screen, rect, text, color):
        mouse = pygame.mouse.get_pos()
        c = tuple(min(v + 25, 255) for v in color) if rect.collidepoint(mouse) else color
        pygame.draw.rect(screen, c, rect, border_radius=12)
        pygame.draw.rect(screen, (255, 255, 255, 60), rect, width=1, border_radius=12)
        txt = self.font_btn.render(text, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=rect.center))

    def draw(self, screen):
        self.theme.draw_background(screen)

        title = self.font_title.render("FreeCell Solitaire", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(self.width // 2, 190)))

        sub = self.font_sub.render("Choose a mode to start", True, (200, 200, 200))
        screen.blit(sub, sub.get_rect(center=(self.width // 2, 260)))

        self._draw_btn(screen, self.rect_manual, "Manual Play", (40, 120, 255))
        self._draw_btn(screen, self.rect_ai, "AI Auto Solve", (180, 90, 40))