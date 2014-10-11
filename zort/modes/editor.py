from pygame.locals import *

from zort.modes.mode import LevelSceneMode
from zort import config


__all__ = ['EditMode']


class EditMode(LevelSceneMode):
    def handle_click(self, button, cell):
        view = self.scene.view

        # left click
        if button == 1:
            cell.raised = not cell.raised
            if cell.raised:
                cell.height = config.getint('display', 'wall_height')
                cell.filename = 'tileRock_full.png'
            else:
                cell.height = 0
                cell.filename = 'tileGrass.png'

            view.needs_refresh = True

    def update(self, delta, events):
        super(EditMode, self).update(delta, events)
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_F5:
                    path = config.get('general', 'save_to_map')
                    self.scene.view.data.save_to_disk(path)
