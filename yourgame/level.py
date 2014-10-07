import itertools
import pygame
from pygame.sprite import groupcollide
from pygame.locals import *

from yourgame.scenes import Scene
from yourgame import resources
from yourgame import gui
from yourgame import hex_model
from yourgame import hex_view
from yourgame import entity
from yourgame import config
import os

__all__ = ['LevelScene']


class LevelSceneMode(object):
    """ provides various handlers to abstract gameplay into modes
    """
    def __init__(self):
        pass

    def handle_click(self, button, view, cell):
        pass

    def draw(self, surface):
        pass

    def update(self, delta, events):
        pass

class EditMode(LevelSceneMode):
    """
    states
    ======

    0 - show intro
    1 - no intro dialog
    """
    def __init__(self, scene):
        super(EditMode, self).__init__()
        self.border = gui.GraphicBox(resources.border_path, False)
        self.state = None
        self._font = pygame.font.Font(resources.fonts['rez'], 32)
        self._surface = None
        self._rect = None
        self._dialog = None

        self.sprite = scene.sprite

    def handle_click(self, button, view, cell):

        # left click
        if button == 1:
            if self.state == 0:
                self.change_state(1)

            elif self.state == 1:
                self.change_state(2)

            cell.raised = not cell.raised
            if cell.raised:
                cell.height = config.getint('display', 'wall_height')
                cell.filename = 'tileRock_full.png'
            else:
                cell.height = 0
                cell.filename = 'tileGrass.png'

            view.refresh_map = True

    def change_state(self, state):
        change = False
        if self.state is None and state == 0:
            self.state = state
            self._dialog = resources.get_text('editor mode intro')
            text = next(self._dialog)
            self.render_dialog(text)
            change = True

        elif self.state == 0 and state == 1:
            self.state = state
            self._surface = None
            change = True

        elif self.state == 1 and state == 2:
            self.state = state
            text = next(self._dialog)
            self.render_dialog(text)
            change = True

        elif self.state == 2 and state == 3:
            self.state = state
            self._surface = None
            self._dialog = None
            change = True

        if not change:
            raise ValueError("change to undefined state {} {}".format(
                self.state, state))

    def render_dialog(self, text):
        if self._rect is None:
            raise ValueError('cannot change state without video')

        sw, sh = self._rect.size
        rect = pygame.Rect(((0, 5), (sw, sh * .15))).inflate(-10, 0)
        tmp = pygame.Surface(rect.inflate(10, 10).size, pygame.SRCALPHA)
        self.border.draw(tmp, rect)
        gui.draw_text(tmp, text,
                      (255, 255, 255), rect.inflate(-20, -20),
                      self._font, True)
        self._surface = tmp

    def draw(self, surface):
        self._rect = surface.get_rect()

        dirty = list()

        if self.state is None:
            self.change_state(0)

        if self._surface:
            rect = surface.blit(self._surface, (0, 0))
            dirty.append(rect)

        return dirty

    def update(self, delta, events):
        moved = False
        pressed = pygame.key.get_pressed()
        if pressed[K_DOWN]:
            self.sprite.position.y += .1
            moved = True
        elif pressed[K_UP]:
            self.sprite.position.y -= .1
            moved = True
        if pressed[K_LEFT]:
            self.sprite.position.x -= .1
            moved = True
        elif pressed[K_RIGHT]:
            self.sprite.position.x += .1
            moved = True

        if moved and self.state == 2:
            self.change_state(3)


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
            #if coords in raised:
            #    cell.raised = True
            #    cell.height = 1
            #    cell.filename = 'tileRock_full.png'
            self.model.add_cell(coords, cell)
        blacklist = {(1, 0), (4, 3), (3, 4), (4, 4), (4, 5)}
        impassable = {} #{'grass'}
        for c in (i for i in self.model.pathfind_evenr(
                (0, 0), (5, 5), blacklist, impassable)[0]):
            self.model._data[c].raised = True
            self.model._data[c].height = 1
            cell.filename = 'tileRock_full.png'

        self.view = hex_view.HexMapView(self.model,
                                        config.getint('display', 'tile_size'))

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
        #surface.fill((0, 0, 0))

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
        c = groupcollide(self.view, self.view.data.walls(),
                         False, False, hex_model.collide_hex)

        self.mode.update(delta, events)

    def resume(self):
        print("Resuming level scene")

