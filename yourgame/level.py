import itertools
import pygame
from pygame import locals

from scenes import Scene
from yourgame import hex_model
from yourgame import hex_view
import os

__all__ = ['LevelScene']

tileset_path = os.path.join(os.path.dirname(__file__),
                            '..', 'data', 'tileset00.png')


class LevelScene(Scene):

    def __init__(self, game):
        super(LevelScene, self).__init__("level", game)

        self.model = hex_model.HexMapModel()
        for coords in itertools.product(range(20), range(20)):
            coords = hex_model.oddr_to_axial(coords)
            self.model.add_cell(coords, hex_model.Cell())

        #tiles = pygame.image.load(tileset_path)
        tiles = None
        self.view = hex_view.HexMapView(self.model, 128, tiles)

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

