import pygame
from pygame.locals import *

import resources
from euclid import Point3


class GameEntity(pygame.sprite.Sprite):

    def __init__(self):
        super(GameEntity, self).__init__()
        self.position = Point3(0, 0, 0)
        self.image = resources.tiles['alienBlue.png']
        self.rect = self.image.get_rect()
