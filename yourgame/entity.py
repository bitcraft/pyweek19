import pygame
from pygame.locals import *

import resources
from euclid import Point2, Point3


class GameEntity(pygame.sprite.Sprite):

    def __init__(self):
        super(GameEntity, self).__init__()
        self.position = Point3(0, 0, 0)
        self.image = resources.tiles['alienBlue.png']
        self.rect = self.image.get_rect()

        w, h = self.image.get_size()
        self.anchor = Point2(16, 57)
