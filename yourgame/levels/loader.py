"""
Loading code for the levels
"""

import yourgame.levels
from yourgame.resources import maps


def load_level(level_name, level_scene):
    level_module = getattr(yourgame.levels, level_name)
    level_scene.view.data.load_from_file(maps[level_name])
    level_module.setup_level(level_scene)
    return level_module
