# stats.py
# tracks live training stats, writes json, saves lap graph and best lap replay

import json
import os
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

STATS_FILE_PATH = "data/live_stats.json"
GRAPH_FILE_PATH = "data/lap_times.png"
REPLAY_FILE_PATH = "data/best_lap_replay.json"
TRACK_SHAPE_PATH = "data/track_shape.json"
FRAMES_PER_SECOND = 60


class StatsTracker:
    def __init__(self, file_path=STATS_FILE_PATH):
        self.file_path = file_path
        self.total_crashes = 0
        self.total_laps = 0
        self.first_lap_time = None
        self.best_lap_time = None
        self.current_episode = 0
        self.lap_times = []
        self.steps_this_lap = 0
        self.current_lap_positions = []
        self.training_start_time = time.time()

    def record_step(self):
        self.steps_this_lap += 1

    def record_position(self, x, y, angle):
        self.current_lap_positions.append([x, y, angle])

    def record_crash(self):
        self.total_crashes += 1
        self.steps_this_lap = 0
        self.current_lap_positions = []

    def record_lap(self):
        lap_time = self.steps_this_lap / FRAMES_PER_SECOND
        self.total_laps += 1
        self.lap_times.append(lap_time)

        is_new_best = self.best_lap_time is None or lap_time < self.best_lap_time

        if self.first_lap_time is None:
            self.first_lap_time = lap_time

        if is_new_best:
            self.best_lap_time = lap_time
            self._save_replay()

        self.steps_this_lap = 0
        self.current_lap_positions = []
        return lap_time

    def set_episode(self, episode_number):
        self.current_episode = episode_number

    def get_current_lap_time(self):
        return self.steps_this_lap / FRAMES_PER_SECOND

    def get_total_elapsed(self):
        return time.time() - self.training_start_time

    def _save_replay(self):
        if not self.current_lap_positions:
            return

        data = {"positions": self.current_lap_positions}

        os.makedirs(os.path.dirname(REPLAY_FILE_PATH), exist_ok=True)
        with open(REPLAY_FILE_PATH, "w") as f:
            json.dump(data, f)

    def export_track_shape(self, track, path=TRACK_SHAPE_PATH):
        data = {
            "outer": [list(point) for point in track.outer_points],
            "inner": [list(point) for point in track.inner_points],
        }

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)

    def save(self):
        data = {
            "total_crashes": self.total_crashes,
            "total_laps": self.total_laps,
            "first_lap_time": self.first_lap_time,
            "best_lap_time": self.best_lap_time,
            "current_episode": self.current_episode,
            "lap_times": self.lap_times,
            "updated_at": time.time(),
        }

        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)

    def save_graph(self, image_path=GRAPH_FILE_PATH):
        if not self.lap_times:
            return

        plt.figure(figsize=(8, 4))
        plt.plot(self.lap_times, color="#e63030", linewidth=2)
        plt.title("lap time improvement")
        plt.xlabel("lap number")
        plt.ylabel("lap time seconds")
        plt.grid(alpha=0.3)

        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        plt.savefig(image_path)
        plt.close()