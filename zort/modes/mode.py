from pygame.locals import *
from zort.hex_model import *


class LevelSceneMode(object):
    """ provides various handlers to abstract gameplay into modes
    """

    def __init__(self, scene):
        self.scene = scene

    def handle_click(self, button, cell):
        pass

    def draw(self, surface):
        pass

    def get_nearest_cell(self, coords):
        _coords = self.scene.view.coords_from_surface(coords)
        if _coords is not None:
            _coords = hex_round(_coords)
            print('highlighted cell is (ever): {}'.format(_coords))
        return self.scene.view.cell_from_surface(coords)


    def update(self, delta, events):
        for event in events:
            if event.type == MOUSEMOTION:
                cell = self.get_nearest_cell(event.pos)
                if cell:
                    self.scene.view.highlight_cell(cell)

            if event.type == MOUSEBUTTONUP:
                cell = self.get_nearest_cell(event.pos)
                if cell:
                    self.handle_click(event.button, cell)
