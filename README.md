# RaceLine-AI

An F1 car that starts out knowing nothing, crashes constantly, and gradually learns the fastest racing line through reinforcement learning — with a live public dashboard showing its progress.

## What it does

- A simulated F1 car learns to drive a custom-built circuit from scratch, using PPO (Proximal Policy Optimization)
- It starts by crashing into the walls almost immediately, with no idea what throttle, braking, or steering even do
- Over time it learns to hold the racing line, brake before corners, and complete full laps
- A live dashboard on GitHub Pages shows total crashes, laps completed, first lap time, best lap time, an improvement graph, and an animated replay of the best lap so far

## Tech stack

- **Python 3.11+** — core language
- **PyGame** — track and car simulation, physics, rendering
- **Gymnasium** — the standard environment interface Stable-Baselines3 trains against
- **Stable-Baselines3 (PPO)** — the reinforcement learning algorithm
- **PyTorch** — neural network backend for PPO
- **NumPy** — math and array operations
- **FastAPI** — optional local server for live-viewing stats while training
- **Matplotlib** — offline lap time graph, saved as a PNG
- **GitHub Pages + vanilla HTML/CSS/JS** — the public dashboard, no frameworks

## Project structure

## Setup

```bash
git clone https://github.com/kaus-thetaa/raceline-ai.git
cd raceline-ai

python -m venv venv
venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Running it

**Train with the live pygame window** (watch it crash and learn in real time):

```bash
python main.py
```

**Train headless** (faster, no window, for longer unattended runs):

```bash
python train.py
```

**View stats locally while training** (optional, in a second terminal):

```bash
python api/server.py
```

Then open `http://localhost:8000/api/stats`.

## The public dashboard

The dashboard in `dashboard/` reads `data/live_stats.json`, `data/track_shape.json`, and `data/best_lap_replay.json` directly — no server required for viewers. After a training session, push the updated `data/` files to GitHub and the live dashboard reflects the latest run.

To enable it: repo **Settings → Pages → Deploy from a branch → main → /dashboard**. GitHub will give you a public URL to share.

## How the car learns

Every frame, the car observes its speed, how misaligned it is from the track direction, how far off-center it is, and how far around the lap it's gotten. It outputs throttle and steering. Reward comes from forward progress along the track, a penalty for crashing, and a bonus for completing a full lap. Over thousands of episodes, PPO gradually shifts the car's behavior toward whatever earns the most reward — which, in practice, looks like learning to actually race.

## Physics notes

The car isn't just clamped to a max speed — it has drag that grows with speed squared, rolling resistance, engine power that fades near top speed, and corners that cost speed if taken too fast, mimicking real tire grip limits. This means holding a fast lap actually requires braking before corners, not just holding full throttle.