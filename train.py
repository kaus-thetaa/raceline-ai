# train.py
# trains ppo agent on raceline env, saves model, updates live stats

import os
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import BaseCallback

from environment import RaceLineEnv
from stats import StatsTracker

TOTAL_TIMESTEPS = 500_000
MODEL_SAVE_PATH = "models/raceline_ppo"


class StatsCallback(BaseCallback):
    def __init__(self, tracker, verbose=0):
        super().__init__(verbose)
        self.tracker = tracker
        self.episode_count = 0

    def _on_step(self):
        infos = self.locals.get("infos", [])
        dones = self.locals.get("dones", [])

        for info, done in zip(infos, dones):
            self.tracker.record_step()

            if info.get("lap_completed"):
                self.tracker.record_lap()
                self.tracker.save()
                self.tracker.save_graph()

            if info.get("crashed"):
                self.tracker.record_crash()
                self.tracker.save()

            if done:
                self.episode_count += 1
                self.tracker.set_episode(self.episode_count)

        return True


def train(render=False, total_timesteps=TOTAL_TIMESTEPS):
    env = Monitor(RaceLineEnv())
    tracker = StatsTracker()
    callback = StatsCallback(tracker)

    model = PPO("MlpPolicy", env, verbose=1, device="cpu")
    model.learn(total_timesteps=total_timesteps, callback=callback)

    os.makedirs("models", exist_ok=True)
    model.save(MODEL_SAVE_PATH)

    tracker.save()
    tracker.save_graph()
    print("training complete, model saved to", MODEL_SAVE_PATH)

    return model, tracker


if __name__ == "__main__":
    train()