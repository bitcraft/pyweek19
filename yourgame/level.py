import itertools
import pygame
from pygame.locals import *

from yourgame.scenes import Scene
from yourgame import hex_model
from yourgame import hex_view
from yourgame import entity
import os

__all__ = ['LevelScene']

tileset_path = os.path.join(os.path.dirname(__file__),
                            '..', 'data', 'tileset00.png')


class LevelScene(Scene):

    def __init__(self, game):
        super(LevelScene, self).__init__("level", game)

        # these coordinates are a bit wonky, the draw order hack messes it up
        self.model = hex_model.HexMapModel()
        for q, r in itertools.product(range(10), range(10)):
            coords = hex_model.evenr_to_axial((r, q))
            cell = hex_model.Cell()
            cell.filename = 'tileDirt.png'
            #if coords in raised:
            #    cell.raised = True
            #    cell.filename = 'tileRock_full.png'
            self.model.add_cell(coords, cell)
        print(self.model._data)
        for c in (i for i in self.model.pathfind((0, 0), (5, 5))[0]):
            print(c, self.model._data[c])
            #print(self.model._data[c])

            self.model._data[hex_model.evenr_to_axial(c)].raised = True

        self.view = hex_view.HexMapView(self.model, 32)

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

    def handle_click(self, cell):
        cell.raised = not cell.raised
        if cell.raised:
            cell.filename = 'tileRock_full.png'
        else:
            cell.filename = 'tileDirt.png'

    def update(self, delta, events):
        for event in events:
            if event.type == MOUSEMOTION:
                cell = self.get_nearest_cell(event.pos)
                if cell:
                    self.view.highlight_cell(cell)

                #if event.buttons[0]:
                #    self.view.tilt = 90 - (event.pos[1] / 540.0 * 90)

            if event.type == MOUSEBUTTONUP:
                cell = self.get_nearest_cell(event.pos)
                if cell:
                    self.handle_click(cell)

        pressed = pygame.key.get_pressed()
        if pressed[K_DOWN]:
            self.sprite.position.y += .1
        elif pressed[K_UP]:
            self.sprite.position.y -= .1
        if pressed[K_LEFT]:
            self.sprite.position.x -= .1
        elif pressed[K_RIGHT]:
            self.sprite.position.x += .1

    def resume(self):
        print("Resuming level scene")

