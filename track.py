# track.py
# procedurally generated f1 style circuit, difficulty scales from easy to hard for curriculum learning

import math
import random
import pygame

GRASS_LIGHT = (36, 96, 50)
GRASS_DARK = (30, 86, 44)
GRAVEL_COLOR = (196, 172, 128)
ASPHALT_COLOR = (42, 42, 46)
CURB_COLORS = [(210, 30, 30), (235, 235, 235)]
CENTERLINE_COLOR = (255, 255, 255)
GRANDSTAND_COLOR = (90, 90, 100)
GRANDSTAND_ROOF_COLOR = (60, 60, 70)
TREE_COLOR = (20, 70, 35)

GRAVEL_MARGIN = 30
STRIPE_HEIGHT = 180

# easy tracks are short, wide, gentle loops, hard tracks are the full sized twisty circuits
EASY_SETTINGS = {"min_points": 7, "max_points": 8, "radius_jitter": 120, "base_radius": 850, "track_width": 140}
HARD_SETTINGS = {"min_points": 10, "max_points": 16, "radius_jitter": 550, "base_radius": 1600, "track_width": 90}


class Track:
    def __init__(self, difficulty=1.0):
        # difficulty 0 is easiest, 1 is the full hard circuit, callers can pass anything between
        difficulty = max(0.0, min(1.0, difficulty))
        settings = self._interpolate_settings(difficulty)

        self.track_width = settings["track_width"]
        self.centerline = self._generate_random_centerline(settings)
        self.outer_points, self.inner_points = self._build_boundaries()
        self.gravel_points = self._build_gravel_boundary()
        self.segment_lengths, self.cumulative, self.total_length = self._build_progress_table()
        self.start_pos, self.start_angle = self._build_start()
        self.tree_spots = self._build_tree_spots()

    def _interpolate_settings(self, difficulty):
        def lerp(easy_val, hard_val):
            return easy_val + (hard_val - easy_val) * difficulty

        return {
            "min_points": round(lerp(EASY_SETTINGS["min_points"], HARD_SETTINGS["min_points"])),
            "max_points": round(lerp(EASY_SETTINGS["max_points"], HARD_SETTINGS["max_points"])),
            "radius_jitter": lerp(EASY_SETTINGS["radius_jitter"], HARD_SETTINGS["radius_jitter"]),
            "base_radius": lerp(EASY_SETTINGS["base_radius"], HARD_SETTINGS["base_radius"]),
            "track_width": lerp(EASY_SETTINGS["track_width"], HARD_SETTINGS["track_width"]),
        }

    def _generate_random_centerline(self, settings, center=(0, 0)):
        num_points = random.randint(settings["min_points"], settings["max_points"])
        angle_step = (2 * math.pi) / num_points
        points = []

        for i in range(num_points):
            angle = i * angle_step + random.uniform(-0.3, 0.3) * angle_step
            radius = settings["base_radius"] + random.uniform(-settings["radius_jitter"], settings["radius_jitter"])
            x = center[0] + math.cos(angle) * radius
            y = center[1] + math.sin(angle) * radius
            points.append((x, y))

        for _ in range(2):
            points = self._smooth_points(points)

        return points

    def _smooth_points(self, points):
        count = len(points)
        smoothed = []

        for i in range(count):
            prev_point = points[i - 1]
            current_point = points[i]
            next_point = points[(i + 1) % count]
            avg_x = (prev_point[0] + current_point[0] + next_point[0]) / 3
            avg_y = (prev_point[1] + current_point[1] + next_point[1]) / 3
            smoothed.append((avg_x, avg_y))

        return smoothed

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

    def _build_tree_spots(self, count=10, min_offset=180, max_offset=380):
        spots = []
        point_count = len(self.centerline)

        for _ in range(count):
            index = random.randrange(point_count)
            base_point = self.centerline[index]
            prev_point = self.centerline[index - 1]
            next_point = self.centerline[(index + 1) % point_count]

            dx = next_point[0] - prev_point[0]
            dy = next_point[1] - prev_point[1]
            length = math.hypot(dx, dy) or 1
            perp_x = -dy / length
            perp_y = dx / length

            side = random.choice([-1, 1])
            offset = random.uniform(min_offset, max_offset)
            x = base_point[0] + perp_x * offset * side
            y = base_point[1] + perp_y * offset * side
            spots.append((x, y))

        return spots

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

    def is_on_track(self, x, y):
        _, _, distance = self.locate(x, y)
        return distance <= self.track_width / 2

    def get_progress(self, x, y):
        index, t, _ = self.locate(x, y)
        length_so_far = self.cumulative[index] + t * self.segment_lengths[index]
        return length_so_far / self.total_length

    def point_at_progress(self, fraction):
        fraction = fraction % 1.0
        target_length = fraction * self.total_length
        count = len(self.centerline)

        for i in range(count):
            if self.cumulative[i + 1] >= target_length:
                segment_start = self.cumulative[i]
                segment_progress = (target_length - segment_start) / self.segment_lengths[i]
                a = self.centerline[i]
                b = self.centerline[(i + 1) % count]
                x = a[0] + (b[0] - a[0]) * segment_progress
                y = a[1] + (b[1] - a[1]) * segment_progress
                heading = math.atan2(b[1] - a[1], b[0] - a[0])
                return (x, y), heading

        a = self.centerline[-1]
        b = self.centerline[0]
        heading = math.atan2(b[1] - a[1], b[0] - a[0])
        return a, heading

    def sensor_distance(self, x, y, angle_degrees, max_range=200, step=8):
        radians = math.radians(angle_degrees)
        dx = math.cos(radians)
        dy = math.sin(radians)

        distance = 0.0
        while distance < max_range:
            check_x = x + dx * distance
            check_y = y + dy * distance
            if not self.is_on_track(check_x, check_y):
                return distance
            distance += step

        return max_range

    def _to_screen(self, point, camera):
        return (point[0] - camera[0], point[1] - camera[1])

    def _translate(self, points, camera):
        return [self._to_screen(p, camera) for p in points]

    def _draw_grass_stripes(self, surface, camera):
        width, height = surface.get_size()
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