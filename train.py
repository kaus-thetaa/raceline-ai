# train.py
# trains ppo agent on raceline env, saves model, updates live stats

import os
import pygame
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback

from environment import RaceLineEnv
from stats import StatsTracker

TOTAL_TIMESTEPS = 500_000
MODEL_SAVE_PATH = "models/raceline_ppo"
CHECKPOINT_DIR = "models/checkpoints"
CHECKPOINT_FREQUENCY = 10_000
SCREEN_SIZE = (1150, 650)

HUD_LABEL_COLOR = (170, 170, 170)
HUD_VALUE_COLOR = (255, 255, 255)
HUD_BEST_COLOR = (120, 220, 140)
HUD_PANEL_COLOR = (10, 10, 10, 165)
HUD_PANEL_SIZE = (250, 220)


def format_time(seconds):
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"


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
            self.tracker.record_position(info.get("x", 0), info.get("y", 0), info.get("angle", 0))

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


class RenderCallback(BaseCallback):
    def __init__(self, screen, tracker, verbose=0):
        super().__init__(verbose)
        self.screen = screen
        self.tracker = tracker
        self.clock = pygame.time.Clock()
        self.label_font = pygame.font.SysFont("consolas", 14)
        self.value_font = pygame.font.SysFont("consolas", 22, bold=True)
        self.panel = pygame.Surface(HUD_PANEL_SIZE, pygame.SRCALPHA)
        self.panel.fill(HUD_PANEL_COLOR)

    def _on_step(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("render window closed by user, stopping training")
                return False

        env = self.training_env.envs[0].unwrapped

        screen_w, screen_h = self.screen.get_size()
        camera = (env.car.x - screen_w / 2, env.car.y - screen_h / 2)

        env.track.draw(self.screen, camera)
        env.car.draw(self.screen, camera)
        self._draw_hud(env)
        pygame.display.flip()
        self.clock.tick(60)

        return True

    def _draw_row(self, label, value, y, color=HUD_VALUE_COLOR):
        label_surface = self.label_font.render(label, True, HUD_LABEL_COLOR)
        value_surface = self.value_font.render(value, True, color)
        self.panel.blit(label_surface, (16, y))
        self.panel.blit(value_surface, (16, y + 16))

    def _draw_hud(self, env):
        best_lap = self.tracker.best_lap_time
        best_lap_text = f"{best_lap:.2f}s" if best_lap is not None else "-"

        self.panel.fill(HUD_PANEL_COLOR)

        self._draw_row("episode", str(self.tracker.current_episode), 10)
        self._draw_row("crashes", str(self.tracker.total_crashes), 60)
        self._draw_row("laps completed", str(self.tracker.total_laps), 110)
        self._draw_row("current lap time", format_time(self.tracker.get_current_lap_time()), 160)
        self._draw_row("best lap", best_lap_text, 210, color=HUD_BEST_COLOR)

        self.screen.blit(self.panel, (10, 10))

        total_time_text = "total time " + format_time(self.tracker.get_total_elapsed())
        total_surface = self.label_font.render(total_time_text, True, HUD_LABEL_COLOR)
        self.screen.blit(total_surface, (10, HUD_PANEL_SIZE[1] + 20))

        speed_text = f"speed {env.car.speed:.1f}"
        speed_surface = self.label_font.render(speed_text, True, HUD_LABEL_COLOR)
        self.screen.blit(speed_surface, (10, HUD_PANEL_SIZE[1] + 40))


def train(render=False, total_timesteps=TOTAL_TIMESTEPS):
    raw_env = RaceLineEnv()
    tracker = StatsTracker()
    tracker.export_track_shape(raw_env.track)

    env = Monitor(raw_env)

    checkpoint_callback = CheckpointCallback(
        save_freq=CHECKPOINT_FREQUENCY,
        save_path=CHECKPOINT_DIR,
        name_prefix="raceline_ppo",
    )
    callbacks = [StatsCallback(tracker), checkpoint_callback]

    screen = None
    if render:
        pygame.init()
        screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("raceline-ai training")
        callbacks.append(RenderCallback(screen, tracker))

    model = PPO("MlpPolicy", env, verbose=1, device="cpu")

    try:
        model.learn(total_timesteps=total_timesteps, callback=callbacks)
    except KeyboardInterrupt:
        print("training interrupted, saving progress so far")
    finally:
        os.makedirs("models", exist_ok=True)
        model.save(MODEL_SAVE_PATH)
        tracker.save()
        tracker.save_graph()
        print("model saved to", MODEL_SAVE_PATH)

        if render:
            pygame.quit()

    return model, tracker


if __name__ == "__main__":
    train()