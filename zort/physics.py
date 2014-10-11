import pygame
from euclid import Vector3
from zort import config
from zort.hex_model import *

__all__ = ['PhysicsGroup']


class PhysicsGroup(pygame.sprite.Group):
    def __init__(self, data):
        super(PhysicsGroup, self).__init__()
        self.data = data

        self.gravity = Vector3(0, 0, config.getfloat('world', 'gravity'))
        self.timestep = config.getfloat('world', 'physics_tick')
        self.gravity_delta = None
        self.ground_friction = None
        self.sleeping = set()
        self.wake = set()
        self.stale = set()
        self.collide_walls = set()

    def update(self, delta, scene):
        stale = self.stale
        delta = self.timestep
        gravity_delta = self.gravity * delta
        ground_friction = pow(.9, delta)
        collide = self.data.collidecircle
        self.sleeping = self.sleeping - self.wake
        self.wake = set()
        all_sprites = self.sprites()

        for sprite in set(self.sprites()) - self.sleeping:
            sleeping = True
            sprite.dirty = 1
            acceleration = sprite.acceleration
            position = sprite.position
            velocity = sprite.velocity
            max_velocity = sprite.max_velocity
            check_walls = sprite in self.collide_walls

            if not position.z == 0 and sprite.gravity:
                acceleration += gravity_delta

            velocity += acceleration * delta
            dv = velocity * delta
            if dv.z > 100:
                dv.z = 100
            x, y, z = dv

            if not z == 0:
                position.z += z
                if position.z < 0:
                    position.z = 0.0
                    if abs(velocity.z) > .2:
                        sprite.bounce_sound.play()
                        sleeping = False
                        acceleration.z = 0.0
                        velocity.z = -velocity.z * .05
                    else:
                        position.z = 0.0
                        acceleration.z = 0.0
                        velocity.z = 0.0
                else:
                    sleeping = False

            if not x == 0:
                if not position.z:
                    velocity.x *= ground_friction

                _collides = False
                if check_walls:
                    new_position = position + (x, 0, 0)
                    axial = sprites_to_axial(new_position)
                    _collides = collide(axial, sprite.radius)

                if not _collides:
                    sleeping = False
                    position.x += x

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

                _collides = False
                if check_walls:
                    new_position = position + (0, y, 0)
                    axial = sprites_to_axial(new_position)
                    _collides = collide(axial, sprite.radius)

                if not _collides:
                    sleeping = False
                    position.y += y

                if abs(round(y, 5)) < .005:
                    acceleration.y = 0.0
                    velocity.y = 0.0

                if velocity.y > max_velocity[1]:
                    velocity.y = max_velocity[1]
                elif velocity.y < -max_velocity[1]:
                    velocity.y = -max_velocity[1]

            if sleeping:
                self.sleeping.add(sprite)
                continue

            axial = sprites_to_axial(position)
            for other in all_sprites:
                if other is sprite:
                    continue

                collided = collide_hex(axial, sprites_to_axial(other.position),
                                       sprite.radius, other.radius)

                t = (sprite, other)
                if collided:
                    if t not in stale:
                        stale.add(t)
                        scene.raise_event("PhysicsGroup", "Collision",
                                          left=sprite, right=other)
                else:
                    if t in stale:
                        stale.remove(t)
                        scene.raise_event(self, "Separation",
                                          left=sprite, right=other)

    def wake_sprite(self, sprite):
        assert (sprite in self.sprites())
        self.wake.add(sprite)
