# test_window.py
# minimal check that pygame can open a window at all

import pygame

pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("test window")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((0, 150, 0))
    pygame.display.flip()

pygame.quit()