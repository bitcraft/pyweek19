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
        self.target_position = None
        self.home_position = None
        self.ramble_radius = 2
        self.path = None
        self.cell_snap = .05
        self.accel_speed = .0001
        self.max_accel = .0004
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
            if self.home_position is None:
                self.home_position = Vector3(*self.position)
                fsm.home()

            if not self.position == self.home_position:
                start = sprites_to_hex(self.position)
                home = sprites_to_hex(self.home_position)
                self.path = scene.model.pathfind(start, home)[0]

            else:
                fsm.home()

        if fsm.isstate('rambling'):
            if not self.path:
                if self.home_position is None:
                    self.home_position = Vector3(*self.position)
                    self.home_position.z = 0

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

        if self.path is not None:
            if not moving and self.target_position is None:
                self.target_position = Vector3(*axial_to_sprites(self.path.pop(-1)))
                #self.target_position = Vector3(*axial_to_sprites(
                #    evenr_to_axial((5, 5))))

            acc = self.acceleration
            if grounded and self.target_position is not None:
                self.wake()
                self.direction = self.target_position - self.position
                acc += self.direction.normalized() * self.accel_speed
                if abs(acc) > self.max_accel:
                    self.acceleration = acc.normalized() * self.max_accel
                if abs(self.direction) <= self.cell_snap:
                    self.position = Vector3(*self.target_position)
                    self.target_position = None
                    self.stop()


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
