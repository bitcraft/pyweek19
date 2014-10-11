"""
Evil Hexagonians!
"""

from zort.entity import *
from zort.enemies import *
from zort.hero import Hero
from zort.level import Task
from zort import hex_model


def setup_level(level_scene):
    """
    Initialize your entities
    """
    button = level_scene.build_button("door-1", "tileRock_tile.png", (15, 6))
    level_scene.build_door("door-1", (5, 9))
    level_scene.raise_event(button, 'Switch', key="door-1", state=True)

    button = level_scene.build_button("door-2", "tileRock_tile.png", (2, 11))
    level_scene.build_door("door-2", (14, 3))
    level_scene.raise_event(button, 'Switch', key="door-2", state=True)

    button = level_scene.build_button("door-3", "tileRock_tile.png", (10, 1))
    level_scene.build_door("door-3", (18, 9))
    level_scene.raise_event(button, 'Switch', key="door-3", state=True)

    button = level_scene.build_button("door-3", "tileRock_tile.png", (2, 2))
    button.toggle = True

    e = ShipPart('smallRockStone.png', level_scene.load_level)
    level_scene.add_entity(e, (9, 12))

    e = level_scene.build_entity(Enemy, "alienGreen.png", (4, 4))
    e.scale = 2
    e.update_image()

    e = level_scene.build_entity(Saucer, "shipGreen_manned.png", (6, 6))
    e.scale = 1
    e.update_image()

    e = Rock('smallRockStone.png')
    level_scene.add_entity(e, (2, 4))

    # dialog must be called after video is ready, so give it a delay
    def show_dialog():
        level_scene.raise_event("scene", "dialog-show",
                                heading="Evil Hexagonians")
    t = Task(show_dialog, 1000)
    level_scene.timers.add(t)


def handle_internal_events(level_scene):
    """
    Handle non-entity specific events here
    (or entity specific events if that means getting the game done on time)
    """
    pass
