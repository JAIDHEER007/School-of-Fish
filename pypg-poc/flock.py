import random

from pygame.math import Vector2

import settings
from fish import Fish

PERCEPTION_SQ = settings.PERCEPTION_RADIUS ** 2
SEPARATION_SQ = settings.SEPARATION_RADIUS ** 2

def alignment(f, fishes):
    total = Vector2(0, 0)
    count = 0
    for other in fishes:
        if other is f:                                    # don't count yourself
            continue
        if (other.pos - f.pos).length_squared() < PERCEPTION_SQ:
            total += other.vel
            count += 1
    if count == 0:
        return Vector2(0, 0)
    return f.steer_towards(total / count)

def cohesion(f, fishes):
    center = Vector2(0, 0)
    count = 0
    for other in fishes:
        if other is f:
            continue
        if (other.pos - f.pos).length_squared() < PERCEPTION_SQ:
            center += other.pos
            count += 1
    if count == 0:
        return Vector2(0, 0)
    center /= count
    return f.steer_towards(center - f.pos)                # vector from me to the center


def separation(f, fishes):
    push = Vector2(0, 0)
    for other in fishes:
        if other is f:
            continue
        offset = f.pos - other.pos                        # points AWAY from the neighbor
        d2 = offset.length_squared()
        if 0 < d2 < SEPARATION_SQ:                         # 0 < : skip exact overlaps (÷0)
            push += offset / d2
    return f.steer_towards(push)

def wander(rng):
    return Vector2(rng.uniform(-1, 1), rng.uniform(-1, 1)) * settings.WANDER_STRENGTH

class Flock:
    def __init__(self, n, seed):
        self.rng = random.Random(seed)
        self.fishes = [Fish.random(self.rng) for _ in range(n)]

        # Live-tunable weights (the sliders will write into these).
        self.separation_weight = settings.SEPARATION_WEIGHT
        self.alignment_weight = settings.ALIGNMENT_WEIGHT
        self.cohesion_weight = settings.COHESION_WEIGHT

    def step(self, dt):
        fishes = self.fishes

        for f in fishes:
            push = Vector2(0, 0)          # separation accumulator
            vel_sum = Vector2(0, 0)       # alignment accumulator
            pos_sum = Vector2(0, 0)       # cohesion accumulator
            count = 0

            for other in fishes:
                if other is f:
                    continue
                offset = f.pos - other.pos
                d2 = offset.length_squared()
                if d2 >= PERCEPTION_SQ:
                    continue              # not a neighbor: skip everything
                count += 1
                vel_sum += other.vel
                pos_sum += other.pos
                if 0 < d2 < SEPARATION_SQ:
                    push += offset / d2

            acc = Vector2(0, 0)
            if count > 0:
                acc += f.steer_towards(vel_sum / count) * self.alignment_weight
                acc += f.steer_towards(pos_sum / count - f.pos) * self.cohesion_weight
            acc += f.steer_towards(push) * self.separation_weight
            acc += wander(self.rng)
            f.acc = acc

        for f in fishes:
            f.update(dt)

    def draw(self, surface):
        for f in self.fishes:
            f.draw(surface)