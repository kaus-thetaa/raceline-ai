# track.py
# hardcoded f1 style circuit, tuned for a roughly 10 second lap

import math
import pygame

GRASS_COLOR = (24, 90, 43)
ASPHALT_COLOR = (42, 42, 46)
BOUNDARY_COLOR = (235, 235, 235)
CURB_COLORS = [(210, 30, 30), (235, 235, 235)]
CENTERLINE_COLOR = (255, 255, 255)


class Track:
    def __init__(self, track_width=65):
        self.track_width = track_width
        self.centerline = self._build_centerline()
        self.outer_points, self.inner_points = self._build_boundaries()
        self.segment_lengths, self.cumulative, self.total_length = self._build_progress_table()
        self.start_pos, self.start_angle = self._build_start()

    def _build_centerline(self):
        # compact circuit with a hairpin style turn and a chicane, tuned for around 10s laps
        return [
            (200, 480),
            (200, 320),
            (260, 220),
            (380, 160),
            (520, 170),
            (580, 240),
            (520, 300),
            (620, 340),
            (780, 260),
            (900, 300),
            (930, 420),
            (830, 500),
            (650, 520),
            (450, 520),
            (300, 500),
        ]

    def _build_boundaries(self):
        outer = []
        inner = []
        points = self.centerline
        count = len(points)
        half = self.track_width / 2

        for i in range(count):
            prev_point = points[i - 1]
            next_point = points[(i + 1) % count]

            dx = next_point[0] - prev_point[0]
            dy = next_point[1] - prev_point[1]
            length = math.hypot(dx, dy)
            if length == 0:
                length = 1

            perp_x = -dy / length
            perp_y = dx / length

            cx, cy = points[i]
            outer.append((cx + perp_x * half, cy + perp_y * half))
            inner.append((cx - perp_x * half, cy - perp_y * half))

        return outer, inner

    def _build_progress_table(self):
        points = self.centerline
        count = len(points)
        segment_lengths = []
        cumulative = [0.0]

        for i in range(count):
            a = points[i]
            b = points[(i + 1) % count]
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            segment_lengths.append(length)
            cumulative.append(cumulative[-1] + length)

        total_length = cumulative[-1]
        return segment_lengths, cumulative, total_length

    def _build_start(self):
        a = self.centerline[0]
        b = self.centerline[1]
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        return a, angle

    def _closest_on_segment(self, px, py, ax, ay, bx, by):
        seg_dx = bx - ax
        seg_dy = by - ay
        seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy
        if seg_len_sq == 0:
            return ax, ay, 0.0

        t = ((px - ax) * seg_dx + (py - ay) * seg_dy) / seg_len_sq
        t = max(0.0, min(1.0, t))

        closest_x = ax + t * seg_dx
        closest_y = ay + t * seg_dy
        return closest_x, closest_y, t

    def _locate(self, x, y):
        points = self.centerline
        count = len(points)
        best_distance = None
        best_index = 0
        best_t = 0.0

        for i in range(count):
            a = points[i]
            b = points[(i + 1) % count]
            cx, cy, t = self._closest_on_segment(x, y, a[0], a[1], b[0], b[1])
            distance = math.hypot(x - cx, y - cy)

            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_index = i
                best_t = t

        return best_index, best_t, best_distance

    def is_on_track(self, x, y):
        _, _, distance = self._locate(x, y)
        return distance <= self.track_width / 2

    def get_progress(self, x, y):
        index, t, _ = self._locate(x, y)
        length_so_far = self.cumulative[index] + t * self.segment_lengths[index]
        return length_so_far / self.total_length

    def _draw_curbs(self, surface, points):
        count = len(points)
        for i in range(count):
            a = points[i]
            b = points[(i + 1) % count]
            color = CURB_COLORS[i % 2]
            pygame.draw.line(surface, color, a, b, 6)

    def _draw_center_dashes(self, surface):
        dash_length = 14
        gap_length = 12
        points = self.centerline
        count = len(points)

        for i in range(count):
            a = points[i]
            b = points[(i + 1) % count]
            segment_length = math.hypot(b[0] - a[0], b[1] - a[1])
            if segment_length == 0:
                continue

            step = dash_length + gap_length
            dash_count = int(segment_length // step)

            for d in range(dash_count):
                t1 = (d * step) / segment_length
                t2 = t1 + (dash_length / segment_length)
                x1 = a[0] + (b[0] - a[0]) * t1
                y1 = a[1] + (b[1] - a[1]) * t1
                x2 = a[0] + (b[0] - a[0]) * t2
                y2 = a[1] + (b[1] - a[1]) * t2
                pygame.draw.line(surface, CENTERLINE_COLOR, (x1, y1), (x2, y2), 3)

    def _draw_start_line(self, surface):
        outer = self.outer_points[0]
        inner = self.inner_points[0]
        steps = 6

        for i in range(steps):
            t1 = i / steps
            t2 = (i + 1) / steps
            x1 = outer[0] + (inner[0] - outer[0]) * t1
            y1 = outer[1] + (inner[1] - outer[1]) * t1
            x2 = outer[0] + (inner[0] - outer[0]) * t2
            y2 = outer[1] + (inner[1] - outer[1]) * t2
            color = (20, 20, 20) if i % 2 == 0 else (240, 240, 240)
            pygame.draw.line(surface, color, (x1, y1), (x2, y2), 8)

    def draw(self, surface):
        surface.fill(GRASS_COLOR)
        pygame.draw.polygon(surface, ASPHALT_COLOR, self.outer_points)
        pygame.draw.polygon(surface, GRASS_COLOR, self.inner_points)
        self._draw_curbs(surface, self.outer_points)
        self._draw_curbs(surface, self.inner_points)
        self._draw_center_dashes(surface)
        self._draw_start_line(surface)