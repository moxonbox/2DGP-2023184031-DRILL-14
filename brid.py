"""Side-view bird flight; positions and velocities use metres and seconds."""

from pico2d import load_image


PIXELS_PER_METER = 10.0 / 0.3
CRUISE_SPEED = 6.0
FLOCK_SIZE = 10


class Bird:
    image = None

    def __init__(self, x, y, index=0):
        if Bird.image is None:
            Bird.image = load_image('bird_animation.png')
        self.x, self.y = x, y
        self.vx, self.vy = CRUISE_SPEED, 0.0
        self.index = index
        self.face_dir = 1
        self.frame = 0.0
