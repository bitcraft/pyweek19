import pygame
from pygame.transform import flip, smoothscale
from pygame.locals import *

from yourgame import hex_model
from yourgame import resources
from yourgame import config
from yourgame.euclid import Vector2, Vector3

__all__ = ['PhysicsGroup'
           'GameEntity',
           'Button',
           'Door']


class PhysicsGroup(pygame.sprite.Group):

    def __init__(self, data):
        super(PhysicsGroup, self).__init__()
        self.data = data

        self.gravity = Vector3(0, 0, config.getfloat('world', 'gravity'))
        self.timestep = config.getfloat('world', 'physics_tick')
        self.gravity_delta = None
        self.ground_friction = None
        self.sleeping = set()

    def update(self, delta):
        delta = self.timestep
        gravity_delta = self.gravity * delta
        ground_friction = pow(.9, delta)

        for sprite in self.sprites():
            velocity = sprite.velocity
            acceleration = sprite.acceleration
            position = sprite.position
            max_velocity = sprite.max_velocity

            if not position.z == 0:
                acceleration += gravity_delta

            velocity += acceleration * delta
            dv = velocity * delta
            position += dv
            x, y, z = dv

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
                    if abs(velocity.x) > .00002:
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
                    if abs(velocity.y) > .00002:
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
        x, y, z = sprite.position
        if z < 0:
            if sprite.position.z < 0:
                sprite.position.z = 0
                return False

        pos = hex_model.evenr_to_axial((x, y))
        print pos
        if self.data.collidecircle(pos, sprite.radius):
            sprite.position -= point
            return False

        return True


class GameEntity(pygame.sprite.DirtySprite):

    def __init__(self, filename):
        super(GameEntity, self).__init__()
        self.position = Vector3(0, 0, 0)
        self.acceleration = Vector3(0, 0, 0)
        self.velocity = Vector3(0, 0, 0)
        self.original_image = resources.tiles[filename]
        self.anchor = Vector2(16, 57)
        self.radius = .4
        self._layer = 1
        self.event_handlers = list()
        self.max_velocity = [.15, .15, 100]
        self.scale = 1
        self._flipped = False
        self.image = None
        self.update_image()
        self.rect = self.image.get_rect()
        self.move_sound = resources.sounds['scifidrone.wav']
        self._playing_move_sound = False

    def update_image(self):
        w, h = self.original_image.get_size()
        self.image = smoothscale(flip(self.original_image, self._flipped, 0),
                                 (int(w * self.scale), int(h * self.scale)))
        self.image = self.image.convert_alpha()

    def update(self, delta):
        if abs(self.acceleration) > 0:
            if not self._playing_move_sound:
                self.move_sound.set_volume(.1)
                self.move_sound.play(-1, fade_ms=200)
                self._playing_move_sound = True
        else:
            if self._playing_move_sound:
                self.move_sound.fadeout(200)
                self._playing_move_sound = False

    @property
    def flipped(self):
        return self._flipped

    @flipped.setter
    def flipped(self, value):
        if self._flipped or value:
            self._flipped = bool(value)
            self.update_image()

    def trigger_view_refresh(self):
        for group in self.groups():
            if hasattr(group, 'needs_refresh'):
                group.needs_refresh = True


class Button(GameEntity):
    def __init__(self, filename, key):
        super(Button, self).__init__(filename)
        assert(key is not None)
        self.key = key

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

            scene.raise_event(self, 'Switch', key=self.key, state=True)


class Door(GameEntity):
    def __init__(self, filename, key, cell):
        super(Door, self).__init__(filename)
        assert(key is not None)
        assert(cell is not None)
        self.key = key
        self.cell = cell
        self.visible = False

    def handle_internal_events(self, scene):
        interested = scene.state['events'].get('Switch', None)
        if not interested:
            return

        for event in interested:
            if not event['key'] == self.key:
                continue

            cell = self.cell
            if event['state']:
                if not cell.height == 3:
                    cell.filename = 'tileMagic_full.png'
                    cell.height = 3
                    cell.raised = True
                    self.trigger_view_refresh()
            else:
                if cell.raised:
                    cell.filename = 'tileGrass_full.png'
                    cell.height = 0
                    cell.raised = False
                    self.trigger_view_refresh()
