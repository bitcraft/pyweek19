import pygame
from pygame.locals import *

from yourgame import gui
from yourgame.scenes import Scene
import os

from this import s as demo_text
d = {}
for c in (65, 97):
    for i in range(26):
        d[chr(i+c)] = chr((i+13) % 26 + c)
demo_text = "".join([d.get(c, c) for c in demo_text])

__all__ = ['DialogScene']

border_path = os.path.join(os.path.dirname(__file__),
                           '..', 'data', 'dialog.png')


class DialogScene(Scene):

    def __init__(self, game):
        super(DialogScene, self).__init__("dialog", game)
        self.box = gui.GraphicBox(border_path, True)

    def setup(self):
        self.mod = 0

    def teardown(self):
        print("Tearing down level scene")

    def draw(self, surface):
        surface.fill((0, 0, 0))
        rect = surface.get_rect().inflate(self.mod, 0)
        self.box.draw(surface, rect)
        gui.draw_text(surface, demo_text, (255, 255, 255),
                      rect.inflate(-10, -10))

    def update(self, delta, events):
        self.mod -= .5

    def resume(self):
        print("Resuming level scene")

