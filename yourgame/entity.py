import pygame
from pygame.locals import *

from yourgame import resources
from yourgame.euclid import Vector3, Point2, Point3

__all__ = ['PhysicsGroup'
           'GameEntity']


class PhysicsGroup(pygame.sprite.Group):

    def update(self, delta):
        for sprite in self.sprites():
            sprite.position += sprite.velocity * delta


class GameEntity(pygame.sprite.Sprite):

    def __init__(self):
        super(GameEntity, self).__init__()
        self.position = Point3(0, 0, 0)
        self.velocity = Vector3(0, 0, 0)
        self.image = resources.tiles['alienBlue.png']
        self.rect = self.image.get_rect()
        self.anchor = Point2(16, 57)
        self.radius = .5
