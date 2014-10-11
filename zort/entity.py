import pygame
from pygame.transform import flip, smoothscale

from zort.hex_model import collide_hex, sprites_to_axial
from zort import resources
from zort import config
from zort.euclid import Vector2, Vector3


__all__ = ['PhysicsGroup',
           'GameEntity',
           'Button',
           'Door',
           'CallbackEntity']


def filter_interested(scene, interested):
    retval = list()
    for name in interested:
        retval.extend(scene.state['events'].get(name, list()))
    return retval


def filter_belong(owner, events):
    retval = list()
    for event in events:
        try:
            members = [event['left'], event['right']]
            members.remove(owner)
            other = members[0]
            retval.append((event, other))
        except ValueError:
            continue
    return retval


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

            if not position.z == 0:
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


class GameEntity(pygame.sprite.DirtySprite):
    def __init__(self, filename):
        super(GameEntity, self).__init__()
        self.position = Vector3(0, 0, 0)
        self.acceleration = Vector3(0, 0, 0)
        self.velocity = Vector3(0, 0, 0)
        self.original_image = resources.tiles[filename]
        self.original_anchor = Vector2(16, 57)
        self.anchor = None
        self.radius = .4
        self._layer = 1
        self.event_handlers = list()
        self.max_velocity = [.15, .15, 100]
        self.scale = 1
        self._flipped = False
        self.image = None
        self.update_image()
        self.rect = self.image.get_rect()
        self.dirty = 1
        self.move_sound = None
        self._playing_move_sound = False
        self.carried = set()
        self.pickup_item_sound = resources.sounds['woosh1.ogg']
        self.drop_item_sound = resources.sounds['woosh2.ogg']
        self.bounce_sound = resources.sounds['boing-slow.ogg']
        self.bounce_sound.set_volume(.2)
        # self.drop_sound = resources.sounds['']
        #self.injure = resources.sounds['']
        #self.surprise_sound = resources.sounds['']
        #self.chase_sound = resources.sounds['']
        self._collided = set()
        self._pickup_cooldown = 0

    def stop(self):
        self.velocity = Vector3(0, 0, 0)
        self.acceleration = Vector3(0, 0, 0)
        self.wake()

    def pickup(self):
        if not self._pickup_cooldown:
            self._pickup_cooldown = 200
            if not self.carried:
                self.pickup_item_sound.play()
                self.carried = set(self._collided)
            else:
                self.drop_item_sound.play()
                for entity in self.carried:
                    entity.wake()
                    entity.acceleration.z = .000025
                self.carried = set()

    @property
    def physics_group(self):
        for g in self.groups():
            if isinstance(g, PhysicsGroup):
                return g

    def wake(self):
        self.physics_group.wake_sprite(self)

    def update_image(self):
        w, h = self.original_image.get_size()
        self.image = smoothscale(flip(self.original_image, self._flipped, 0),
                                 (int(w * self.scale), int(h * self.scale)))
        self.anchor = self.original_anchor * self.scale
        self.image = self.image.convert_alpha()

    def update(self, delta):
        if self._pickup_cooldown:
            self._pickup_cooldown -= delta
            if self._pickup_cooldown < 0:
                self._pickup_cooldown = 0

        for entity in self.carried:
            entity.dirty = 1
            entity.position = self.position + (0, 0, self.rect.height)
            entity.stop()

        if self.move_sound:
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

    def handle_internal_events(self, scene):
        events = filter_belong(self, filter_interested(scene, ('Collision',)))
        if events:
            self._collided = set(i[1] for i in events)

        events = filter_belong(self, filter_interested(scene, ('Separation',)))
        if events:
            self._collided = self._collided - set(i[1] for i in events)


class Collider(GameEntity):
    def on_collide(self, scene, other):
        pass

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

            self.on_collide(scene, other)


class Button(Collider):
    def __init__(self, filename, key):
        super(Button, self).__init__(filename)
        assert (key is not None)
        self.key = key

    def on_collide(self, scene, other):
        scene.raise_event(self, 'Switch', key=self.key, state=True)

    def on_seperate(self, scene, other):
        scene.raise_event(self, 'Switch', key=self.key, state=False)


class Rock(GameEntity):
    def __init__(self, filename):
        super(Rock, self).__init__(filename)
        self.bounce_sound = resources.sounds['stoneHit3.ogg']

    def handle_internal_events(self, scene):
        pass


class Door(GameEntity):
    def __init__(self, filename, key, cell):
        super(Door, self).__init__(filename)
        assert (key is not None)
        assert (cell is not None)
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


class CallbackEntity(Collider):
    def __init__(self, filename, callback, args=None, kwargs=None):
        super(CallbackEntity, self).__init__(filename)
        self._callback = callback
        self._args = args if args else list()
        self._kwargs = kwargs if kwargs else dict()

    def on_collide(self, scene, other):
        self._callback(*self._args, **self._kwargs)
