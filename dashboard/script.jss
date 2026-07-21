// dashboard/script.js
// fetches live stats, fills cards, draws graph, plays lap replay

const STATS_URL = "../data/live_stats.json";
const REPLAY_URL = "../data/best_lap_replay.json";
const TRACK_URL = "../data/track_shape.json";
const STATS_REFRESH_MS = 5000;
const REPLAY_REFRESH_MS = 30000;
const REPLAY_FRAME_MS = 30;

let trackData = null;
let replayData = null;
let replayFrame = 0;

function formatLapTime(seconds) {
  if (seconds === null || seconds === undefined) return "-";
  return seconds.toFixed(2) + "s";
}

function updateStatCards(stats) {
  document.getElementById("stat-episode").textContent = stats.current_episode ?? "-";
  document.getElementById("stat-crashes").textContent = stats.total_crashes ?? "-";
  document.getElementById("stat-laps").textContent = stats.total_laps ?? "-";
  document.getElementById("stat-first-lap").textContent = formatLapTime(stats.first_lap_time);
  document.getElementById("stat-best-lap").textContent = formatLapTime(stats.best_lap_time);
}

function updateLastUpdated(updatedAt) {
  const el = document.getElementById("last-updated");
  if (!updatedAt) {
    el.textContent = "waiting for data";
    return;
  }
  const date = new Date(updatedAt * 1000);
  el.textContent = "last updated " + date.toLocaleString();
}

function drawLapGraph(lapTimes) {
  const canvas = document.getElementById("lap-chart");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!lapTimes || lapTimes.length === 0) return;

  const padding = 30;
  const width = canvas.width - padding * 2;
  const height = canvas.height - padding * 2;

  const maxTime = Math.max(...lapTimes);
  const minTime = Math.min(...lapTimes);
  const range = maxTime - minTime || 1;

  const pointX = (index) => padding + (index / (lapTimes.length - 1 || 1)) * width;
  const pointY = (time) => padding + height - ((time - minTime) / range) * height;

  ctx.strokeStyle = "#e63030";
  ctx.lineWidth = 2;
  ctx.beginPath();
  lapTimes.forEach((time, index) => {
    const x = pointX(index);
    const y = pointY(time);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = "#e63030";
  lapTimes.forEach((time, index) => {
    ctx.beginPath();
    ctx.arc(pointX(index), pointY(time), 3, 0, Math.PI * 2);
    ctx.fill();
  });
}

async function fetchStats() {
  try {
    const response = await fetch(STATS_URL + "?t=" + Date.now());
    if (!response.ok) throw new Error("stats fetch failed");
    const stats = await response.json();

    updateStatCards(stats);
    drawLapGraph(stats.lap_times);
    updateLastUpdated(stats.updated_at);
  } catch (error) {
    console.error("could not load live stats", error);
  }
}

function getReplayBounds(track) {
  const allPoints = track.outer.concat(track.inner);
  const xs = allPoints.map((p) => p[0]);
  const ys = allPoints.map((p) => p[1]);
  return {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys),
  };
}

function getReplayTransform(track, canvas) {
  const bounds = getReplayBounds(track);
  const trackWidth = bounds.maxX - bounds.minX;
  const trackHeight = bounds.maxY - bounds.minY;
  const margin = 40;

  const scale = Math.min(
    (canvas.width - margin * 2) / trackWidth,
    (canvas.height - margin * 2) / trackHeight
  );

  const toCanvas = (point) => [
    margin + (point[0] - bounds.minX) * scale,
    margin + (point[1] - bounds.minY) * scale,
  ];

  return toCanvas;
}

function drawReplayTrack(ctx, track, toCanvas) {
  ctx.strokeStyle = "#444444";
  ctx.lineWidth = 2;

  [track.outer, track.inner].forEach((points) => {
    ctx.beginPath();
    points.forEach((point, index) => {
      const [x, y] = toCanvas(point);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.stroke();
  });
}

function drawReplayCar(ctx, position, toCanvas) {
  const [x, y] = toCanvas(position);
  const angle = position[2] || 0;

  ctx.save();
  ctx.translate(x, y);
  ctx.rotate((angle * Math.PI) / 180);

  ctx.fillStyle = "#e63030";
  ctx.beginPath();
  ctx.moveTo(8, 0);
  ctx.lineTo(-6, 5);
  ctx.lineTo(-6, -5);
  ctx.closePath();
  ctx.fill();

  ctx.restore();
}

function drawReplay() {
  const canvas = document.getElementById("replay-canvas");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!trackData || !replayData || replayData.positions.length === 0) return;

  const toCanvas = getReplayTransform(trackData, canvas);
  drawReplayTrack(ctx, trackData, toCanvas);

  const position = replayData.positions[replayFrame];
  drawReplayCar(ctx, position, toCanvas);

  replayFrame = (replayFrame + 1) % replayData.positions.length;
}

async function fetchReplay() {
  try {
    const trackResponse = await fetch(TRACK_URL + "?t=" + Date.now());
    const replayResponse = await fetch(REPLAY_URL + "?t=" + Date.now());

    if (!trackResponse.ok || !replayResponse.ok) return;

    trackData = await trackResponse.json();
    replayData = await replayResponse.json();
    replayFrame = 0;
  } catch (error) {
    console.error("no replay data available yet", error);
  }
}

fetchStats();
fetchReplay();
setInterval(fetchStats, STATS_REFRESH_MS);
setInterval(fetchReplay, REPLAY_REFRESH_MS);
setInterval(drawReplay, REPLAY_FRAME_MS);