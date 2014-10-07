import itertools
import pygame
from pygame.sprite import groupcollide
from pygame.locals import *

from yourgame.scenes import Scene
from yourgame import hex_model
from yourgame import hex_view
from yourgame import entity
from yourgame import config
from yourgame import resources
from yourgame.modes.editor import EditMode

__all__ = ['LevelScene']


class LevelScene(Scene):

    def __init__(self, game):
        super(LevelScene, self).__init__("level", game)

        # these coordinates are a bit wonky, the draw order hack messes it up
        raised = ((2, 3), (4, 5), (1, 7))
        self.model = hex_model.HexMapModel()
        for q, r in itertools.product(range(10), range(10)):
            coords = hex_model.evenr_to_axial((r, q))
            cell = hex_model.Cell()
            cell.filename = 'tileGrass.png'
            cell.kind = 'grass'
            if coords in raised:
                cell.raised = True
                cell.height = 1
                cell.filename = 'tileRock_full.png'
            self.model.add_cell(coords, cell)

        # blacklist = {(1, 0), (4, 4)}
        # impassable = {} #{'grass'}
        # for c in (i for i in self.model.pathfind_evenr(
        #         (0, 0), (5, 5), blacklist, impassable)[0]):
        #     self.model._data[c].raised = True
        #     self.model._data[c].height = 1
        #     cell.filename = 'tileRock_full.png'

        self.view = hex_view.HexMapView(self.model,
                                        config.getint('display', 'tile_size'))

        self.velocity_updates = entity.PhysicsGroup()

        sprite = entity.GameEntity()
        sprite.position.x = 0
        sprite.position.y = 0
        self.view.add(sprite)
        sprite = entity.GameEntity()
        sprite.position.x = 5
        sprite.position.y = 5
        self.view.add(sprite)
        sprite = entity.GameEntity()
        sprite.position.x = 7
        sprite.position.y = 2
        self.view.add(sprite)
        sprite = entity.GameEntity()
        sprite.position.x = 9
        sprite.position.y = 9
        self.view.add(sprite)
        sprite = entity.GameEntity()
        sprite.position.x = 2
        sprite.position.y = 7
        self.view.add(sprite)

        self.sprite = sprite
        self.velocity_updates.add(sprite)

        # this must come last
        self.mode = EditMode(self)

    def setup(self):
        print("Setting up level scene")

    def teardown(self):
        print("Tearing down level scene")

    def get_nearest_cell(self, coords):
        point = self.view.point_from_surface(coords)
        if point:
            return self.view.data.get_nearest_cell(point)

    # fix this
    once = False

    def draw(self, surface):
        if not self.once:
            surface.blit(resources.images["backdrop"], (0, 0))
            self.once = True

        dirty = self.view.draw(surface)
        dirty.extend(self.mode.draw(surface))
        return dirty

    def clear(self, surface):
        self.view.clear(surface)

    def handle_click(self, button, cell):
        self.mode.handle_click(button, self.view, cell)

    def update(self, delta, events):
        for event in events:
            if event.type == MOUSEMOTION:
                cell = self.get_nearest_cell(event.pos)
                if cell:
                    self.view.highlight_cell(cell)

            if event.type == MOUSEBUTTONUP:
                cell = self.get_nearest_cell(event.pos)
                if cell:
                    self.handle_click(event.button, cell)

        # collisions
        #c = groupcollide(self.view, self.view.data.walls(),
        #                 False, False, hex_model.collide_hex)

        self.mode.update(delta, events)
        self.velocity_updates.update(delta)

    def resume(self):
        print("Resuming level scene")

