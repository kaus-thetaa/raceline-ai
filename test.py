from environment import RaceLineEnv

env = RaceLineEnv()
obs, info = env.reset()
print("starting observation:", obs)

for i in range(10):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"step {i} reward {reward:.3f} terminated {terminated}")
    if terminated or truncated:
        break