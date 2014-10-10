from zort.entity import GameEntity
from zort import resources


class Hero(GameEntity):
    def __init__(self, filename):
        super(Hero, self).__init__(filename)
        self.move_sound = resources.sounds['scifidrone.wav']
        self._playing_move_sound = False
