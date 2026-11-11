from math import pi, hypot, sin, tau

from pico2d import *
from sdl2 import (SDL_KEYDOWN, SDL_KEYUP, SDLK_LEFT, SDLK_RIGHT,
                  SDLK_SPACE)
from transitions import Machine

import game_world
from ball import Ball

import game_framework

PIXEL_PER_METER = (10.0 / 0.3) # pixel / cm
RUN_SPEED_KMPH = 20.0 # Km/h
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

STRIDE_LENGTH_M = 1.8 # 보폭
RUN_FRAMES_PER_STRIDE = 5
RUN_FRAMES_PER_SECOND = RUN_SPEED_MPS / STRIDE_LENGTH_M * RUN_FRAMES_PER_STRIDE



class Idle:
    def enter(self, boy):
        boy.idle_started_at = get_time()
        boy.frame = 0

    def do(self, boy):
        if get_time() - boy.idle_started_at >= 5.0:
            boy.fall_asleep()
        else:
            boy.frame = (boy.frame + 1) % 8

    def draw(self, boy):
        row = 300 if boy.face_dir == 1 else 200
        boy.image.clip_draw(boy.frame * 100, row, 100, 100, boy.x, boy.y)

    def space(self, boy):
        boy.fire_ball()

    def move(self, boy):
        boy.start_run()


class Sleep:
    def enter(self, boy):
        boy.frame = 0

    def do(self, boy):
        pass

    def draw(self, boy):
        angle = pi / 2 if boy.face_dir == 1 else -pi / 2
        flip = '' if boy.face_dir == 1 else 'h'
        boy.image.clip_composite_draw(
            boy.frame * 100, 300, 100, 100,
            angle, flip, boy.x, boy.y - 30, 100, 100
        )

    def space(self, boy):
        boy.wake_up()

    def move(self, boy):
        boy.start_run()


class Run:
    def enter(self, boy):
        boy.frame = 0

    def do(self, boy):
        boy.frame = (boy.frame * RUN_FRAMES_PER_SECOND * game_framework.frame_time) % 8
        boy.x += boy.dir * RUN_SPEED_PPS * game_framework.frame_time
        boy.x = max(25, min(get_canvas_width() - 25, boy.x))

    def draw(self, boy):
        row = 100 if boy.face_dir == 1 else 0
        boy.image.clip_draw(int(boy.frame) * 100, row, 100, 100, boy.x, boy.y)

    def space(self, boy):
        boy.fire_ball()

    def move(self, boy):
        pass


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.image = load_image('animation_sheet.png')
        self.idle_started_at = get_time()
        self.dir = 0
        self.face_dir = 1
        self.pressed_keys = set()
        self.item = 'Ball'

        self.font = load_font('ENCR10B.TTF', 16)

        self.states = {'IDLE': Idle(), 'SLEEP': Sleep(), 'RUN': Run()}

        self.machine = Machine(
            model=self,
            states=['IDLE', 'SLEEP', 'RUN'],
            transitions=[
                {'trigger': 'fall_asleep',
                 'source': 'IDLE', 'dest': 'SLEEP'},
                {'trigger': 'wake_up',
                 'source': 'SLEEP', 'dest': 'IDLE'},
                {'trigger': 'start_run',
                 'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},
                {'trigger': 'stop_run',
                 'source': 'RUN', 'dest': 'IDLE'},
            ],
            initial='IDLE',
            auto_transitions=False,
        )

    def on_enter_IDLE(self):
        self.states['IDLE'].enter(self)

    def on_enter_SLEEP(self):
        self.states['SLEEP'].enter(self)

    def on_enter_RUN(self):
        self.states['RUN'].enter(self)

    def fire_ball(self):
        if self.item is None:
            return
        ball = Ball(self.x, self.y, self.face_dir * 10, 1 if self.item == 'Ball' else 2)
        game_world.add_oject(ball)

    def pause(self):
        self.pressed_keys.clear()
        if self.state == 'RUN':
            self.dir = 0
            self.stop_run()

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            self.states[self.state].space(self)
            return

        if (event.type not in (SDL_KEYDOWN, SDL_KEYUP) or
                event.key not in (SDLK_LEFT, SDLK_RIGHT)):
            return

        if event.type == SDL_KEYDOWN:
            self.pressed_keys.add(event.key)
        else:
            self.pressed_keys.discard(event.key)

        direction = (int(SDLK_RIGHT in self.pressed_keys) -
                     int(SDLK_LEFT in self.pressed_keys))

        if direction != 0:
            self.dir = direction
            self.face_dir = direction
            self.states[self.state].move(self)
        elif self.state == 'RUN':
            self.dir = 0
            self.stop_run()

    def update(self):
        self.states[self.state].do(self)

    def draw(self):
        self.states[self.state].draw(self)
        self.font.draw(self.x - 60, self.y + 50, f'(Time: {get_time():.2f})', (255, 255, 0))


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
MAX_STEERING = 12.0
SEPARATION_RADIUS = 2.4
NEIGHBOR_RADIUS = 6.0
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

    def flocking(self, neighbors):
        ax, ay = 0.0, 0.0
        count, velocity_x, velocity_y = 0, 0.0, 0.0
        center_x, center_y = 0.0, 0.0
        for other in neighbors:
            if other is self:
                continue
            dx, dy = self.x - other.x, self.y - other.y
            distance = hypot(dx, dy)
            if distance < NEIGHBOR_RADIUS:
                count += 1
                velocity_x += other.vx
                velocity_y += other.vy
                center_x += other.x
                center_y += other.y
            if distance < SEPARATION_RADIUS:
                if distance < 1e-8:
                    # Give coincident birds opposite escape directions.
                    dx, dy = (1.0 if self.index > other.index else -1.0), 0.0
                    distance = 1.0
                strength = 8.0 * (SEPARATION_RADIUS - distance) / SEPARATION_RADIUS
                ax += dx / distance * strength
                ay += dy / distance * strength
        if count:
            ax += 0.8 * (velocity_x / count - self.vx)
            ay += 0.8 * (velocity_y / count - self.vy)
            ax += 0.35 * (center_x / count - self.x)
            ay += 0.35 * (center_y / count - self.y)
        return ax, ay

    def steering(self, direction, altitude, neighbors=()):
        ax = 2.0 * (direction * CRUISE_SPEED - self.vx)
        ay = 2.4 * (altitude - self.y) - 2.0 * self.vy
        flock_x, flock_y = self.flocking(neighbors)
        ax, ay = ax + flock_x, ay + flock_y
        length = hypot(ax, ay)
        if length > MAX_STEERING:
            ax, ay = ax * MAX_STEERING / length, ay * MAX_STEERING / length
        return ax, ay

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


class Flock:
    def __init__(self):
        self.width = get_canvas_width() / PIXELS_PER_METER
        self.height = get_canvas_height() / PIXELS_PER_METER
        self.altitude = self.height * 0.62
        self.direction = 1
        self.birds = [Bird(
            self.width * 0.35 + (i % 5 - 2) * 2.4,
            self.altitude + (i // 5 - 0.5) * 2.0, i,
        ) for i in range(FLOCK_SIZE)]

    def step(self, dt):
        # Read every bird before moving any bird to avoid update-order bias.
        steering = [bird.steering(self.direction, self.altitude, self.birds)
                    for bird in self.birds]
        for bird, force in zip(self.birds, steering):
            bird.step(dt, force)

    def draw(self):
        for bird in self.birds:
            bird.draw()
