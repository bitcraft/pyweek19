import itertools
import random

import pygame

from yourgame import hex_model
from yourgame import hex_view
from yourgame import config
from yourgame import resources
from yourgame.scenes import Scene
from yourgame.environ import maze
from yourgame.euclid import Point2
from yourgame.entity import *
from yourgame.modes.editor import EditMode
from yourgame.hero import Hero
from yourgame.enemies import *

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

        self.damage = dict()
        self.needs_refresh = True
        self.lost_damage = list()

        # build a basic flat map
        self.model = hex_model.HexMapModel()
        w = config.getint('world', 'width')
        h = config.getint('world', 'height')
        for q, r in itertools.product(range(w), range(h)):
            coords = hex_model.evenr_to_axial((q, r))
            cell = hex_model.Cell()
            cell.filename = 'tileGrass.png'
            cell.kind = 'grass'
            self.model.add_cell(coords, cell)

        # build a maze
        maze.build_maze_from_hex(self.model,
                                 lower_limit=(1, 1),
                                 upper_limit=(self.model.width - 2,
                                              self.model.height - 2),
                                 height=1.0,
                                 raised_tile='tileRock_full.png',
                                 lowered_tile='tileGrass.png',
                                 num_adjacent=1)

        self.view = hex_view.HexMapView(self, self.model,
                                        config.getint('display', 'hex_radius'))

        self.velocity_updates = PhysicsGroup(data=self.model)
        self.internal_event_group = pygame.sprite.Group()
        self.timers = pygame.sprite.Group()

        def f(klass, filename):
            sprite = klass(filename)
            sprite.position.x = random.randint(0, w)
            sprite.position.y = random.randint(0, h)
            sprite.position.z = 900
            self.view.add(sprite)
            self.internal_event_group.add(sprite)
            self.velocity_updates.add(sprite)

        enemies = ((Stalker, 'alienGreen.png'),
                   (Rambler, 'alienYellow.png'),
                   (Tosser, 'alienPink.png'))

        for i, args in enumerate(enemies*2):
            t = Task(f, i*500, 1, args)
            self.timers.add(t)

        # sprite = entity.GameEntity('alienBlue.png')
        # sprite.position.x = 9
        # sprite.position.y = 9
        # self.view.add(sprite)
        hero = Hero('alienBlue.png')
        hero.position.x = 1
        hero.position.y = 1
        hero._layer = 99
        self.view.add(hero)
        self.internal_event_group.add(hero)
        self.velocity_updates.add(hero)
        self.hero = hero

        # "switch"
        button = Button('tileRock_tile.png', 'testDoor')
        button.position.x = 2
        button.position.y = 4
        button.position.z = 900
        button.anchor = Point2(33, 30)
        self.view.add(button, layer=0)
        self.internal_event_group.add(button)
        self.velocity_updates.add(button)

        # "door"
        coords = hex_model.evenr_to_axial((0, 0))
        cell = self.view.data.get_cell(coords)
        door = Door('smallRockStone.png', 'testDoor', cell)
        # it must be added to the view group so it can trigger map refreshes
        self.view.add(door)
        self.internal_event_group.add(door)

        # start the silly timer to drop powerups
        timer = Task(self.new_powerup, 5000, -1)
        self.timers.add(timer)

        # this must come last
        self.mode = EditMode(self)

    def new_powerup(self):
        w = self.view.data.width - 1
        h = self.view.data.height - 1

        # generic powerup
        sprite = CallbackEntity('smallRockSnow.png', self.next_level)
        sprite.position.x = random.randint(0, w)
        sprite.position.y = random.randint(0, h)
        sprite.position.z = 900
        sprite.anchor = Point2(33, 30)
        self.view.add(sprite, layer=0)
        self.internal_event_group.add(sprite)
        self.velocity_updates.add(sprite)

    def next_level(self):
        pass

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
        self.timers.update(delta)

        self.internal_event_group.update(self)
        for sprite in self.internal_event_group:
            if hasattr(sprite, "handle_internal_events"):
                sprite.handle_internal_events(self)

        self.mode.update(delta, events)
        self.velocity_updates.update(self, delta)

    def resume(self):
        print("Resuming level scene")

