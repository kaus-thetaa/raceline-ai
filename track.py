# track.py
# hardcoded f1 style circuit, big world with camera scrolling, tuned for a long lap

import math
import pygame

GRASS_LIGHT = (34, 102, 51)
GRASS_DARK = (26, 88, 43)
GRAVEL_COLOR = (196, 172, 128)
ASPHALT_COLOR = (42, 42, 46)
CURB_COLORS = [(210, 30, 30), (235, 235, 235)]
CENTERLINE_COLOR = (255, 255, 255)
GRANDSTAND_COLOR = (90, 90, 100)
GRANDSTAND_ROOF_COLOR = (60, 60, 70)
TREE_COLOR = (20, 70, 35)

GRAVEL_MARGIN = 30
STRIPE_HEIGHT = 50


class Track:
    def __init__(self, track_width=90):
        self.track_width = track_width
        self.centerline = self._build_centerline()
        self.outer_points, self.inner_points = self._build_boundaries()
        self.gravel_points = self._build_gravel_boundary()
        self.segment_lengths, self.cumulative, self.total_length = self._build_progress_table()
        self.start_pos, self.start_angle = self._build_start()
        self.tree_spots = self._build_tree_spots()

    def _build_centerline(self):
        raw_points = [
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
        # scaled up 7x into a big world, far larger than one screen, so a lap takes real time
        return self._scale_points(raw_points, scale=7.0, center=(565, 340))

    def _scale_points(self, points, scale, center):
        scaled = []
        for x, y in points:
            new_x = center[0] + (x - center[0]) * scale
            new_y = center[1] + (y - center[1]) * scale
            scaled.append((new_x, new_y))
        return scaled

    def _offset_points(self, half_width):
        points = self.centerline
        count = len(points)
        offset = []

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
            offset.append((cx + perp_x * half_width, cy + perp_y * half_width))

        return offset

    def _build_boundaries(self):
        half = self.track_width / 2
        outer = self._offset_points(half)
        inner = self._offset_points(-half)
        return outer, inner

    def _build_gravel_boundary(self):
        half = (self.track_width / 2) + GRAVEL_MARGIN
        return self._offset_points(half)

    def _build_tree_spots(self):
        raw_spots = [
            (120, 150), (160, 550), (1000, 150), (1020, 560),
            (450, 90), (750, 590), (60, 350), (1080, 350),
        ]
        return self._scale_points(raw_spots, scale=7.0, center=(565, 340))

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

    def locate(self, x, y):
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

    # kept for anything still calling the old private name
    def _locate(self, x, y):
        return self.locate(x, y)

    def is_on_track(self, x, y):
        _, _, distance = self.locate(x, y)
        return distance <= self.track_width / 2

    def get_progress(self, x, y):
        index, t, _ = self.locate(x, y)
        length_so_far = self.cumulative[index] + t * self.segment_lengths[index]
        return length_so_far / self.total_length

    def checkpoint_count(self):
        return len(self.centerline)

    def _to_screen(self, point, camera):
        return (point[0] - camera[0], point[1] - camera[1])

    def _translate(self, points, camera):
        return [self._to_screen(p, camera) for p in points]

    def _draw_grass_stripes(self, surface, camera):
        width, height = surface.get_size()
        # offset the stripe pattern by the camera so the ground appears to scroll too
        start_offset = -(camera[1] % STRIPE_HEIGHT)
        stripe_count = int(height // STRIPE_HEIGHT) + 2

        for i in range(stripe_count):
            color = GRASS_LIGHT if i % 2 == 0 else GRASS_DARK
            y = start_offset + i * STRIPE_HEIGHT
            rect = pygame.Rect(0, int(y), width, STRIPE_HEIGHT)
            pygame.draw.rect(surface, color, rect)

    def _draw_trees(self, surface, camera):
        for point in self.tree_spots:
            x, y = self._to_screen(point, camera)
            pygame.draw.circle(surface, TREE_COLOR, (int(x), int(y)), 16)
            pygame.draw.circle(surface, TREE_COLOR, (int(x) + 12, int(y) + 8), 12)
            pygame.draw.circle(surface, TREE_COLOR, (int(x) - 12, int(y) + 10), 12)

    def _draw_grandstands(self, surface, camera):
        start_x, start_y = self._to_screen(self.start_pos, camera)
        stand_offset = self.track_width + 30

        stand_a = pygame.Rect(int(start_x) - 90, int(start_y) + stand_offset, 110, 50)
        stand_b = pygame.Rect(int(start_x) + 50, int(start_y) + stand_offset, 110, 50)

        for stand in (stand_a, stand_b):
            pygame.draw.rect(surface, GRANDSTAND_COLOR, stand)
            roof = pygame.Rect(stand.x - 4, stand.y - 8, stand.width + 8, 10)
            pygame.draw.rect(surface, GRANDSTAND_ROOF_COLOR, roof)

    def _draw_curbs(self, surface, points, camera):
        translated = self._translate(points, camera)
        count = len(translated)
        for i in range(count):
            a = translated[i]
            b = translated[(i + 1) % count]
            color = CURB_COLORS[i % 2]
            pygame.draw.line(surface, color, a, b, 8)

    def _draw_center_dashes(self, surface, camera):
        dash_length = 16
        gap_length = 14
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
                p1 = self._to_screen((x1, y1), camera)
                p2 = self._to_screen((x2, y2), camera)
                pygame.draw.line(surface, CENTERLINE_COLOR, p1, p2, 4)

    def _draw_start_line(self, surface, camera):
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
            p1 = self._to_screen((x1, y1), camera)
            p2 = self._to_screen((x2, y2), camera)
            pygame.draw.line(surface, color, p1, p2, 10)

    def draw(self, surface, camera=(0, 0)):
        self._draw_grass_stripes(surface, camera)
        self._draw_trees(surface, camera)
        self._draw_grandstands(surface, camera)

        pygame.draw.polygon(surface, GRAVEL_COLOR, self._translate(self.gravel_points, camera))
        pygame.draw.polygon(surface, ASPHALT_COLOR, self._translate(self.outer_points, camera))
        pygame.draw.polygon(surface, GRASS_DARK, self._translate(self.inner_points, camera))

        self._draw_curbs(surface, self.outer_points, camera)
        self._draw_curbs(surface, self.inner_points, camera)
        self._draw_center_dashes(surface, camera)
        self._draw_start_line(surface, camera)