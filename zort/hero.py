import pygame
from pygame.locals import *

from zort.entity import GameEntity
from zort import resources, config


class Hero(GameEntity):
    """

    GURUS OF PYTHON:

    game entities now have built in callback for collisions!

    see the on_collide and on_separate methods

    """

    def __init__(self, filename):
        super(Hero, self).__init__(filename)
        self.movement_accel = config.getfloat('world', 'player_move_accel')
        self.move_sound = resources.sounds['scifidrone.wav']
        self._playing_move_sound = False
        self._layer = 2

    def handle_pygame_events(self, events):
        moved = False
        pressed = pygame.key.get_pressed()
        grounded = self.position.z == self.velocity.z == 0
        moving = self.velocity.x or self.velocity.y or self.velocity.z

        if not grounded:
            self.wake()
            return

        if pressed[K_DOWN]:
            self.acceleration.y = self.movement_accel
            moved = True
        elif pressed[K_UP]:
            self.acceleration.y = -self.movement_accel
            moved = True
        else:
            self.acceleration.y = 0

        if pressed[K_LEFT]:
            self.acceleration.x = -self.movement_accel
            self.flipped = True
            moved = True
        elif pressed[K_RIGHT]:
            self.acceleration.x = self.movement_accel
            self.flipped = False
            moved = True
        else:
            self.acceleration.x = 0

        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    self.pickup()

        if moved:
            self.wake()
