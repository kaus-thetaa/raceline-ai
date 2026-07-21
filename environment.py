# environment.py
# gymnasium environment wrapping track and car for ppo training

import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces

from track import Track
from car import Car


class RaceLineEnv(gym.Env):
    def __init__(self):
        super().__init__()

        self.track = Track()
        self.car = Car(*self.track.start_pos, math.degrees(self.track.start_angle))

        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
        )

        self.observation_space = spaces.Box(
            low=np.array([-1.0, -1.0, -1.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
        )

        self.max_steps = 2000
        self.current_step = 0
        self.last_progress = 0.0
        self.laps_completed = 0
        self.crash_count = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.car.reset(*self.track.start_pos, math.degrees(self.track.start_angle))
        self.current_step = 0
        self.last_progress = 0.0

        observation = self._get_observation()
        info = {}
        return observation, info

    def step(self, action):
        throttle = float(action[0])
        steer = float(action[1])

        self.car.step(throttle, steer)
        self.car.check_collision(self.track)
        self.current_step += 1

        progress = self.track.get_progress(self.car.x, self.car.y)
        reward, lap_completed = self._compute_reward(progress)

        terminated = self.car.crashed
        truncated = self.current_step >= self.max_steps

        if terminated:
            self.crash_count += 1

        if lap_completed:
            self.laps_completed += 1

        self.last_progress = progress

        observation = self._get_observation()
        info = {
            "lap_completed": lap_completed,
            "crashed": terminated,
            "progress": progress,
            "x": self.car.x,
            "y": self.car.y,
            "angle": self.car.angle,
        }
        return observation, reward, terminated, truncated, info

    def _compute_reward(self, progress):
        delta = progress - self.last_progress

        lap_completed = False
        if delta < -0.5:
            delta += 1.0
            lap_completed = True

        reward = delta * 100

        if self.car.crashed:
            reward -= 10

        if lap_completed:
            reward += 50

        return reward, lap_completed

    def _get_observation(self):
        index, t, distance = self.track._locate(self.car.x, self.car.y)
        a = self.track.centerline[index]
        b = self.track.centerline[(index + 1) % len(self.track.centerline)]
        track_heading = math.atan2(b[1] - a[1], b[0] - a[0])

        car_heading = math.radians(self.car.angle)
        heading_diff = math.atan2(math.sin(car_heading - track_heading), math.cos(car_heading - track_heading))

        normalized_speed = self.car.speed / self.car.max_speed
        normalized_heading_diff = heading_diff / math.pi
        normalized_offset = max(-1.0, min(1.0, distance / (self.track.track_width / 2)))
        progress = self.track.get_progress(self.car.x, self.car.y)

        return np.array(
            [normalized_speed, normalized_heading_diff, normalized_offset, progress],
            dtype=np.float32,
        )