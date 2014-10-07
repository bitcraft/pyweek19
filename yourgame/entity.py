import pygame
from pygame.locals import *

from yourgame import resources
from yourgame import config
from yourgame.euclid import Vector3, Point2, Point3

__all__ = ['PhysicsGroup'
           'GameEntity']


class PhysicsGroup(pygame.sprite.Group):

    def __init__(self):
        super(PhysicsGroup, self).__init__()

        gravity = -.000001
        self.gravity = Vector3(0, 0, gravity)
        self.timestep = None
        self.gravity_delta = None
        self.ground_friction = None
        self.sleeping = set()
        self.set_timestep(config.getfloat('display', 'target-fps'))

    def update(self, delta):
        for sprite in self.sprites():
            if not sprite.position.z == 0:
                sprite.acceleration += self.gravity_delta

            sprite.velocity += sprite.acceleration * self.timestep
            sprite.position += sprite.velocity
            x, y, z = sprite.velocity

            if not x == 0:
                if not self.move_sprite(sprite, (x, 0, 0)):
                    if abs(sprite.velocity.x) > .0002:
                        sprite.acceleration.x = 0.0
                        sprite.velocity.x = 0.0

            if not y == 0:
                if not self.move_sprite(sprite, (0, y, 0)):
                    if abs(sprite.velocity.y) > .0002:
                        sprite.acceleration.y = 0.0
                        sprite.velocity.y = 0.0

            if not z == 0:
                if sprite.position.z < 0:
                    sprite.position.z = 0
                    sprite.velocity.z = 0
                    sprite.acceleration.z = 0

                if not self.move_sprite(sprite, (0, 0, z)):
                    if abs(sprite.velocity.z) > .0002:
                        sprite.acceleration.z = 0.0
                        sprite.vel.z = -sprite.velocity.z * .05

            if sprite.position.z == 0:
                sprite.velocity.x *= self.ground_friction
                sprite.velocity.y *= self.ground_friction

    def move_sprite(self, sprite, point, clip=True):
        return True

    def set_timestep(self, timestep):
        self.timestep = timestep
        self.gravity_delta = self.gravity * timestep
        # self.ground_friction = pow(.1, self.timestep)
        self.ground_friction = .8


class GameEntity(pygame.sprite.Sprite):

    def __init__(self):
        super(GameEntity, self).__init__()
        self.position = Point3(0, 0, 0)
        self.acceleration = Vector3(0, 0, 0)
        self.velocity = Vector3(0, 0, 0)
        self.image = resources.tiles['alienBlue.png']
        self.rect = self.image.get_rect()
        self.anchor = Point2(16, 57)
        self.radius = .5
