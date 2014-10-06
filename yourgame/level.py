import itertools
import pygame
from pygame.locals import *

from yourgame.scenes import Scene
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
        for q, r in itertools.product(range(10), range(10)):
            coords = hex_model.evenr_to_axial((r, q))
            cell = hex_model.Cell()
            cell.filename = 'tileDirt.png'
            self.model.add_cell(coords, cell)

        self.view = hex_view.HexMapView(self.model, 32)

    def setup(self):
        print("Setting up level scene")

    def teardown(self):
        print("Tearing down level scene")

    def get_nearest_cell(self, coords):
        point = self.view.point_from_surface(coords)
        if point:
            return self.view.data.get_nearest_cell(point)

    def draw(self, surface):
        surface.fill((0, 0, 0))
        self.view.draw(surface)

    def update(self, delta, events):
        for event in events:
            if event.type == MOUSEMOTION:
                cell = self.get_nearest_cell(event.pos)
                if cell:
                    self.view.highlight_cell(cell)

                if event.buttons[0]:
                    self.view.tilt = 90 - (event.pos[1] / 540.0 * 90)

    def resume(self):
        print("Resuming level scene")

