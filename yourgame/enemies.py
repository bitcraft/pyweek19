from fysom import Fysom

from yourgame.entity import GameEntity
from yourgame.hex_model import sprites_to_hex
from yourgame import resources


__all__ = ['Enemy',
           'Stalker',
           'Rambler',
           'Tosser']


class Enemy(GameEntity):
    def __init__(self, filename):
        super(Enemy, self).__init__(filename)
        self._home = (None, None)
        self.path = ()
        self.fsm = Fysom({'initial': 'home',
                          'events': [
                              {'name': 'go_home',
                               'src': 'seeking',
                               'dst': 'going_home'},
                              {'name': 'ramble',
                               'src': ['home', 'seeking'],
                               'dst': 'rambling'},
                              {'name': 'seek_player',
                               'src': ['home', 'going_home', 'rambling'],
                               'dst': 'seeking'}
                          ]})

    @property
    def home(self):
        return self._home

    @home.setter
    def home(self, coord):
        self._home = coord
        self.position.x, self.position.y = coord

    def handle_internal_events(self, scene):
        fsm = self.fsm
        if fsm.isstate('home'):
            fsm.ramble()
        if fsm.isstate('going_home'):
            if self.position == self.home:
                print("Now rambling")
                fsm.ramble()
        if fsm.isstate('rambling'):
            blacklist = {sprites_to_hex(sprite.position)
                         for sprite in scene.internal_event_group}
            pos = sprites_to_hex(self.position)
            home = sprites_to_hex(self.home)
            self.path = scene.model.pathfind_ramble(pos, home, 2, blacklist)
            print(list(self.path[0]))


class Stalker(GameEntity):
    """ follows the player
    """
    def __init__(self, filename):
        super(Stalker, self).__init__(filename)
        self.move_sound = resources.sounds['scifidrone.wav']
        self._playing_move_sound = False


class Rambler(GameEntity):
    """ random walks
    """
    def __init__(self, filename):
        super(Rambler, self).__init__(filename)
        self.move_sound = resources.sounds['scifidrone.wav']
        self._playing_move_sound = False


class Tosser(GameEntity):
    """ tosses.
    """
    def __init__(self, filename):
        super(Tosser, self).__init__(filename)
        self.move_sound = resources.sounds['scifidrone.wav']
        self._playing_move_sound = False
