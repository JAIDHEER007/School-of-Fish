# ---------------- Window ----------------
WIDTH, HEIGHT = 1200, 800
FPS_CAP = 60
BG_COLOR = (10, 30, 50)

# ---------------- Simulation ----------------
SIM_DT = 1.0 / 60.0          # fixed timestep in seconds (Step 8)
MAX_STEPS_PER_FRAME = 5      # protects against the "spiral of death" (Step 8)
NUM_FISH = 400
SEED = 42                    # same seed → same starting positions every run

# Units: pixels and seconds. Speeds are px/s, forces (accelerations) are px/s².
MIN_SPEED = 40.0
MAX_SPEED = 120.0
MAX_FORCE = 200.0            # max steering acceleration per rule

PERCEPTION_RADIUS = 65.0     # neighbors within this distance count for align/cohesion
SEPARATION_RADIUS = 25.0     # neighbors closer than this push the fish away

# Default weights (the sliders start here)
SEPARATION_WEIGHT = 1.5
ALIGNMENT_WEIGHT = 1.0
COHESION_WEIGHT = 1.0
WANDER_STRENGTH = 20.0       # size of the random nudge, px/s²

# ---------------- Drawing ----------------
FISH_SIZE = 8                # nose-to-center length in pixels
