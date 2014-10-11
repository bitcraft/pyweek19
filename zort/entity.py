import pygame
from pygame.transform import flip, smoothscale
from zort.hex_model import *
from zort import resources
from zort.euclid import Vector2, Vector3
from zort.physics import PhysicsGroup

__all__ = ['GameEntity',
           'Button',
           'Door',
           'Rock',
           'CallbackEntity',
           'ShipPart',
           'filter_interested',
           'filter_belong']


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


class GameEntity(pygame.sprite.DirtySprite):
    """

    GURUS OF PYTHON:

    game entities now have built in callback for collisions!

    see the on_collide and on_separate methods

    """

    def __init__(self, filename):
        super(GameEntity, self).__init__()
        self.gravity = True
        self.timers = pygame.sprite.Group()
        self.position = Vector3(-100, -100, 0)
        self.acceleration = Vector3(0, 0, 0)
        self.velocity = Vector3(0, 0, 0)
        self.original_image = resources.tiles[filename]
        self.anchor = None
        self.radius = .4
        self._layer = 1
        self.max_velocity = [.15, .15, 100]
        self.scale = 1
        self._flipped = False
        self.image = None
        self.rect = self.original_image.get_rect()
        self.original_anchor = Vector2(*self.rect.midbottom)
        self.update_image()
        self.dirty = 1
        self.move_sound = None
        self.carried = None
        self._playing_move_sound = False
        self.pickup_item_sound = resources.sounds['woosh1.ogg']
        self.drop_item_sound = resources.sounds['woosh2.ogg']
        self.bounce_sound = resources.sounds['boing-slow.ogg']
        self.bounce_sound.set_volume(.2)
        # self.drop_sound = resources.sounds['']
        # self.injure = resources.sounds['']
        #self.surprise_sound = resources.sounds['']
        #self.chase_sound = resources.sounds['']
        self._collided = set()
        self._pickup_cooldown = 0
        self._attached = None

    def kill(self):
        self._attached = None
        if self.carried is not None:
            self.drop()
        super(GameEntity, self).kill()

    def stop(self):
        self.velocity = Vector3(0, 0, 0)
        self.acceleration = Vector3(0, 0, 0)
        self.wake()

    def pickup(self):
        if not self._pickup_cooldown:
            self._pickup_cooldown = 200
            if self.carried is None:
                if self._collided:
                    self.carried = set(self._collided)
                    self.pickup_item_sound.play()
                    for entity in self.carried:
                        entity._layer = 3
                        entity.attach(self, (0, 0, 40))
            else:
                self.drop()

    def drop(self):
        if self.carried is not None:
            self.drop_item_sound.play()
            for entity in self.carried:
                entity.acceleration.z = .0025
                entity.release()
                entity.wake()
            self.carried = None

    def spawn(self, other):
        for g in self.groups():
            g.add(other)

    def attach(self, other, anchor=None):
        if anchor is None:
            anchor = (0, 0, 0)
        anchor = Vector3(*anchor)
        self.wake()
        self._attached = other, anchor

    def release(self):
        self._attached = None

    @property
    def physics_group(self):
        for g in self.groups():
            if isinstance(g, PhysicsGroup):
                return g

    @property
    def view_group(self):
        for g in self.groups():
            if hasattr(g, 'map_buffer'):
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
        self.timers.update(delta)

        if self._pickup_cooldown:
            self._pickup_cooldown -= delta
            if self._pickup_cooldown < 0:
                self._pickup_cooldown = 0

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

        if self._attached is not None:
            self.stop()
            self.dirty = 1
            entity, anchor = self._attached
            self.position = entity.position + anchor

    @property
    def grounded(self):
        return self.position.z == self.velocity.z == 0

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
        for event, other in events:
            self.on_collide(scene, other)

        events = filter_belong(self, filter_interested(scene, ('Separation',)))
        for event, other in events:
            self.on_separate(scene, other)

    def on_collide(self, scene, other):
        pass

    def on_separate(self, scene, other):
        pass


class Button(GameEntity):
    def __init__(self, filename, key):
        super(Button, self).__init__(filename)
        assert (key is not None)
        self.original_anchor = Vector2(32, 35)
        self.update_image()
        self.key = key
        self.toggle = False  # if true the door will only work when colliding
        self._collided = set()
        self.collide_sound = resources.sounds['stoneDragHit3.ogg']
        self.separate_sound = resources.sounds['stoneHit3.ogg']

    def on_collide(self, scene, other):
        scene.raise_event(self, 'Switch', key=self.key, state=False)
        self.collide_sound.play()
        self._collided.add(other)

    def on_seperate(self, scene, other):
        self.separate_sound.play()
        self._collided.remove(other)
        if len(self._collided) == 0 and self.toggle:
            scene.raise_event(self, 'Switch', key=self.key, state=True)


class Rock(GameEntity):
    def __init__(self, filename):
        super(Rock, self).__init__(filename)
        self.bounce_sound = resources.sounds['stoneHit3.ogg']
        self.radius = .5
        self.update_image()

    def handle_internal_events(self, scene):
        pass


class Door(GameEntity):
    def __init__(self, filename, key, cell):
        super(Door, self).__init__(filename)
        assert (key is not None and cell is not None)
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


class CallbackEntity(GameEntity):
    def __init__(self, filename, callback, args=None, kwargs=None):
        super(CallbackEntity, self).__init__(filename)
        self._callback = callback
        self._args = args if args else list()
        self._kwargs = kwargs if kwargs else dict()

    def on_collide(self, scene, other):
        self._callback(*self._args, **self._kwargs)


class ShipPart(CallbackEntity):
    pass
