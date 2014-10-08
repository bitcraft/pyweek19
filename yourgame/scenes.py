import sys
from collections import defaultdict

from pygame.time import Clock
from pygame import event
from pygame import QUIT
from pygame.display import flip, update, set_caption
from pygame.draw import rect as draw_rect

from yourgame import config


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
        DEBUG = config.getboolean('display', 'debug')

        draw_interval = 1 / float(self.target_fps)
        tick_fps = self.target_fps
        draw_timer = 0
        event_get = event.get
        tick = self.clock.tick
        main_surface = self.main_surface
        fps_display_acc = 0

        while len(self.scene_stack) > 0:
            events = event_get()
            for e in events:
                if e.type == QUIT:
                    while len(self.scene_stack) > 0:
                        self.pop_scene()
                    sys.exit()

            delta = tick(tick_fps)
            fps_display_acc += delta
            if fps_display_acc >= 1000:
                set_caption("FPS ::: %.3f" % self.clock.get_fps())
                fps_display_acc = 0
            self.current_scene.update_events()
            self.current_scene.update(delta, events)

            draw_timer += delta
            if draw_timer >= draw_interval:
                if DEBUG:
                    main_surface.fill((0, 0, 0))

                draw_timer -= draw_interval
                self.current_scene.clear(main_surface)
                dirty = self.current_scene.draw(main_surface)

                if DEBUG:
                    #rect = dirty[0].unionall(dirty)
                    #print float(rect.w * rect.h) / (surface.get_width() * surface.get_height()) * 100
                    for rect in dirty:
                        draw_rect(main_surface, (0, 255, 0), rect, 1)

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
        event = dict(kwargs)
        event["originator"] = originator
        event["frames_left"] = config.getint('general', 'event_life')
        try:
            events = self.state["events"][event_name]
        except KeyError:
            events = list()
            self.state['events'][event_name] = events
        finally:
            events.append(event)

    def update_events(self):
        events = self.state["events"]
        for event_type, event_list in events.items():
            dead = list()
            for e in event_list:
                e["frames_left"] -= 1
                if e["frames_left"] <= 0:
                    dead.append(e)

            for e in dead:
                event_list.remove(e)

    def clear_events(self):
        self.state["events"] = dict()
