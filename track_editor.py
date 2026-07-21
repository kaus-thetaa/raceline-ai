# track_editor.py
# click to draw a custom track, save it, used by training instead of default circuit

import json
import os
import pygame

SAVE_PATH = "data/custom_track.json"
POINT_COLOR = (255, 200, 0)
LINE_COLOR = (150, 150, 150)
BACKGROUND_COLOR = (18, 18, 18)


def main():
    pygame.init()
    screen = pygame.display.set_mode((1150, 650))
    pygame.display.set_caption("raceline-ai track editor")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    points = []
    saved = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                points.append(event.pos)
                saved = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z:
                    if points:
                        points.pop()
                        saved = False

                elif event.key == pygame.K_s:
                    if len(points) >= 3:
                        save_track(points)
                        saved = True
                    else:
                        print("need at least 3 points before saving")

                elif event.key == pygame.K_ESCAPE:
                    running = False

        screen.fill(BACKGROUND_COLOR)
        draw_editor(screen, font, points, saved)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def draw_editor(surface, font, points, saved):
    if len(points) >= 2:
        pygame.draw.lines(surface, LINE_COLOR, False, points, 2)

    for point in points:
        pygame.draw.circle(surface, POINT_COLOR, point, 5)

    status = "saved" if saved else "not saved"
    help_text = f"click to add point, z to undo, s to save, esc to quit  |  points {len(points)}  |  {status}"
    text_surface = font.render(help_text, True, (230, 230, 230))
    surface.blit(text_surface, (10, 10))


def save_track(points):
    os.makedirs("data", exist_ok=True)
    data = {"points": points}

    with open(SAVE_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print("track saved to", SAVE_PATH, "with", len(points), "points")


if __name__ == "__main__":
    main()