from itertools import product
import math
import pygame
from pygame.transform import smoothscale

from yourgame.euclid import Point2, Point3, Vector3, Matrix4


__all__ = ['LevelView']


class LevelView(pygame.sprite.Group):
    def __init__(self, layer, tile_size, tile_image):
        super(LevelView, self).__init__()
        self.layer = layer
        layer.set_renderer(self)

        self.screen_offset = None
        self.world_offset = Vector3(10, 10, 0)

        ds = len(layer.data)
        self.view = pygame.Rect(0, 0, ds, ds)

        self.refresh = True
        self.surface = None
        self.highlighted = set()
        self.queue = set()
        self.dirty_rect_list = list()
        self.prj = None
        self.inv_prj = None
        self.tile_size = None
        self.tile_images = None
        self.tile_anchor = None
        self_size = None

        self.set_tileset(tile_size, tile_image)
        self.reproject(math.radians(45))

    def set_tileset(self, tile_size, surface):
        self.tile_size = float(tile_size)
        self.tile_images = list()

        # required for smoothscale
        d = int(self.tile_size * 1.67)
        ts = (d, d)

        iw, ih = surface.get_size()
        tw = iw // 3
        th = ih // 2

        self.tile_anchor = tw // 2, th // 2

        p = product(range(0, iw, tw), range(0, ih, th))
        for index, (x, y) in enumerate(p):
            rect = (x, y, tw, th)
            _tile = smoothscale(surface.subsurface(rect), ts)
            tile = pygame.Surface(_tile.get_size())
            tile.fill((255, 0, 255))
            tile.blit(_tile, (0, 0))
            self.tile_images.append(tile)

    def center(self, (x, y)):
        pass

    @staticmethod
    def cart_iso(self, pos):
        x, y = pos
        return x - y, (x + y) / 2

    @staticmethod
    def iso_cart(self, pos):
        x, y = pos
        return (2 * y + x) / 2, (2 * y - x) / 2

    def reproject(self, rot):
        self.prj = Matrix4()
        self.prj.scale(self.tile_size, self.tile_size, 1.0)

        # NOTE: this 67 value needs tweaking!
        self.prj.rotate_axis(math.radians(67), Vector3(1, 0, 0))
        self.prj.rotate_axis(rot, Vector3(0, 0, 1))

        self.inv_prj = Matrix4()
        self.inv_prj.scale(self.tile_size, self.tile_size / 2, 1.0)
        self.inv_prj.rotate_axis(rot, Vector3(0, 0, 1))
        self.inv_prj = self.inv_prj.inverse()

    def highlight(self, (x, y, z)):
        position = (int(x), int(y))
        if position not in self.highlighted:
            self.refresh = True
            self.highlighted.add(position)

    def unhighlight(self, (x, y, z)):
        try:
            self.highlighted.remove((int(x), int(y)))
        except KeyError:
            pass

    def draw(self, surface):
        """
        draw the map and sprites onto a surface.
        """
        self._size = surface.get_size()
        place = self.place
        surblit = surface.blit

        if self.surface is None:
            w, h = self._size
            self.screen_offset = Vector3(w // 2, h *1.5, 0)
            self.surface = pygame.Surface(self._size)

        if len(self.queue) == 0:
            self.flush_queue()
            self.refresh = True

        if self.refresh:
            self.redraw()
            surface.blit(self.surface, (0, 0))
            self.dirty_rect_list = []
            self.refresh = False

        for rect in self.dirty_rect_list:
            surblit(self.surface, rect, area=rect)

        self.dirty_rect_list = []

        sprites = [(sum(s.position), s) for s in self.sprites()]
        sprites.sort()

        for index, spr in sprites:
            p = self.project_point(spr.position)
            try:
                w, h = spr.image.get_size()
                p.y -= h
                p.x -= w / 2
                rect = pygame.Rect(int(p.x), int(p.y), w, h)
                self.dirty_rect_list.append(rect)
                surblit(spr.image, rect)
            except AttributeError:
                p2 = self.project_point(spr.endpoint)
                pygame.draw.line(surface, (192, 200, 255), (p.x, p.y),
                                 (p2.x, p2.y), int(spr.life))
                rect = pygame.Rect(p.x, p.y, p.x - p2.x, p.y - p2.y)
                self.dirty_rect_list.append(rect)

    def place(self, sprite):
        """ adjust the apparent position of a sprite """
        p = self.project_point(sprite.position)
        w, h = sprite.image.get_size()
        p.y -= h
        p.x -= w / 2
        return map(int, p[:2])

    def mark_changed(self, position):
        self.queue.add((position[0], position[1], 0))

    def draw_tile(self, surface, pos):
        x, y, z = pos

        ax, ay, az = self.project_point(Vector3(x, y, z))
        bx, by, bz = self.project_point(Vector3(x + 1, y, z))
        cx, cy, cz = self.project_point(Vector3(x + 1, y + 1, z))
        dx, dy, dz = self.project_point(Vector3(x, y + 1, z))

        points = ((ax, ay), (bx, by), (cx, cy), (dx, dy))
        color = (255, 128, 255)
        index = 5

        print ax - bx

        ox, oy = self.tile_anchor

        surface.blit(self.tile_images[index], (ax - ox, ay - oy))
        pygame.draw.polygon(surface, color, points, 1)

    def paint_tile(self, surface, pos, width=0, color=None, outline=False):
        x, y, z = pos

        ax, ay, az = self.project_point(Vector3(x, y, z))
        bx, by, bz = self.project_point(Vector3(x + 1, y, z))
        cx, cy, cz = self.project_point(Vector3(x + 1, y + 1, z))
        dx, dy, dz = self.project_point(Vector3(x, y + 1, z))

        points = ((ax, ay), (bx, by), (cx, cy), (dx, dy))
        color = (255, 128, 0)

        pygame.draw.polygon(surface, color, points, width)
        if outline:
            pygame.draw.lines(surface, (200, 200, 180), 1, points, 3)

    def project_point(self, point):
        """ world --> screen """
        return self.prj * (point - self.world_offset) + self.screen_offset

    def unproject_point(self, point):
        """ screen --> world """
        return self.inv_prj * (point - self.screen_offset) + self.world_offset

    def flush_queue(self):
        [self.draw_tile(self.surface, i) for i in self.queue]
        self.queue = set()

    def redraw(self):
        if self.surface:
            self.surface.fill((0, 0, 0))
        else:
            self.surface = pygame.Surface(self._size)
        self.queue = product(xrange(self.view.left, self.view.right),
                             xrange(self.view.top, self.view.bottom),
                             xrange(1))
        self.flush_queue()

        self.surface.lock()
        for x, y in self.highlighted:
            try:
                self.paint_tile(self.surface, (x, y, 0), width=2,
                                color=(255, 255, 240))
            except IndexError:
                pass
        self.surface.unlock()
