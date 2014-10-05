from pygame.time import Clock


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

    def __getitem__(self, key):
        return self.states[self.current_scene.name][self.current_index][key]

    def __setitem__(self, key, value):
        pass

    def loop(self):
        while len(self.scene_stack) > 0:
            delta = self.clock.tick(self.target_fps)
            self.current_scene.update(delta)
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
