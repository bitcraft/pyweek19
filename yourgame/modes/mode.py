class LevelSceneMode(object):
    """ provides various handlers to abstract gameplay into modes
    """
    def __init__(self):
        pass

    def handle_click(self, button, view, cell):
        pass

    def draw(self, surface):
        pass

    def update(self, delta, events):
        pass
