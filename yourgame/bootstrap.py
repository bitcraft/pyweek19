import logging
import os
import pygame
from pygame.display import set_mode

from yourgame import config
from yourgame import gui
from yourgame.scenes import Game
from yourgame.title import TitleScene
from yourgame.level import LevelScene
from yourgame import resources

logger = logging.getLogger('yourgame.bootstrap')
filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'yourgame.ini')
config.read(filename)


def bootstrap_game():
    pygame.display.init()
    pygame.mixer.init(frequency=config.getint('sound', 'frequency'),
                         buffer=config.getint('sound', 'buffer'))
    pygame.font.init()
    pygame.init()

    main_surface = set_mode((config.getint('display', 'width'),
                             config.getint('display', 'height')))

    main_surface.fill((0, 0, 0))
    gui.draw_text(main_surface, "loading, please wait...", (255,255,255),
                  main_surface.get_rect())
    pygame.display.flip()

    for path, thing in resources.load():
        logger.info('loaded %s', path)
        pygame.event.pump()

    game = Game(config.getint('display', 'target-fps'), main_surface)
    game.register_scene(TitleScene(game))
    game.register_scene(LevelScene(game))
    game.push_scene("level")
    game.scenes["level"].view.data.save_to_disk("/tmp/foo.json")
    game.scenes["level"].view.data.load_from_disk("/tmp/foo.json")
    return game
