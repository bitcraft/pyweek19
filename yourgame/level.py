import itertools
import pygame
from pygame.locals import *

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
        self.view = hex_view.HexMapView(self.model, 32, tiles)

    def setup(self):
        print("Setting up level scene")

    def teardown(self):
        print("Tearing down level scene")

    def get_nearest_cell(self, coords):
        pt = self.view.point_from_surface(coords)
        if pt:
            coords = hex_model.pixel_to_axial(pt, self.view.hex_radius)

        cell = None
        if coords:
            cell = self.view.data.get_nearest_cell(coords)

        return cell

    def draw(self, surface):
        surface.fill((0, 0, 0))
        self.view.draw(surface)

    def update(self, delta, events):
        for event in events:
            if event.type == MOUSEMOTION:
                cell = self.get_nearest_cell(event.pos)
                if cell:
                    self.view.highlight_cell(cell)

            elif event.type == MOUSEBUTTONUP:
                cell = self.get_nearest_cell(event.pos)
                if cell:
                    self.view.select_cell(cell)

    def resume(self):
        print("Resuming level scene")

