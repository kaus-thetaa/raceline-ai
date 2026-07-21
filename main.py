# main.py
# entry point, trains with the pygame window visible so you can watch it learn

from train import train

if __name__ == "__main__":
    train(render=True)