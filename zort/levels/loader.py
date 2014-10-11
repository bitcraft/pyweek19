"""
Loading code for the levels
"""

import importlib

import zort.levels
from zort import resources


def load_level(level_name, level_scene):
    level_module = importlib.import_module("zort.levels.%s" % level_name)
    level_module = getattr(zort.levels, level_name)
    level_scene.view.data.load_from_file(resources.maps[level_name])
    level_module.setup_level(level_scene)
    return level_module
