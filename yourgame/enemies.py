from yourgame.entity import GameEntity
from yourgame import resources


__all__ = ['Stalker',
           'Rambler',
           'Tosser']


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
