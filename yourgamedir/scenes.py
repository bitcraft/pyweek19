import sys

from pygame.time import Clock
from pygame import event
from pygame import QUIT


class Game(object):

    def __init__(self, target_fps, main_surface):
        self.scenes = dict()
        self.scene_stack = list()
        self.current_scene = None
        self.target_fps = target_fps
        self.clock = Clock()
        self.main_surface = main_surface

    def register_scene(self, scene):
        self.scenes[scene.name] = scene

    def push_scene(self, name):
        scene = self.scenes[name]
        self.scene_stack.push(scene)
        scene.setup()

    def loop(self):
        while len(self.scene_stack) > 0:
            event.pump()
            events = event.get()
            for e in events:
                if e.type == QUIT:
                    while len(self.scene_stack) > 0:
                        self.pop_scene()
                    sys.exit()
            
            delta = self.clock.tick(self.target_fps)
            self.current_scene.update(delta, events)
            self.current_scene.draw(self.main_surface)


class Scene(object):

    def __init__(self, name, game):
        self.game = game
        self.name = name
        self.state = dict()

    def setup(self):
        raise NotImplemented("Not implemented by subclass")

    def teardown(self):
        raise NotImplemented("Not implemented by subclass")

    def resume(self):
        raise NotImplemented("Not implemented by subclass")

    def draw(self):
        pass

    def update(self):
        pass
