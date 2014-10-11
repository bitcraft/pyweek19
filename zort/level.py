import pygame
from pygame.locals import *

from zort import hex_view
from zort import config
from zort import resources
from zort.hex_model import *
from zort.entity import *
from zort.environ import maze
from zort.scenes import Scene
from zort.euclid import Point2
from zort.hero import Hero
from zort.levels import loader
from zort.resources import maps
from zort.modes.editor import EditMode


__all__ = ['LevelScene', 'Task']


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
        self.movement_accel = None
        self.damage = None
        self.needs_refresh = None
        self.current_level_module = None
        self.velocity_updates = None
        self.internal_event_group = None
        self.pygame_event_group = None
        self.timers = None
        self.mode = None
        self.view = None

    def init(self):
        self.load_level()
        self.movement_accel = config.getfloat('world', 'player_move_accel')
        self.damage = dict()
        self.needs_refresh = True
        self.velocity_updates = PhysicsGroup(data=self.model)
        self.internal_event_group = pygame.sprite.Group()
        self.pygame_event_group = pygame.sprite.Group()
        self.timers = pygame.sprite.Group()

    def set_model(self, model):
        self.model = model
        # self.model = maze.new_maze(config.getint('world', 'width'),
        #                            config.getint('world', 'height'),
        #                            num_adjacent=2)

        self.view = hex_view.HexMapView(self, self.model,
                                        config.getint('display', 'hex_radius'))

    def new_hero(self):
        # adds new hero, but doesn't remove old one
        self.hero = self.add_entity(Hero, 'alienBlue.png', (1, 1))
        self.velocity_updates.collide_walls.add(self.hero)
        self.pygame_event_group.add(self.hero)

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
        self.timers.update(delta)

        self.internal_event_group.update(delta)

        if len(events):
            for entity in self.pygame_event_group:
                if hasattr(entity, "handle_pygame_events"):
                    entity.handle_pygame_events(events)

        if self.current_level_module:
            self.current_level_module.handle_internal_events(self)

        for sprite in self.internal_event_group:
            if hasattr(sprite, "handle_internal_events"):
                sprite.handle_internal_events(self)

        if self.mode is not None:
            self.mode.update(delta, events)

        self.velocity_updates.update(delta, self)

    def resume(self):
        print("Resuming level scene")

    def load_level(self, level_name=None):
        # teardown whatever needs to be torn down here
        if level_name is None:
            level_name = maps.keys()[0]
        self.current_level_module = loader.load_level(level_name, self)
