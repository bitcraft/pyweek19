import random

from fysom import Fysom
from zort.euclid import Vector2, Vector3

from zort.level import Task
from zort.entity import GameEntity
from zort.hex_model import *
from zort import resources


__all__ = ['Enemy',
           'Stalker',
           'Rambler',
           'Tosser',
           'Saucer']


class Enemy(GameEntity):
    def __init__(self, filename):
        super(Enemy, self).__init__(filename)
        self.move_sound = resources.sounds['scifidrone.wav']
        self.target_position = None
        self.home_position = None
        self.ramble_radius = 2
        self.cells_followed = 0
        self.follow_persistence = self.ramble_radius+1
        self.path = None
        self.cell_snap = .01
        self.accel_speed = .000095
        self.max_accel = .000375
        self.direction = Vector3(0, 0, 0)
        self.fsm = Fysom({'initial': 'home',
                          'events': [
                              {'name': 'go_home',
                               'src': 'seeking',
                               'dst': 'going_home'},
                              {'name': 'ramble',
                               'src': ['home', 'seeking', 'going_home'],
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

        hpos = scene.hero.position
        dist = abs(self.position - hpos)
        if dist <= self.ramble_radius:
            pos = sprites_to_hex(self.position)
            next = sprites_to_hex(hpos)
            self.path = scene.model.pathfind(pos, next)[0]
            print("Seeking", self.path)
            self.cells_followed = 0
            if not fsm.isstate('seeking'):
                fsm.seek_player()
        elif fsm.isstate('seeking'):
            if not self.path:
                if self.cells_followed < self.follow_persistence:
                    pos = sprites_to_hex(self.position)
                    next = sprites_to_hex(hpos)
                    self.path = scene.model.pathfind(pos, next)[0]
                    print("Seeking", self.path)
                else:
                    fsm.go_home()
                    self.path = None
            else:
                fsm.go_home()

        if fsm.isstate('home'):
            fsm.ramble()
            self.path = None

        if fsm.isstate('going_home'):
            if self.home_position is None:
                self.home_position = Vector3(*self.position)

            if not self.position == self.home_position:
                if not self.path:
                    start = sprites_to_hex(self.position)
                    home = sprites_to_hex(self.home_position)
                    self.path = scene.model.pathfind(start, home)[0]
                    print("Going home", self.path)
            else:
                fsm.ramble()

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
        super(Enemy, self).update(delta)

        fsm = self.fsm
        grounded = self.position.z == self.velocity.z == 0
        moving = self.velocity.x or self.velocity.y or self.velocity.z

        if self.path is not None:
            if not moving and self.target_position is None:
                self.target_position = Vector3(*axial_to_sprites(
                    self.path.pop(-1)))
                if fsm.isstate('seeking'):
                    self.cells_followed += 1



            acc = self.acceleration
            if grounded and self.target_position is not None:
                self.wake()
                self.direction = self.target_position - self.position
                #acc *= .1
                #acc += self.direction.normalized() * self.accel_speed
                self.acceleration = self.direction.normalized() * self.max_accel
                if abs(acc) > self.max_accel:
                    self.acceleration = acc.normalized() * self.max_accel
                if abs(self.direction) <= self.cell_snap:
                    self.position = Vector3(*self.target_position)
                    self.target_position = None
                    self.stop()
        else:
            self.stop()


class Stalker(Enemy):
    """ follows the player
    """
    def __init__(self, filename):
        super(Stalker, self).__init__(filename)
        self.move_sound = resources.sounds['lose7.ogg']
        self._playing_move_sound = False


class Rambler(Enemy):
    """ random walks
    """
    def __init__(self, filename):
        super(Rambler, self).__init__(filename)
        self.move_sound = resources.sounds['lose7.ogg']
        self._playing_move_sound = False


class Tosser(Enemy):
    """ tosses.
    """
    def __init__(self, filename):
        super(Tosser, self).__init__(filename)
        self.move_sound = resources.sounds['lose7.ogg']
        self._playing_move_sound = False


class Saucer(Enemy):
    # pours sauce?  idk.
    def __init__(self, filename):
        super(Saucer, self).__init__(filename)
        self.laser_sound = resources.sounds['z_laser-gun-2.wav']
        self.move_sound = resources.sounds['lose7.ogg']
        self.target_position = None
        self.home_position = None
        self.path = None
        self.ramble_radius = 5
        self.cell_snap = .01
        self.accel_speed = .0005
        self.max_velocity = [.0005, .0005, .0005]
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

        t = Task(self.shoot, random.randint(100, 100))
        self.timers.add(t)

    def update(self, delta):
        super(Saucer, self).update(delta)

        fsm = self.fsm
        grounded = self.position.z == self.velocity.z == 0
        moving = self.velocity.x or self.velocity.y or self.velocity.z

        if self.position.z < 2:
            self.velocity.z = 0
            self.acceleration.z = 0
            self.position.z = 2
            self.gravity = False
            self._layer = 3

        if self.path is not None:
            if not moving and self.target_position is None:
                self.target_position = Vector3(*axial_to_sprites(
                    self.path.pop(-1)))

            acc = self.acceleration
            if self.target_position is not None:
                self.wake()
                direction = self.target_position - self.position
                self.acceleration = direction.normalized() * self.accel_speed
                if abs(direction) <= self.cell_snap:
                    self.position = Vector3(*self.target_position)
                    self.target_position = None

    def shoot(self):
        t = Task(self.shoot, random.randint(3000, 6000))
        self.timers.add(t)

        self.laser_sound.set_volume(.4)
        self.laser_sound.play()
        g = self.view_group

        laser = GameEntity('laserGreen2.png')
        self.spawn(laser)

        laser.anchor = Vector2(*laser.rect.midtop)
        laser.update_image()
        laser.attach(self, (0, 0, 0))

        t = Task(laser.kill, 10000)
        self.timers.add(t)
