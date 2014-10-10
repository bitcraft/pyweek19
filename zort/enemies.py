from fysom import Fysom
from zort.euclid import Vector2, Vector3

from zort.entity import GameEntity
from zort.hex_model import *
from zort import resources


__all__ = ['Enemy',
           'Stalker',
           'Rambler',
           'Tosser']


class Enemy(GameEntity):
    def __init__(self, filename):
        super(Enemy, self).__init__(filename)
        self.ramble_radius = 2
        self.target_position = None
        self.home_position = None
        self.cell_snap = .05
        self.accel = .0001
        self.max_accel = .0004
        self.moving = False
        self.path = list()
        self.direction = Vector3(0, 0, 0)
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

    def handle_internal_events(self, scene):
        self.update_ai(scene, None)
        pass

    def update_ai(self, scene, event):
        fsm = self.fsm
        if fsm.isstate('home'):
            fsm.ramble()

        if fsm.isstate('going_home'):
            if sprites_to_hex(self.position) == sprites_to_hex(self.home):
                fsm.ramble()

        if fsm.isstate('rambling'):
            if not self.path:
                if not self.home_position:
                    self.home_position = Vector3(*self.position)

                blacklist = {sprites_to_hex(sprite.position)
                         for sprite in scene.internal_event_group}

                pos = sprites_to_hex(self.position)
                home = sprites_to_hex(self.home_position)
                self.path = scene.model.pathfind_ramble(
                    pos, home, self.ramble_radius, blacklist)[0]

    def update(self, delta):
        super(GameEntity, self).update(delta)

        fsm = self.fsm
        grounded = self.position.z == self.velocity.z == 0
        moving = self.velocity.x or self.velocity.y or self.velocity.z

        if fsm.isstate('rambling'):
            if not moving and self.target_position is None:
                self.acceleration = Vector3(0, 0, 0)
                self.target_position = Vector3(*axial_to_sprites(self.path.pop(-1)))
                #self.target_position = Vector3(*axial_to_sprites(
                #    evenr_to_axial((5, 5))))

            if grounded and self.target_position is not None:
                self.wake()
                self.direction = self.target_position - self.position
                self.acceleration += self.direction.normalized() * self.accel
                if abs(self.acceleration) > self.max_accel:
                    self.acceleration = self.acceleration.normalized() * self.max_accel
                if abs(self.direction) <= self.cell_snap:
                    self.position = Vector3(*self.target_position)
                    self.stop()
                    self.target_position = None


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
