import random

import pygame
from pygame.locals import *

from zort import hex_view
from zort import config
from zort import resources
from zort.hex_model import *
from zort.enemies import *
from zort.entity import *
from zort.environ import maze
from zort.scenes import Scene
from zort.euclid import Point2
from zort.hero import Hero
from zort.levels import loader
from zort.modes.editor import EditMode

__all__ = ['LevelScene']


class Task(pygame.sprite.Sprite):
    def __init__(self, callback, interval=0, loops=1, args=None, kwargs=None):
        assert (callable(callback))
        assert (loops >= -1)
        super(Task, self).__init__()
        self.interval = interval
        self.loops = loops
        self.callback = callback
        self._timer = 0
        self._args = args if args else list()
        self._kwargs = kwargs if kwargs else dict()
        self._loops = loops

    def update(self, delta):
        self._timer += delta
        if self._timer >= self.interval:
            self._timer -= self.interval
            self.callback(*self._args, **self._kwargs)
            if not self._loops == -1:
                self._loops -= 1
                if self._loops <= 0:
                    self.kill()


class LevelScene(Scene):
    def __init__(self, game):
        super(LevelScene, self).__init__("level", game)

        self.movement_accel = config.getfloat('world', 'player_move_accel')
        self.damage = dict()
        self.needs_refresh = True
        self.lost_damage = list()
        self.current_level_module = None
        self.model = maze.new_maze(config.getint('world', 'width'),
                                   config.getint('world', 'height'),
                                   num_adjacent=2)

        self.view = hex_view.HexMapView(self, self.model,
                                        config.getint('display', 'hex_radius'))

        self.velocity_updates = PhysicsGroup(data=self.model)
        self.internal_event_group = pygame.sprite.Group()
        self.timers = pygame.sprite.Group()

        # start the silly timer to drop powerups
        #timer = Task(self.new_powerup, 5000, -1)
        #self.timers.add(timer)

        self.hero = self.add_entity(Hero, 'alienBlue.png', (1, 1))
        self.velocity_updates.collide_walls.add(self.hero)
        self.add_entity(Enemy, 'alienYellow.png', (3, 8))

        # this must come last
        self.mode = EditMode(self)

    def add_entity(self, enemy_class, enemy_sprite_file_name, position):
        # send position in even r coordinates
        sx, sy = axial_to_sprites(evenr_to_axial(position))
        sprite = enemy_class(enemy_sprite_file_name)
        sprite.position += (sx, sy, 900)
        if hasattr(sprite, 'home'):
            sprite.home = sprite.position[:2]
        sprite.update_image()
        self.view.add(sprite)
        self.internal_event_group.add(sprite)
        self.velocity_updates.add(sprite)
        return sprite

    def add_button(self, door_key, door_sprite_file_name,
                   position, anchor=None):
        # send position in even r coordinates
        if anchor is None:
            anchor = Point2(30, 60)
        sx, sy = axial_to_sprites(evenr_to_axial(position))
        button = Button(door_sprite_file_name, door_key)
        button.position += (sx, sy, 900)
        button.anchor = anchor
        button.update_image()
        self.view.add(button, layer=0)
        self.internal_event_group.add(button)
        self.velocity_updates.add(button)
        return button

    def add_door(self, door_key, door_sprite_file_name, position):
        # send position in even r coordinates
        coords = evenr_to_axial(position)
        cell = self.view.data.get_cell(coords)
        door = Door(door_sprite_file_name, door_key, cell)
        self.view.add(door)
        self.internal_event_group.add(door)
        return door

    def setup(self):
        print("Setting up level scene")
        resources.play_music('level')

    def teardown(self):
        print("Tearing down level scene")
        pygame.mixer.music.fadeout(500)

    def draw(self, surface):
        dirty = list()
        refreshed = False
        damage = self.damage

        if self.needs_refresh:
            dirty = [surface.get_rect()]
            self.view.needs_refresh = True
            self.mode.needs_refresh = True
            self.needs_refresh = False
            refreshed = True

        _dirty = self.view.draw(surface)
        if _dirty:
            _damage = _dirty[0].unionall(_dirty)
            damage[self.view] = _damage
            for key, value in self.damage.items():
                if key is self.view:
                    continue
                if _damage.colliderect(value):
                    key.needs_refresh = True

            if not refreshed:
                dirty.extend(_dirty)

        _dirty = self.mode.draw(surface)
        if _dirty:
            _damage = _dirty[0].unionall(_dirty)
            damage[self.mode] = _damage
            if not refreshed:
                dirty.extend(_dirty)

        self.damage = damage
        return dirty

    def clear(self, surface):
        self.view.clear(surface)

    def update(self, delta, events):
        moved = False
        pressed = pygame.key.get_pressed()

        if pressed[K_DOWN]:
            self.hero.acceleration.y = self.movement_accel
            moved = True
        elif pressed[K_UP]:
            self.hero.acceleration.y = -self.movement_accel
            moved = True
        else:
            self.hero.acceleration.y = 0

        if pressed[K_LEFT]:
            self.hero.acceleration.x = -self.movement_accel
            self.hero.flipped = True
            moved = True
        elif pressed[K_RIGHT]:
            self.hero.acceleration.x = self.movement_accel
            self.hero.flipped = False
            moved = True
        else:
            self.hero.acceleration.x = 0

        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    self.hero.pickup()

        if moved:
            self.hero.wake()

        self.timers.update(delta)

        self.internal_event_group.update(delta)
        if self.current_level_module:
            self.current_level_module.handle_internal_events(self)
        for sprite in self.internal_event_group:
            if hasattr(sprite, "handle_internal_events"):
                sprite.handle_internal_events(self)

        self.mode.update(delta, events)
        self.velocity_updates.update(delta, self)

    def resume(self):
        print("Resuming level scene")

    def load_level(level_name):
        # teardown whatever needs to be torn down here
        self.current_level_module = loader.load_level(level_name, level_scene)
