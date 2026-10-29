import pygame


class Slider:
    def __init__(self, label, x, y, width, min_val, max_val, value):
        self.label = label
        self.rect = pygame.Rect(x, y, width, 6)       # the track
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # inflate() makes the clickable area taller than the 6 px track.
            if self.rect.inflate(0, 20).collidepoint(event.pos):
                self.dragging = True
                self._set_from_mouse_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_mouse_x(event.pos[0])

    def _set_from_mouse_x(self, mouse_x):
        t = (mouse_x - self.rect.x) / self.rect.width
        t = max(0.0, min(1.0, t))
        self.value = self.min_val + t * (self.max_val - self.min_val)

    def draw(self, surface, font):
        pygame.draw.rect(surface, (90, 90, 110), self.rect, border_radius=3)
        t = (self.value - self.min_val) / (self.max_val - self.min_val)
        knob_x = self.rect.x + t * self.rect.width
        pygame.draw.circle(surface, (230, 230, 230), (int(knob_x), self.rect.centery), 8)
        text = font.render(f"{self.label}: {self.value:.2f}", True, (230, 230, 230))
        surface.blit(text, (self.rect.x, self.rect.y - 22))
