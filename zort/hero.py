import pygame
from pygame.locals import *

from zort.entity import GameEntity
from zort import resources


class Hero(GameEntity):

    def __init__(self, filename):
        super(Hero, self).__init__(filename)
        self.move_sound = resources.sounds['scifidrone.wav']
        self._playing_move_sound = False

    def handle_internal_events(self, scene):
        pass

    def handle_pygame_events(self, events):
        moved = False
        pressed = pygame.key.get_pressed()

        if pressed[K_DOWN]:
            self.hero.acceleration.y = self.movement_accel
            moved = True
        elif pressed[K_UP]:
            self.hero.acceleration.y = -self.movement_accel
            moved = True
        else:
            self.hero.acceleration.y = 0

        if pressed[K_LEFT]:
            self.hero.acceleration.x = -self.movement_accel
            self.hero.flipped = True
            moved = True
        elif pressed[K_RIGHT]:
            self.hero.acceleration.x = self.movement_accel
            self.hero.flipped = False
            moved = True
        else:
            self.hero.acceleration.x = 0

        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    self.hero.pickup()

        if moved:
            self.hero.wake()
