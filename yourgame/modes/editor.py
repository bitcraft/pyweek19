from yourgame import resources
from yourgame import gui
from mode import LevelSceneMode
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
        self.border = gui.GraphicBox(resources.border_path, False)
        self.state = None
        self._font = pygame.font.Font(resources.fonts['rez'], 32)
        self._surface = None
        self._rect = None
        self._dialog = None
        self.needs_clear = False

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
            self.needs_clear = True
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
            self.needs_clear = True
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

        if self.needs_clear:
            dirty.append(self._rect)

        return dirty

    def update(self, delta, events):
        moved = False
        pressed = pygame.key.get_pressed()
        movement_speed = .005

        if pressed[K_DOWN]:
            self.sprite.velocity.y = movement_speed
            moved = True
        elif pressed[K_UP]:
            self.sprite.velocity.y = -movement_speed
            moved = True
        else:
            self.sprite.velocity.y = 0

        if pressed[K_LEFT]:
            self.sprite.velocity.x = -movement_speed
            moved = True
        elif pressed[K_RIGHT]:
            self.sprite.velocity.x = movement_speed
            moved = True
        else:
            self.sprite.velocity.x = 0

        if moved and self.state == 2:
            self.change_state(3)

