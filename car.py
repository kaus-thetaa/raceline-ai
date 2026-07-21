# car.py
# car physics, state, movement, collision check, f1 style rendering with camera offset

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

        self.max_speed = 8.0
        self.acceleration = 0.22
        self.brake_power = 0.45
        self.drag_coefficient = 0.0025
        self.rolling_resistance = 0.015
        self.turn_speed = 3.2
        self.corner_slip_threshold = 0.45
        self.corner_slip_factor = 0.06

        self.length = 34
        self.width = 16

    def reset(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 0.0
        self.crashed = False

    def step(self, throttle, steer):
        if self.crashed:
            return

        power_factor = max(0.0, 1 - (abs(self.speed) / self.max_speed))

        if throttle > 0:
            self.speed += self.acceleration * throttle * power_factor
        elif throttle < 0:
            self.speed += self.brake_power * throttle

        drag = self.drag_coefficient * self.speed * abs(self.speed)
        self.speed -= drag

        if self.speed > 0:
            self.speed = max(0.0, self.speed - self.rolling_resistance)
        elif self.speed < 0:
            self.speed = min(0.0, self.speed + self.rolling_resistance)

        if abs(steer) > self.corner_slip_threshold and self.speed > self.max_speed * 0.4:
            slip_penalty = abs(steer) * self.corner_slip_factor * self.speed
            self.speed -= slip_penalty

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

    def _to_screen(self, world_point, camera):
        return (world_point[0] - camera[0], world_point[1] - camera[1])

    def draw(self, surface, camera=(0, 0)):
        half_len = self.length / 2
        half_wid = self.width / 2

        body_points = [
            self._to_screen(self._rotated(half_len, 0), camera),
            self._to_screen(self._rotated(half_len * 0.4, half_wid), camera),
            self._to_screen(self._rotated(-half_len * 0.7, half_wid), camera),
            self._to_screen(self._rotated(-half_len * 0.7, -half_wid), camera),
            self._to_screen(self._rotated(half_len * 0.4, -half_wid), camera),
        ]
        color = (90, 90, 90) if self.crashed else BODY_COLOR
        pygame.draw.polygon(surface, color, body_points)

        wing_points = [
            self._to_screen(self._rotated(-half_len, half_wid * 1.3), camera),
            self._to_screen(self._rotated(-half_len * 0.7, half_wid * 1.3), camera),
            self._to_screen(self._rotated(-half_len * 0.7, -half_wid * 1.3), camera),
            self._to_screen(self._rotated(-half_len, -half_wid * 1.3), camera),
        ]
        pygame.draw.polygon(surface, WING_COLOR, wing_points)

        front_wing_points = [
            self._to_screen(self._rotated(half_len * 0.5, half_wid * 1.4), camera),
            self._to_screen(self._rotated(half_len * 0.7, half_wid * 1.4), camera),
            self._to_screen(self._rotated(half_len * 0.7, -half_wid * 1.4), camera),
            self._to_screen(self._rotated(half_len * 0.5, -half_wid * 1.4), camera),
        ]
        pygame.draw.polygon(surface, WING_COLOR, front_wing_points)

        helmet_pos = self._to_screen(self._rotated(-half_len * 0.1, 0), camera)
        pygame.draw.circle(surface, HELMET_COLOR, (int(helmet_pos[0]), int(helmet_pos[1])), 4)

        wheel_offsets = [
            (half_len * 0.5, half_wid * 1.1),
            (half_len * 0.5, -half_wid * 1.1),
            (-half_len * 0.5, half_wid * 1.1),
            (-half_len * 0.5, -half_wid * 1.1),
        ]
        for offset_x, offset_y in wheel_offsets:
            wheel_pos = self._to_screen(self._rotated(offset_x, offset_y), camera)
            pygame.draw.circle(surface, WHEEL_COLOR, (int(wheel_pos[0]), int(wheel_pos[1])), 4)