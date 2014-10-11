"""
Loading code for the levels
"""

import importlib
import zort.levels
from zort import resources


def load_level(level_name, level_scene):
    level_module = importlib.import_module("." + level_name, "zort.levels")
    level_scene.view.data.load_from_disk(resources.maps[level_name])
    level_module.setup_level(level_scene)
    return level_module
