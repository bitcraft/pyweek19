import sys

from pygame.time import Clock
from pygame import event
from pygame import QUIT
from pygame.display import flip, update


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
        self.scene_stack.append(scene)
        self.current_scene = scene
        scene.setup()

    def pop_scene(self):
        self.current_scene.teardown()
        self.current_scene = None
        if len(self.scene_stack):
            self.current_scene = self.scene_stack.pop()
            self.current_scene.resume()

    def loop(self):
        draw_interval = 1 / float(self.target_fps)
        tick_fps = self.target_fps * 2
        draw_timer = 0
        event_get = event.get
        tick = self.clock.tick
        main_surface = self.main_surface

        while len(self.scene_stack) > 0:
            events = event_get()
            for e in events:
                if e.type == QUIT:
                    while len(self.scene_stack) > 0:
                        self.pop_scene()
                    sys.exit()

            delta = tick(tick_fps)
            self.current_scene.update_events()
            self.current_scene.update(delta, events)

            draw_timer += delta
            if draw_timer >= draw_interval:
                draw_timer -= draw_interval
                self.current_scene.clear(main_surface)
                dirty = self.current_scene.draw(main_surface)
                update(dirty)


class Scene(object):

    def __init__(self, name, game):
        self.game = game
        self.name = name
        self.state = {"events": {}}
        # events are stored as {"event-name": list of kwargs dicts}

    def setup(self):
        raise NotImplemented("Not implemented by subclass")

    def teardown(self):
        raise NotImplemented("Not implemented by subclass")

    def resume(self):
        raise NotImplemented("Not implemented by subclass")

    def draw(self, surface):
        pass

    def update(self, delta, events):
        return True

    def clear(self, surface):
        pass

    def raise_event(self, originator, event_name, **kwargs):
        events = self.state["events"]
        events[event_name] = dict(kwargs)
        events[event_name]["originator"] = originator
        events[event_name]["frames_left"] = 2

    def update_events(self):
        events = self.state["events"]
        for event_list in events.values():
            dead = list()
            for e in event_list:
                e["frames_left"] -= 1
                if e["frame_left"] <= 0:
                    dead.append(e["frame_left"])
            for e in dead:
                event_list.remove(e)

    def clear_events(self):
        self.state["events"] = dict()
