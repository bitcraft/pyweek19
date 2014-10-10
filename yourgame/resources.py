from os.path import join as jpath
from os.path import basename, abspath
from os.path import isfile
import pygame
import logging
import glob
logger = logging.getLogger('yourgame.resources')

import yourgame.gui

__all__ = ['load', 'sounds', 'images', 'music', 'maps', 'tiles', 'play_music',
           'border']

# because i am lazy
resource_path = None
sounds = None
images = None
music = None
fonts = None
maps = None
tiles = None
border_path = None
border = None

# for dialog scripting
def get_text(heading):
    fh = open(jpath(resource_path, 'dialogs.txt'))

    found = False
    while 1:
        line = fh.readline().strip()
        if line.lower() == heading.lower():
            found = True
            break

    if not found:
        raise ValueError('heading not found: {}'.format(heading))

    line = fh.readline()
    if not line.startswith('='):
        raise ValueError('improperly formatted header: {}'.format(heading))

    while 1:
        line = fh.readline().strip()
        if not line:
            continue
        yield line


def load():
    pygame.font.init()

    logger.info("loading")
    from yourgame import config

    global resource_path
    global sounds, images, music, fonts, maps, tiles
    global border, border_path

    tiles = dict()
    sounds = dict()
    images = dict()
    music = dict()
    fonts = dict()
    maps = dict()

    resource_path = config.get('paths', 'resource-path')
    resource_path = abspath(resource_path)
    border_path = jpath(resource_path, 'dialog.png')
    sounds_path = jpath(resource_path, 'sounds', '*')

    # load the tiles
    tile_path = jpath(resource_path, 'tiles', '*png')
    for filename in glob.glob(tile_path):
        path = jpath(resource_path, 'tiles', filename)
        image = pygame.image.load(path).convert_alpha()
        tiles[basename(filename)] = image
        yield path, image

    for name, filename in config.items('font-files'):
        path = jpath(resource_path, 'fonts', filename)
        fonts[name] = path
        yield path, path

    vol = config.getint('sound', 'sound-volume') / 100.
    for filename in glob.glob(sounds_path):
        logger.info("loading %s", filename)
        try:
            if isfile(filename):
                sound = pygame.mixer.Sound(filename)
                sound.set_volume(vol)
                sounds[basename(filename)] = sound
                yield filename, sound
        except pygame.error:
            pass

    for name, filename in config.items('image-files'):
        path = jpath(resource_path, 'images', filename)
        logger.info("loading %s", path)
        image = pygame.image.load(path)
        images[name] = image
        yield path, image

    for name, filename in config.items('map-files'):
        path = jpath(resource_path, 'maps', filename)
        logger.info("loading %s", path)
        maps[name] = path
        yield path, map

    for name, filename in config.items('music-files'):
        path = jpath(resource_path, 'music', filename)
        logger.info("loading %s", path)
        music[name] = path
        yield path, path


def play_music(name):
    from yourgame import config

    try:
        track = music[name]
        logger.info("playing %s", track)
        vol = config.getint('sound', 'music-volume') / 100.
        if vol > 0:
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.load(track)
            pygame.mixer.music.play(-1)
    except pygame.error:
        raise
