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
    button = level_scene.build_button("door-1", "tileRock_tile.png", (16, 7))
    level_scene.build_door("door-1", (5, 9))
    level_scene.raise_event(button, 'Switch', key="door-1", state=True)


    button = level_scene.build_button("door-2", "tileRock_tile.png", (2, 12))
    level_scene.build_door("door-2", (14, 3))
    level_scene.raise_event(button, 'Switch', key="door-2", state=True)


    button = level_scene.build_button("door-3", "tileRock_tile.png", (9, 2))
    level_scene.build_door("door-3", (18, 9))
    level_scene.raise_event(button, 'Switch', key="door-3", state=True)


    e = ShipPart('smallRockStone.png', level_scene.load_level)
    level_scene.add_entity(e, (9, 12))



def handle_internal_events(level_scene):
    """
    Handle non-entity specific events here
    (or entity specific events if that means getting the game done on time)
    """
    pass
