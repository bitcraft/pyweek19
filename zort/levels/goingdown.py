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


def setup_level(level_scene):
    """
    Initialize your entities
    """
    # level_scene.add_entity(Saucer, 'shipPink_manned.png', (5, 5))
    # level_scene.add_entity(Enemy, "alienGreen.png", (9, 9))
    # level_scene.add_entity(Hero, "alienBlue.png", (1, 1))
    button = level_scene.add_button("test-door", "tileRock_tile.png", (9, 8))
    level_scene.add_door("test-door", "smallRockStone.png", (14, 9))
    level_scene.add_door("test-door", "smallRockStone.png", (14, 8))
    level_scene.raise_event(button, 'Switch', key="test-door", state=True)

    # # start the silly timer to drop powerups
    # #timer = Task(self.new_powerup, 5000, -1)
    # #self.timers.add(timer)

    pass


def handle_internal_events(level_scene):
    """
    Handle non-entity specific events here
    (or entity specific events if that means getting the game done on time)
    """
    pass
