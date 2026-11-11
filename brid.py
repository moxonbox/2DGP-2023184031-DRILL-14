"""Side-view bird flight; positions and velocities use metres and seconds."""

from math import hypot, sin, tau

from pico2d import load_image


PIXELS_PER_METER = 10.0 / 0.3
CRUISE_SPEED = 6.0
GRAVITY = 9.81
MASS = 0.08
AIR_DENSITY = 1.225
WING_AREA = 0.025
DRAG_COEFFICIENT = 0.14
WING_AIRSPEED = 5.0
MAX_LIFT_COEFFICIENT = 2.4
MAX_THRUST = 1.0
PRESSURE_AREA = 0.5 * AIR_DENSITY * WING_AREA
CRUISE_DRAG = PRESSURE_AREA * DRAG_COEFFICIENT * CRUISE_SPEED ** 2
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

    def acceleration(self, steering):
        speed = hypot(self.vx, self.vy)
        drag_x = -PRESSURE_AREA * DRAG_COEFFICIENT * speed * self.vx
        drag_y = -PRESSURE_AREA * DRAG_COEFFICIENT * speed * self.vy
        downstroke = sin(tau * self.phase)
        thrust = max(-MAX_THRUST, min(MAX_THRUST,
            (MASS * steering[0] + self.face_dir * CRUISE_DRAG)
            * (1.0 + 0.08 * downstroke)))
        trim_pressure = PRESSURE_AREA * (CRUISE_SPEED ** 2 + WING_AIRSPEED ** 2)
        lift_coefficient = max(0.0, min(MAX_LIFT_COEFFICIENT,
            MASS * (GRAVITY + steering[1]) / trim_pressure))
        # Wing motion supplies airflow even while forward speed drops in a turn.
        lift = (PRESSURE_AREA * (speed ** 2 + WING_AIRSPEED ** 2)
                * lift_coefficient * (1.0 + 0.12 * downstroke))
        return ((thrust + drag_x) / MASS,
                (lift + drag_y) / MASS - GRAVITY)

    def step(self, dt, steering=(0.0, 0.0)):
        ax, ay = self.acceleration(steering)
        self.vx += ax * dt
        self.vy += ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if abs(self.vx) > 0.1:
            self.face_dir = 1 if self.vx > 0.0 else -1
        self.animate(dt)

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
