# car.py
# car physics, state, movement, collision check, f1 style rendering

import math
import pygame

BODY_COLOR = (200, 20, 20)
WING_COLOR = (20, 20, 20)
WHEEL_COLOR = (15, 15, 15)
HELMET_COLOR = (240, 240, 240)


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

        self.length = 26
        self.width = 12

    def reset(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 0.0
        self.crashed = False

    def step(self, throttle, steer):
        if self.crashed:
            return

        if throttle > 0:
            self.speed += self.acceleration * throttle
        elif throttle < 0:
            self.speed += self.brake_power * throttle

        if self.speed > 0:
            self.speed -= self.friction
        elif self.speed < 0:
            self.speed += self.friction

        self.speed = max(-self.max_speed / 2, min(self.max_speed, self.speed))

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

    def _rotated(self, local_x, local_y):
        radians = math.radians(self.angle)
        cos_a = math.cos(radians)
        sin_a = math.sin(radians)
        world_x = self.x + local_x * cos_a - local_y * sin_a
        world_y = self.y + local_x * sin_a + local_y * cos_a
        return (world_x, world_y)

    def draw(self, surface):
        half_len = self.length / 2
        half_wid = self.width / 2

        # main body, nose pointed forward along local x axis
        body_points = [
            self._rotated(half_len, 0),
            self._rotated(half_len * 0.4, half_wid),
            self._rotated(-half_len * 0.7, half_wid),
            self._rotated(-half_len * 0.7, -half_wid),
            self._rotated(half_len * 0.4, -half_wid),
        ]
        color = (90, 90, 90) if self.crashed else BODY_COLOR
        pygame.draw.polygon(surface, color, body_points)

        # rear wing
        wing_points = [
            self._rotated(-half_len, half_wid * 1.3),
            self._rotated(-half_len * 0.7, half_wid * 1.3),
            self._rotated(-half_len * 0.7, -half_wid * 1.3),
            self._rotated(-half_len, -half_wid * 1.3),
        ]
        pygame.draw.polygon(surface, WING_COLOR, wing_points)

        # front wing
        front_wing_points = [
            self._rotated(half_len * 0.5, half_wid * 1.4),
            self._rotated(half_len * 0.7, half_wid * 1.4),
            self._rotated(half_len * 0.7, -half_wid * 1.4),
            self._rotated(half_len * 0.5, -half_wid * 1.4),
        ]
        pygame.draw.polygon(surface, WING_COLOR, front_wing_points)

        # helmet, small circle just behind center
        helmet_pos = self._rotated(-half_len * 0.1, 0)
        pygame.draw.circle(surface, HELMET_COLOR, (int(helmet_pos[0]), int(helmet_pos[1])), 3)

        # four wheels as small dark rectangles at each corner
        wheel_offsets = [
            (half_len * 0.5, half_wid * 1.1),
            (half_len * 0.5, -half_wid * 1.1),
            (-half_len * 0.5, half_wid * 1.1),
            (-half_len * 0.5, -half_wid * 1.1),
        ]
        for offset_x, offset_y in wheel_offsets:
            wheel_pos = self._rotated(offset_x, offset_y)
            pygame.draw.circle(surface, WHEEL_COLOR, (int(wheel_pos[0]), int(wheel_pos[1])), 3)