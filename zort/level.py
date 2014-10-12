import pygame
from pygame.locals import *

from zort import hex_view
from zort import config
from zort import gui
from zort import resources
from zort.environ import util
from zort.hex_model import *
from zort.entity import *
from zort.dialog import Dialog
from zort.scenes import Scene
from zort.euclid import Point2, Vector3
from zort.hero import Hero
from zort.physics import PhysicsGroup
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


class Hud(GameEntity):
    def __init__(self):
        super(Hud, self).__init__('smallRockStone.png')
        self.border = gui.GraphicBox(resources.border_path, False)
        self.font = pygame.font.Font(resources.fonts['rez'], 32)
        self.state = None
        self.surface = None
        self.rect = None
        self._dialog = None
        self.needs_refresh = False
        self._listen = ['dialog-show', 'dialog-hidden', 'dialog-next']

    def handle_internal_events(self, scene):
        all_events = scene.state['events']
        for event in all_events.get('dialog-show', list()):
            self._dialog = resources.get_text(event['heading'])
            text = next(self._dialog)
            self.render_dialog(text)

        for event in all_events.get('dialog-hide', list()):
            scene.needs_refresh = True
            self._dialog = None
            self.surface = None

        for event in all_events.get('dialog-next', list()):
            try:
                text = next(self._dialog)
                self.render_dialog(text)
            except StopIteration:
                scene.raise_event('dialog', 'dialog-hidden')

    def draw(self, surface):
        self.rect = surface.get_rect()

        if self.needs_refresh:
            self.needs_refresh = False
            if self.surface:
                return [surface.blit(self.surface, (0, 0))]
            else:
                return [self.rect]


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
        self.mode = None
        self.timers = None
        self.dialog = None
        self.view = None
        self.model = None
        self._hero = None
        self.hud = None
        self.time = None

    def init(self):
        self.load_level()

    def set_model(self, model):
        self.model = model
        self.view = hex_view.HexMapView(self, self.model,
                                        config.getint('display', 'hex_radius'))
        self.velocity_updates = PhysicsGroup(data=self.model)

    def new_hero(self):
        # adds new hero, but doesn't remove old one
        self._hero = self.build_entity(Hero, 'alienBlue.png', (1, 1))
        self.velocity_updates.collide_walls.add(self.hero)
        self.pygame_event_group.add(self._hero)

    def build_entity(self, enemy_class, enemy_sprite_file_name, position):
        entity = enemy_class(enemy_sprite_file_name)
        self.add_entity(entity, position)
        return entity

    def build_button(self, door_key, door_sprite_file_name,
                     position, anchor=None):
        # send position in even r coordinates
        if anchor is None:
            anchor = Point2(30, 60)
        sx, sy = axial_to_sprites(evenr_to_axial(position))
        button = Button(door_sprite_file_name, door_key)
        button.position = Vector3(sx, sy, 0)
        button.anchor = anchor
        button.update_image()
        self.view.add(button, layer=0)
        self.internal_event_group.add(button)
        self.velocity_updates.add(button)
        return button

    def add_entity(self, entity, position):
        sx, sy = axial_to_sprites(evenr_to_axial(position))
        entity.position = Vector3(sx, sy, 900)
        if hasattr(entity, 'home'):
            entity.home = Vector3(entity.position)
        self.view.add(entity)
        self.internal_event_group.add(entity)
        self.velocity_updates.add(entity)

    def build_door(self, door_key, position):
        # send position in even r coordinates
        door_sprite_file_name = 'smallRockStone.png'
        coords = evenr_to_axial(position)
        cell = self.view.data.get_cell(coords)
        door = Door(door_sprite_file_name, door_key, cell)
        self.view.add(door)
        self.internal_event_group.add(door)
        return door

    def move_hero(self, position):
        sx, sy = axial_to_sprites(evenr_to_axial(position))
        self.hero.position = Vector3(sx, sy, 900)

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
            self.dialog.needs_refresh = True
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

        _dirty = self.dialog.draw(surface)
        if _dirty:
            _damage = _dirty[0].unionall(_dirty)
            damage[self.dialog] = _damage
            if not refreshed:
                dirty.extend(_dirty)

        _dirty = self.hud.draw(surface)
        if _dirty:
            _damage = _dirty[0].unionall(_dirty)
            damage[self.hud] = _damage
            if not refreshed:
                dirty.extend(_dirty)

        self.damage = damage
        return dirty

    @property
    def hero(self):
        return self._hero

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

    def build_hud(self):
        self.hud = Hud()

    def load_level(self, level_name=None):
        # teardown whatever needs to be torn down here
        self.model = HexMapModel()
        self.view = hex_view.HexMapView(
            self, self.model, config.getint('display', 'hex_radius'))
        self.movement_accel = config.getfloat('world', 'player_move_accel')
        self.damage = dict()
        self.needs_refresh = True
        self.velocity_updates = PhysicsGroup(data=self.model)
        self.internal_event_group = pygame.sprite.Group()
        self.pygame_event_group = pygame.sprite.Group()
        self.timers = pygame.sprite.Group()
        self.mode = EditMode(self)
        self.dialog = Dialog()
        self.internal_event_group.add(self.dialog)
        self.build_hud()
        self.new_hero()
        if level_name is None:
            level_name = next((k for k in maps.keys()))
        self.current_level_module = loader.load_level(level_name, self)
