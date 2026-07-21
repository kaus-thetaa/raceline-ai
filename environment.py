# environment.py
# gymnasium environment wrapping track and car, now with look ahead and wall sensors

import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces

from track import Track
from car import Car

LOOKAHEAD_FRACTIONS = [0.02, 0.05, 0.09]
SENSOR_ANGLES = [-90, -45, 0, 45, 90]
SENSOR_MAX_RANGE = 200


class RaceLineEnv(gym.Env):
    def __init__(self):
        super().__init__()

        self.track = Track()
        self.car = Car(*self.track.start_pos, math.degrees(self.track.start_angle))

        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
        )

        # speed, heading diff, offset, progress, 3 lookahead angles, 5 wall sensors
        obs_size = 4 + len(LOOKAHEAD_FRACTIONS) + len(SENSOR_ANGLES)
        self.observation_space = spaces.Box(
            low=np.full(obs_size, -1.0, dtype=np.float32),
            high=np.full(obs_size, 1.0, dtype=np.float32),
        )

        self.max_steps = 6000
        self.current_step = 0
        self.last_progress = 0.0
        self.next_checkpoint = 1
        self.laps_completed = 0
        self.crash_count = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.car.reset(*self.track.start_pos, math.degrees(self.track.start_angle))
        self.current_step = 0
        self.last_progress = 0.0
        self.next_checkpoint = 1

        observation = self._get_observation()
        info = {}
        return observation, info

    def step(self, action):
        throttle = float(action[0])
        steer = float(action[1])

        self.car.step(throttle, steer)
        self.car.check_collision(self.track)
        self.current_step += 1

        index, t, distance = self.track.locate(self.car.x, self.car.y)
        progress = self._progress_from_locate(index, t)

        lap_completed = self._check_checkpoint(index)
        reward = self._compute_reward(progress, lap_completed)

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

    def _progress_from_locate(self, index, t):
        length_so_far = self.track.cumulative[index] + t * self.track.segment_lengths[index]
        return length_so_far / self.track.total_length

    def _check_checkpoint(self, current_index):
        checkpoint_count = self.track.checkpoint_count()

        if current_index == self.next_checkpoint:
            self.next_checkpoint = (self.next_checkpoint + 1) % checkpoint_count

            if self.next_checkpoint == 1:
                return True

        return False

    def _compute_reward(self, progress, lap_completed):
        delta = progress - self.last_progress

        if abs(delta) > 0.3:
            delta = 0.0

        reward = delta * 100

        if self.car.crashed:
            reward -= 10

        if lap_completed:
            reward += 50

        return reward

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
        progress = self._progress_from_locate(index, t)

        base_features = [normalized_speed, normalized_heading_diff, normalized_offset, progress]
        lookahead_features = self._get_lookahead_features(progress, car_heading)
        sensor_features = self._get_sensor_features()

        return np.array(base_features + lookahead_features + sensor_features, dtype=np.float32)