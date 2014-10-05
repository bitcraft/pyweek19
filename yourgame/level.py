import pygame
from pygame import locals

from scenes import Scene
from level_model import *
from level_view import *
import os

__all__ = ['LevelScene']

tileset_path = os.path.join(os.path.dirname(__file__),
                            '..', 'data', 'tileset00.png')


class LevelScene(Scene):

    def __init__(self, game):
        super(LevelScene, self).__init__("level", game)
        tiles = pygame.image.load(tileset_path)
        self.model = LevelModel((20, 20), None)
        self.view = LevelView(self.model, 32, tiles)

    def setup(self):
        print("Setting up level scene")

    def teardown(self):
        print("Tearing down level scene")

    def draw(self, surface):
        self.view.draw(surface)

    def update(self, delta, events):
        pass

    def resume(self):
        print("Resuming level scene")

