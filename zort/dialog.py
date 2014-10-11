import pygame

from zort import resources
from zort import gui
from zort.entity import GameEntity


__all__ = ['Dialog']


class Dialog(GameEntity):
    def __init__(self):
        super(Dialog, self).__init__('smallRockStone.png')
        self.border = gui.GraphicBox(resources.border_path, False)
        self.font = pygame.font.Font(resources.fonts['rez'], 32)
        self.state = None
        self.surface = None
        self.rect = None
        self._dialog = None
        self.needs_refresh = False
        self._listen = ['dialog-show', 'dialog-hidden', 'dialog-next']

    def change_state(self, state):
        self.state = state
        self._dialog = resources.get_text('editor mode intro')
        text = next(self._dialog)
        self.render_dialog(text)

    def handle_internal_events(self, scene):
        all_events = scene.state['events']
        for event in all_events.get('dialog-show', list()):
            self._dialog = resources.get_text(event['heading'])
            text = next(self._dialog)
            self.render_dialog(text)

        for event in all_events.get('dialog-hide', list()):
            scene.needs_refresh = True
            self._dialog = None
            self.surface = None

        for event in all_events.get('dialog-next', list()):
            try:
                text = next(self._dialog)
                self.render_dialog(text)
            except StopIteration:
                scene.raise_event('dialog', 'dialog-hidden')

    def render_dialog(self, text):
        if self.rect is None:
            raise ValueError('cannot change state without video')

        sw, sh = self.rect.size
        rect = pygame.Rect(((0, 5), (sw, sh * .15))).inflate(-10, 0)
        tmp = pygame.Surface(rect.inflate(10, 10).size, pygame.SRCALPHA)
        self.border.draw(tmp, rect)
        gui.draw_text(tmp, text,
                      (255, 255, 255), rect.inflate(-20, -20),
                      self.font, True)
        self.surface = tmp
        self.needs_refresh = True

    def draw(self, surface):
        self.rect = surface.get_rect()

        if self.needs_refresh:
            self.needs_refresh = False
            if self.surface:
                return [surface.blit(self.surface, (0, 0))]
            else:
                return [self.rect]

