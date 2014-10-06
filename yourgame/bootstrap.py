from pygame import init
from pygame.display import set_mode

from scenes import Game
from title import TitleScene
from level import LevelScene
from dialog import DialogScene

TARGETFPS = 60
SCREENSIZE = (800, 600)


def bootstrap_game():
    init()
    main_surface = set_mode(SCREENSIZE)
    game = Game(TARGETFPS, main_surface)
    game.register_scene(TitleScene(game))
    game.register_scene(LevelScene(game))
    game.register_scene(DialogScene(game))
    game.push_scene("level")
    return game

