from fysom import Fysom
from zort.euclid import Vector2

from zort.entity import GameEntity
from zort.hex_model import sprites_to_hex
from zort import resources


__all__ = ['Enemy',
           'Stalker',
           'Rambler',
           'Tosser']


class Enemy(GameEntity):
    def __init__(self, filename):
        super(Enemy, self).__init__(filename)
        self._home = (None, None)
        self.accel = 10
        self.moving = False
        self.radius = 2
        self.path = ()
        self.direction = Vector2(0, 0)
        self.target_cell = (None, None)
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
        pass

    def update_ai(self, scene, event):
        fsm = self.fsm
        if fsm.isstate('home'):
            fsm.ramble()
        if fsm.isstate('going_home'):
            if self.position == self.home:
                fsm.ramble()
        if fsm.isstate('rambling'):
            blacklist = {sprites_to_hex(sprite.position)
                         for sprite in scene.internal_event_group}
            pos = sprites_to_hex(self.position)
            home = sprites_to_hex(self.home)
            if not self.path:
                self.path = list(scene.model.pathfind_ramble(
                    pos, home, self.radius, blacklist)[0])

    def update(self, delta):
        super(GameEntity, self).update(delta)

        current_position = sprites_to_hex(self.position)
        if self.moving:
            if current_position == self.target_cell:
                self.moving = False

        if self.path and not self.moving:
            self.target_cell = self.path.pop(0)
            self.direction = Vector2(self.target_cell[0]-current_position[0],
                                     self.target_cell[1]-current_position[1])
            self.moving = True

        if self.moving:
            self.acceleration.y = self.direction[0]*self.accel
            self.acceleration.x = self.direction[1]*self.accel
            self.wake()


class Stalker(GameEntity):
    """ follows the player
    """
    def __init__(self, filename):
        super(Stalker, self).__init__(filename)
        self.move_sound = resources.sounds['lose7.ogg']
        self._playing_move_sound = False


class Rambler(GameEntity):
    """ random walks
    """
    def __init__(self, filename):
        super(Rambler, self).__init__(filename)
        self.move_sound = resources.sounds['lose7.ogg']
        self._playing_move_sound = False


class Tosser(GameEntity):
    """ tosses.
    """
    def __init__(self, filename):
        super(Tosser, self).__init__(filename)
        self.move_sound = resources.sounds['lose7.ogg']
        self._playing_move_sound = False
