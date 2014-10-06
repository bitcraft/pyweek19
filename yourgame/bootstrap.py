import logging
import os
import pygame
from pygame import init
from pygame.display import set_mode

from . import config
from scenes import Game
from title import TitleScene
from level import LevelScene
#from dialog import DialogScene
import resources

logger = logging.getLogger('yourgame.bootstrap')
filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'yourgame.ini')
config.read(filename)


def bootstrap_game():
    init()
    main_surface = set_mode((config.getint('display', 'width'),
                             config.getint('display', 'height')))

    main_surface.fill((0, 0, 0))

    for path, thing in resources.load():
        logger.info('loaded %s', path)
        pygame.event.pump()

    game = Game(config.getint('display', 'target-fps'), main_surface)
    game.register_scene(TitleScene(game))
    game.register_scene(LevelScene(game))
    #game.register_scene(DialogScene(game))
    game.push_scene("level")
    return game
