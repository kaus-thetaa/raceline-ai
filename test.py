import pygame
import math
from track import Track
from car import Car

pygame.init()
screen = pygame.display.set_mode((1100, 600))
track = Track()
car = Car(*track.start_pos, math.degrees(track.start_angle))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    throttle = 1 if keys[pygame.K_UP] else (-1 if keys[pygame.K_DOWN] else 0)
    steer = -1 if keys[pygame.K_LEFT] else (1 if keys[pygame.K_RIGHT] else 0)

    car.step(throttle, steer)
    car.check_collision(track)

    screen.fill((18, 18, 18))
    track.draw(screen)
    pygame.draw.circle(screen, (255, 200, 0), (int(car.x), int(car.y)), 6)
    pygame.display.flip()
    pygame.time.delay(16)

pygame.quit()