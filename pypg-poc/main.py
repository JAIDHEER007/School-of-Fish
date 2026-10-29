import pygame
import settings
from fish import Fish
import random
from flock import Flock
from slider import Slider

WIDTH, HEIGHT = settings.WIDTH, settings.HEIGHT

flock = Flock(settings.NUM_FISH, settings.SEED)

x = settings.WIDTH - 240
sep_slider = Slider("Separation", x, 40, 200, 0.0, 5.0, settings.SEPARATION_WEIGHT)
ali_slider = Slider("Alignment", x, 90, 200, 0.0, 5.0, settings.ALIGNMENT_WEIGHT)
coh_slider = Slider("Cohesion", x, 140, 200, 0.0, 5.0, settings.COHESION_WEIGHT)
sliders = [sep_slider, ali_slider, coh_slider]

def main():
    pygame.init()                                        # start all PyGame subsystems
    screen = pygame.display.set_mode((WIDTH, HEIGHT))    # the window's drawing surface
    pygame.display.set_caption("School of Fish - PyGame POC")
    clock = pygame.time.Clock()                          # for frame timing (next step)

    font = pygame.font.Font(None, 24)
    frame_ms = clock.tick(settings.FPS_CAP)

    

    running = True
    while running:
        # 1. Input: the OS queues events (key presses, mouse, window close).
        #    You MUST drain this queue every frame, or the OS thinks the app froze.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:                # clicked the window's X
                running = False

        for s in sliders:
            s.handle_event(event)
        
        # 2. Draw: clear the whole frame first, then draw everything on top.
        screen.fill(settings.BG_COLOR)                        # dark ocean blue (R, G, B)

        flock.step(settings.SIM_DT)

        flock.separation_weight = sep_slider.value
        flock.alignment_weight = ali_slider.value
        flock.cohesion_weight = coh_slider.value

        flock.draw(screen)

        for s in sliders:
            s.draw(screen, font)

        hud = f"FPS: {clock.get_fps():5.1f}   frame: {frame_ms:4.1f} ms"
        text_surface = font.render(hud, True, (230, 230, 230))   # True = antialiased
        screen.blit(text_surface, (10, 10)) 

        # 3. Present: PyGame draws into a hidden back buffer; flip() swaps it to the screen.
        pygame.display.flip()

        clock.tick(settings.FPS_CAP)                                   # wait so we run at most 60 FPS

    pygame.quit()


if __name__ == "__main__":
    main()