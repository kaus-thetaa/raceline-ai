# car.py
# car physics, state, movement, and collision check against track

import math


class Car:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 0.0
        self.crashed = False

        self.max_speed = 6.0
        self.acceleration = 0.15
        self.brake_power = 0.3
        self.friction = 0.02
        self.turn_speed = 3.5

    def reset(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 0.0
        self.crashed = False

    def step(self, throttle, steer):
        if self.crashed:
            return

        # throttle in -1 to 1, negative brakes/reverses
        if throttle > 0:
            self.speed += self.acceleration * throttle
        elif throttle < 0:
            self.speed += self.brake_power * throttle

        # natural slowdown each frame
        if self.speed > 0:
            self.speed -= self.friction
        elif self.speed < 0:
            self.speed += self.friction

        self.speed = max(-self.max_speed / 2, min(self.max_speed, self.speed))

        # steer in -1 to 1, scaled by current speed so parked car cant turn
        speed_factor = self.speed / self.max_speed
        self.angle += steer * self.turn_speed * speed_factor

        radians = math.radians(self.angle)
        self.x += math.cos(radians) * self.speed
        self.y += math.sin(radians) * self.speed

    def check_collision(self, track):
        if not track.is_on_track(self.x, self.y):
            self.crashed = True
        return self.crashed

    def get_state(self):
        return {
            "x": self.x,
            "y": self.y,
            "angle": self.angle,
            "speed": self.speed,
            "crashed": self.crashed,
        }