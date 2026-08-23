# environment.py
# gymnasium environment, difficulty scales via curriculum, robust lap detection

import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces

from track import Track
from car import Car

LOOKAHEAD_FRACTIONS = [0.02, 0.05, 0.09]
SENSOR_ANGLES = [-90, -45, 0, 45, 90]
SENSOR_MAX_RANGE = 200
LAP_MIN_PROGRESS = 0.7


class RaceLineEnv(gym.Env):
    def __init__(self):
        super().__init__()

        self.difficulty = 1.0
        self.track = Track(difficulty=self.difficulty)
        self.car = Car(*self.track.start_pos, math.degrees(self.track.start_angle))

        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
        )

        obs_size = 4 + len(LOOKAHEAD_FRACTIONS) + len(SENSOR_ANGLES)
        self.observation_space = spaces.Box(
            low=np.full(obs_size, -1.0, dtype=np.float32),
            high=np.full(obs_size, 1.0, dtype=np.float32),
        )

        self.max_steps = 6000
        self.current_step = 0
        self.last_progress = 0.0
        self.max_progress_reached = 0.0
        self.laps_completed = 0
        self.crash_count = 0

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.track = Track(difficulty=self.difficulty)
        self.car.reset(*self.track.start_pos, math.degrees(self.track.start_angle))
        self.current_step = 0
        self.last_progress = 0.0
        self.max_progress_reached = 0.0

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

        if lap_completed:
            info["track_outer"] = [list(p) for p in self.track.outer_points]
            info["track_inner"] = [list(p) for p in self.track.inner_points]

        return observation, reward, terminated, truncated, info

    def _compute_reward(self, progress):
        # check the real, unmodified delta for a lap wrap before any clipping touches it
        raw_delta = progress - self.last_progress
        self.max_progress_reached = max(self.max_progress_reached, progress)

        lap_completed = raw_delta < -0.5 and self.max_progress_reached >= LAP_MIN_PROGRESS

        if lap_completed:
            # unwrap the jump into the small genuine forward step it actually represents
            delta = 1.0 + raw_delta
            self.max_progress_reached = 0.0
        elif abs(raw_delta) > 0.3:
            # a large jump that isn't a real lap is a geometry glitch, not real movement
            delta = 0.0
        else:
            delta = raw_delta

        reward = delta * 100

        if self.car.crashed:
            reward -= 10

        if lap_completed:
            reward += 50

        return reward, lap_completed

    def _get_lookahead_features(self, current_progress, car_heading_radians):
        features = []
        for fraction in LOOKAHEAD_FRACTIONS:
            _, future_heading = self.track.point_at_progress(current_progress + fraction)
            heading_diff = math.atan2(
                math.sin(future_heading - car_heading_radians),
                math.cos(future_heading - car_heading_radians),
            )
            features.append(heading_diff / math.pi)
        return features

    def _get_sensor_features(self):
        features = []
        for relative_angle in SENSOR_ANGLES:
            world_angle = self.car.angle + relative_angle
            distance = self.track.sensor_distance(self.car.x, self.car.y, world_angle, SENSOR_MAX_RANGE)
            features.append((distance / SENSOR_MAX_RANGE) * 2 - 1)
        return features

    def _get_observation(self):
        index, t, distance = self.track.locate(self.car.x, self.car.y)
        a = self.track.centerline[index]
        b = self.track.centerline[(index + 1) % len(self.track.centerline)]
        track_heading = math.atan2(b[1] - a[1], b[0] - a[0])

        car_heading = math.radians(self.car.angle)
        heading_diff = math.atan2(math.sin(car_heading - track_heading), math.cos(car_heading - track_heading))

        normalized_speed = self.car.speed / self.car.max_speed
        normalized_heading_diff = heading_diff / math.pi
        normalized_offset = max(-1.0, min(1.0, distance / (self.track.track_width / 2)))
        progress = self.track.get_progress(self.car.x, self.car.y)

        base_features = [normalized_speed, normalized_heading_diff, normalized_offset, progress]
        lookahead_features = self._get_lookahead_features(progress, car_heading)
        sensor_features = self._get_sensor_features()

        return np.array(base_features + lookahead_features + sensor_features, dtype=np.float32)