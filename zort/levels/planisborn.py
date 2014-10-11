"""
A Plan is Born
"""

# import your game entities here
# implement any level specific enemies here

from zort.entity import *
from zort.enemies import *
from zort.hero import Hero
from zort.level import Task
from zort import hex_model


def setup_level(level_scene):
    """
    Initialize your entities
    """

    e = ShipPart('shipPart1.png', level_scene.load_level)
    e.scale = .5
    e.update_image()
    level_scene.add_entity(e, (15, 12))

    # dialog must be called after video is ready, so give it a delay
    def show_dialog():
        level_scene.raise_event("scene", "dialog-show",
                                heading="A Plan is Born")
    t = Task(show_dialog, 1000)
    level_scene.timers.add(t)


def handle_internal_events(level_scene):
    """
    Handle non-entity specific events here
    (or entity specific events if that means getting the game done on time)
    """
    pass
