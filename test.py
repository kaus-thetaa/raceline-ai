from environment import RaceLineEnv

env = RaceLineEnv()
print("using track with", len(env.track.centerline), "points")