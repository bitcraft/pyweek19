from yourgame.scenes import Scene


class TitleScene(Scene):

    def __init__(self, game):
        super(TitleScene, self).__init__("title", game)

    def setup(self):
        print("Setting up title scene")

    def teardown(self):
        print("Tearing down title scene")

    def draw(self, surface):
        print("Drawing title scene")

    def update(self, delta, events):
        print("Updating title scene")

    def resume(self):
        print("Resuming title scene")
