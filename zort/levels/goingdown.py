"""
Going Down!

This is the first level. Zort has been shot out of orbit and
crashlanded here. This level should be relatively straight forward and
take no more than 2 minutes to complete. There should be no monsters,
an obvious path, one door and one switch to go through.
"""

# import your game entities here
# implement any level specific enemies here

from zort.entity import *
from zort.enemies import *
from zort.hero import Hero
from zort.level import Task
from zort import hex_model
from zort import resources


def setup_level(level_scene):
    """
    Initialize your entities
    """
    button = level_scene.build_button("test-door", "tileRock_tile.png", (9, 8))
    level_scene.build_door("test-door", (14, 9))
    level_scene.build_door("test-door", (14, 8))
    level_scene.raise_event(button, 'Switch', key="test-door", state=True)

    e = ShipPart('smallRockStone.png', level_scene.load_level)
    level_scene.add_entity(e, (16, 10))


def handle_internal_events(level_scene):
    """
    Handle non-entity specific events here
    (or entity specific events if that means getting the game done on time)
    """
    pass
