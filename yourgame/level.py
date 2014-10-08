import itertools
import pygame
from pygame.sprite import Group
from pygame.sprite import groupcollide
from pygame.locals import *

from yourgame.scenes import Scene
from yourgame import hex_model
from yourgame import hex_view
from yourgame import entity
from yourgame.environ import maze
from yourgame import config
from yourgame import resources
from yourgame.modes.editor import EditMode
from yourgame.euclid import Point2

__all__ = ['LevelScene']


class LevelScene(Scene):

    def __init__(self, game):
        super(LevelScene, self).__init__("level", game)

        self.damage = list()
        self.needs_refresh = True
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
                cell.height = config.getint('display', 'wall_height')
                cell.filename = 'tileRock_full.png'
                cell.kind = 'rock'
            self.model.add_cell(coords, cell)

        maze.build_maze_from_hex(self.model,
                                 lower_limit=(1, 1),
                                 upper_limit=(self.model.width-2, self.model.height-2),
                                 height=1.0,
                                 raised_tile='tileRock_full.png',
                                 lowered_tile='tileGrass.png',
                                 num_adjacent=1)

        self.view = hex_view.HexMapView(self, self.model,
                                        config.getint('display', 'tile_size'))

        self.velocity_updates = entity.PhysicsGroup()
        self.internal_event_group = pygame.sprite.Group()

        sprite = entity.GameEntity('alienBlue.png')
        sprite.position.x = 0
        sprite.position.y = 0
        self.view.add(sprite)
        sprite = entity.GameEntity('alienBlue.png')
        sprite.position.x = 7
        sprite.position.y = 2
        self.view.add(sprite)
        sprite = entity.GameEntity('alienBlue.png')
        sprite.position.x = 9
        sprite.position.y = 9
        self.view.add(sprite)
        sprite = entity.GameEntity('alienBlue.png')
        sprite.position.x = 2
        sprite.position.y = 7
        self.view.add(sprite)
        self.internal_event_group.add(sprite)

        self.sprite = sprite
        self.velocity_updates.add(sprite)

        # "switch"
        button = entity.Button('tileRock_tile.png')
        button.position.x = 2
        button.position.y = 5
        button.anchor = Point2(33, 30)
        self.view.add(button, layer=0)
        self.internal_event_group.add(button)

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

    def draw(self, surface):
        dirty = list()
        refreshed = False

        if self.needs_refresh:
            surface.blit(resources.images["backdrop"], (0, 0))
            dirty = [surface.get_rect()]
            self.view.needs_refresh = True
            self.mode.needs_refresh = True
            self.needs_refresh = False
            refreshed = True

        _dirty = self.view.draw(surface)
        if _dirty:
            if not refreshed:
                dirty.extend(_dirty)

            damage = _dirty[0].unionall(_dirty)
            if self.damage:
                if damage.colliderect(self.damage):
                    self.mode.needs_refresh = True

        _dirty = self.mode.draw(surface)
        if _dirty:
            if not refreshed:
                dirty.extend(_dirty)

            self.damage = _dirty[0].unionall(_dirty)

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

        # collisions with walls (broken!)
        #c = groupcollide(self.view, self.view.data.walls(),
        #                 False, False, hex_model.collide_hex)

        self.mode.update(delta, events)

        for sprite in self.internal_event_group:
            if hasattr(sprite, "handle_internal_events"):
                sprite.handle_internal_events(self)

        self.internal_event_group.update(self)
        self.velocity_updates.update(delta)
        self.view.test_sprite_collisions()

    def resume(self):
        print("Resuming level scene")

