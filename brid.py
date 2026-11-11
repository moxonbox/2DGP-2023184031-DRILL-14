"""Side-view bird flight; positions and velocities use metres and seconds."""

from pico2d import load_image


PIXELS_PER_METER = 10.0 / 0.3
CRUISE_SPEED = 6.0
FLOCK_SIZE = 10
FRAME_WIDTH, FRAME_HEIGHT = 183, 168
FRAME_COLUMNS, FRAME_COUNT = 5, 14
DRAW_WIDTH, DRAW_HEIGHT = 66, 60


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
        self.phase = index / FLOCK_SIZE
        self.flap_hz = 4.0 + (index % 3) * 0.12
        self.frame = self.phase * FRAME_COUNT

    def animate(self, dt):
        self.phase = (self.phase + self.flap_hz * dt) % 1.0
        self.frame = self.phase * FRAME_COUNT

    def draw(self):
        column = int(self.frame) % FRAME_COLUMNS
        row = int(self.frame) // FRAME_COLUMNS
        Bird.image.clip_composite_draw(
            column * FRAME_WIDTH,
            Bird.image.h - (row + 1) * FRAME_HEIGHT,
            FRAME_WIDTH, FRAME_HEIGHT, 0.0,
            'h' if self.face_dir < 0 else '',
            self.x * PIXELS_PER_METER, self.y * PIXELS_PER_METER,
            DRAW_WIDTH, DRAW_HEIGHT,
        )
