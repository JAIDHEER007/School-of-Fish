import math

import pygame
from pygame.math import Vector2

import settings


class Fish:
    def __init__(self, pos, vel):
        self.pos = Vector2(pos)      # Vector2(...) makes a copy, so callers can't alias it
        self.vel = Vector2(vel)
        self.acc = Vector2(0, 0)     # sum of steering forces for the current step

    @classmethod
    def random(cls, rng):
        """A fish at a random position, swimming in a random direction."""
        pos = (rng.uniform(0, settings.WIDTH), rng.uniform(0, settings.HEIGHT))
        angle = rng.uniform(0, 2 * math.pi)
        speed = rng.uniform(settings.MIN_SPEED, settings.MAX_SPEED)
        vel = (math.cos(angle) * speed, math.sin(angle) * speed)
        return cls(pos, vel)

    def draw(self, surface):
        # Direction of travel; fall back to "right" if the fish is somehow stopped.
        d = self.vel.normalize() if self.vel.length_squared() > 0 else Vector2(1, 0)
        side = Vector2(-d.y, d.x)                 # d rotated 90°
        s = settings.FISH_SIZE

        nose = self.pos + d * s
        tail_left = self.pos - d * (0.6 * s) + side * (0.4 * s)
        tail_right = self.pos - d * (0.6 * s) - side * (0.4 * s)

        pygame.draw.polygon(surface, (240, 200, 80), [nose, tail_left, tail_right])

    def update(self, dt):
        self.vel += self.acc * dt

        speed = self.vel.length()
        if speed > settings.MAX_SPEED:
            self.vel.scale_to_length(settings.MAX_SPEED)
        elif 0 < speed < settings.MIN_SPEED:          # guard: can't scale a zero vector
            self.vel.scale_to_length(settings.MIN_SPEED)

        self.pos += self.vel * dt

        # Python's % always returns a value in [0, WIDTH), even for negative numbers
        # (-5 % 1200 == 1195), so this single line wraps both edges.
        self.pos.x %= settings.WIDTH
        self.pos.y %= settings.HEIGHT

        self.acc.update(0, 0)                         # forces are re-summed every step

    def steer_towards(self, direction):
        """Steering force that turns this fish toward `direction` (any length)."""
        if direction.length_squared() == 0:
            return Vector2(0, 0)
        desired = direction.normalize() * settings.MAX_SPEED
        steer = desired - self.vel
        if steer.length_squared() > settings.MAX_FORCE ** 2:
            steer.scale_to_length(settings.MAX_FORCE)
        return steer

