# main.py
# entry point, trains with the pygame window visible so you can watch it learn

import os
import sys
import traceback

os.environ["SDL_VIDEO_WINDOW_POS"] = "50,50"

print("main.py starting")
print("python executable:", sys.executable)

try:
    import pygame
    print("pygame imported ok, version", pygame.version.ver)
except Exception:
    print("pygame import failed")
    traceback.print_exc()
    sys.exit(1)

try:
    pygame.init()
    print("pygame.init() done")
    screen = pygame.display.set_mode((1150, 650))
    print("display.set_mode() done, window should exist now")
    pygame.display.set_caption("raceline-ai training")
    screen.fill((0, 150, 0))
    pygame.display.flip()
    print("filled window green, check your screen and taskbar now")
    pygame.time.wait(3000)
    pygame.quit()
    print("closed test window, moving on to real training")
except Exception:
    print("pygame window setup failed")
    traceback.print_exc()
    sys.exit(1)

from train import train

if __name__ == "__main__":
    train(render=True)