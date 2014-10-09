from yourgame import resources
from yourgame import gui
from yourgame.modes.mode import LevelSceneMode
from yourgame import config
import pygame
from pygame.locals import *

__all__ = ['EditMode']


class EditMode(LevelSceneMode):
    """
    states
    ======

    0 - show intro
    1 - no intro dialog
    """
    def __init__(self, scene):
        super(EditMode, self).__init__()
        self.scene = scene
        self.border = gui.GraphicBox(resources.border_path, False)
        self.state = None
        self._font = pygame.font.Font(resources.fonts['rez'], 32)
        self.surface = None
        self.rect = None
        self._dialog = None
        self.needs_refresh = False

        self.sprite = scene.sprite

    def handle_click(self, button, cell):
        view = self.scene.view

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

            view.needs_refresh = True

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
            self.surface = None
            self.scene.needs_refresh = True
            change = True

        elif self.state == 1 and state == 2:
            self.state = state
            text = next(self._dialog)
            self.render_dialog(text)
            change = True

        elif self.state == 2 and state == 3:
            self.state = state
            self.surface = None
            self._dialog = None
            self.scene.needs_refresh = True
            change = True

        if not change:
            raise ValueError("change to undefined state {} {}".format(
                self.state, state))

    def render_dialog(self, text):
        if self.rect is None:
            raise ValueError('cannot change state without video')

        sw, sh = self.rect.size
        rect = pygame.Rect(((0, 5), (sw, sh * .15))).inflate(-10, 0)
        tmp = pygame.Surface(rect.inflate(10, 10).size, pygame.SRCALPHA)
        self.border.draw(tmp, rect)
        gui.draw_text(tmp, text,
                      (255, 255, 255), rect.inflate(-20, -20),
                      self._font, True)
        self.surface = tmp
        self.needs_refresh = True

    def draw(self, surface):
        self.rect = surface.get_rect()

        refreshed = False
        dirty = list()

        if self.state is None:
            self.change_state(0)

        if self.needs_refresh:
            if self.surface:
                rect = surface.blit(self.surface, (0, 0))
                dirty.append(rect)
            else:
                dirty.append(self.rect)
            self.needs_refresh = False
            refreshed = True

        return dirty

    def get_nearest_cell(self, coords):
        view = self.scene.view
        point = view.point_from_surface(coords)
        if point:
            return view.data.get_nearest_cell(point)

    def update(self, delta, events):
        view = self.scene.view

        for event in events:
            if event.type == MOUSEMOTION:
                cell = self.get_nearest_cell(event.pos)
                if cell:
                    view.highlight_cell(cell)

            if event.type == MOUSEBUTTONUP:
                cell = self.get_nearest_cell(event.pos)
                if cell:
                    self.handle_click(event.button, cell)

        moved = False
        pressed = pygame.key.get_pressed()
        movement_accel = config.getfloat('world', 'player_move_accel')

        if pressed[K_DOWN]:
            self.sprite.acceleration.y = movement_accel
            moved = True
        elif pressed[K_UP]:
            self.sprite.acceleration.y = -movement_accel
            moved = True
        else:
            self.sprite.acceleration.y = 0

        if pressed[K_LEFT]:
            self.sprite.acceleration.x = -movement_accel
            self.sprite.flipped = True
            moved = True
        elif pressed[K_RIGHT]:
            self.sprite.acceleration.x = movement_accel
            self.sprite.flipped = False
            moved = True
        else:
            self.sprite.acceleration.x = 0

        if pressed[K_SPACE]:
            if self.sprite.position.z == 0:
                self.sprite.velocity.z = .5

        if moved and self.state == 2:
            self.change_state(3)

