from stats import StatsTracker

tracker = StatsTracker()
for _ in range(120):
    tracker.record_step()
tracker.record_lap()
tracker.record_crash()
tracker.set_episode(1)
tracker.save()
tracker.save_graph()

print("total laps:", tracker.total_laps)
print("first lap time:", tracker.first_lap_time)