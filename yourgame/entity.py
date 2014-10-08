import pygame
from pygame.transform import flip
from pygame.locals import *

from yourgame import resources
from yourgame import config
from yourgame.euclid import Vector2, Vector3

__all__ = ['PhysicsGroup'
           'GameEntity',
           'Button']


class PhysicsGroup(pygame.sprite.Group):

    def __init__(self):
        super(PhysicsGroup, self).__init__()
        gravity = config.getfloat('world', 'gravity')

        self.timestep = None
        self.gravity_delta = None
        self.ground_friction = None
        self.sleeping = set()
        self.gravity = Vector3(0, 0, gravity)

    def update(self, delta):
        gravity_delta = self.gravity * delta
        ground_friction = pow(.99, delta)

        for sprite in self.sprites():
            velocity = sprite.velocity
            acceleration = sprite.acceleration
            position = sprite.position
            max_velocity = sprite.max_velocity

            if not position.z == 0:
                acceleration += gravity_delta

            velocity += acceleration * delta
            position += velocity
            x, y, z = velocity

            if not z == 0:
                if not self.move_sprite(sprite, (0, 0, z)):
                    if abs(velocity.z) > .2:
                        acceleration.z = 0.0
                        velocity.z = -velocity.z * .05
                    else:
                        position.z = 0.0
                        acceleration.z = 0.0
                        velocity.z = 0.0

            if not x == 0:
                if not position.z:
                    velocity.x *= ground_friction

                if not self.move_sprite(sprite, (x, 0, 0)):
                    if abs(velocity.x) > .0002:
                        acceleration.x = 0.0
                        velocity.x = 0.0

                if abs(round(x, 5)) < .005:
                    acceleration.x = 0.0
                    velocity.x = 0.0

                if velocity.x > max_velocity[0]:
                    velocity.x = max_velocity[0]
                elif velocity.x < -max_velocity[0]:
                    velocity.x = -max_velocity[0]

            if not y == 0:
                if not position.z:
                    velocity.y *= ground_friction

                if not self.move_sprite(sprite, (0, y, 0)):
                    if abs(velocity.y) > .0002:
                        acceleration.y = 0.0
                        velocity.y = 0.0

                if abs(round(y, 5)) < .005:
                    acceleration.y = 0.0
                    velocity.y = 0.0

                if velocity.y > max_velocity[1]:
                    velocity.y = max_velocity[1]
                elif velocity.y < -max_velocity[1]:
                    velocity.y = -max_velocity[1]

    def move_sprite(self, sprite, point, clip=True):
        z, y, z = point
        if z < 0:
            if sprite.position.z < 0:
                sprite.position.z = 0
                return False

        return True


class GameEntity(pygame.sprite.Sprite):

    def __init__(self, filename):
        super(GameEntity, self).__init__()
        self.position = Vector3(0, 0, 0)
        self.acceleration = Vector3(0, 0, 0)
        self.velocity = Vector3(0, 0, 0)
        self.original_image = resources.tiles[filename]
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.anchor = Vector2(16, 57)
        self.radius = .5
        self._layer = 1
        self.event_handlers = list()
        self.max_velocity = [.15, .15, 100]

        # set this init value to False if sprite is facing right
        self._flipped = False

    @property
    def flipped(self):
        return self._flipped

    @flipped.setter
    def flipped(self, value):
        if self._flipped or value:
            self.image = flip(self.original_image, value, 0)
        self._flipped = bool(value)


class Button(GameEntity):
    def handle_internal_events(self, scene):
        interested = scene.state['events'].get('Collision', None)
        if not interested:
            return

        for event in interested:
            try:
                members = [event['left'], event['right']]
                members.remove(self)
                other = members[0]
            except ValueError:
                continue

            other.kill()

