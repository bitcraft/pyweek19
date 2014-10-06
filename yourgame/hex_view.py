import pygame
import pygame.gfxdraw
import threading
from pygame.transform import smoothscale
from six.moves import queue
from math import sin, cos, pi, sqrt, radians, ceil
from itertools import product

from yourgame.euclid import Point3, Vector3, Matrix4
from yourgame import resources
from yourgame.hex_model import *


__all__ = ['HexMapView']

class BlitThread(threading.Thread):
    def __init__(self, q, blit):
        threading.Thread.__init__(self)
        self.q = q
        self.blit = blit
        self.running = False
        self.daemon = True

    def run(self):
        blit = self.blit
        get = self.q.get
        task_done = self.q.task_done

        self.running = True
        while self.running:
            try:
                surface, pos = get(1)
            except queue.Empty:
                self.running = False
                "dead"
                break

            else:
                blit(surface, pos)
                task_done()


def vec(i):
    return Vector3(i[0], i[1], 0)


def get_hex_draw(mat, size):
    def draw_hex(surface, coords, border_color, fill_color):
        new_points = [(coords[0] + x, coords[1] + y) for x, y in points]
        if fill_color:
            fill(surface, new_points, fill_color)
        outline(surface, new_points, border_color)

    points = list()
    temp = 2 * pi / 6.
    for i in range(6):
        angle = temp * (i + .5)
        x, y = size * cos(angle), size * sin(angle)
        xx, yy, zz = mat * Point3(x, y, 0)
        points.append((xx, yy))

    outline = pygame.gfxdraw.aapolygon
    fill = pygame.gfxdraw.filled_polygon
    return draw_hex


def get_hex_tile(mat, radius):
    def draw_tile(blit, filename, coords):
        x, y, z = coords
        tile = tile_dict[filename]
        blit((tile, (int(x - half_width), int(y - radius))))

    height = radius * 2 + 1
    width = (sqrt(3) / 2 * height)
    half_width = int(width / 2)
    size = (int(width), int(height))
    tile_dict = dict()
    for filename, image in resources.tiles.items():
        if filename.startswith('tile'):
            if not size[0] == image.get_width():
                image = smoothscale(image, size)
            tile_dict[filename] = image

    # this is a heck!
    radius -= 16

    return draw_tile


def get_projection(data, radius, mat, rect):
    # caches the entire operation of axial coords to the screen
    # returns the rect representing the map's boundry and a function to
    # call that caches coordinate transformations
    # if sending fractional data, do not cache the transformation

    w, h = rect.size
    size_sqrt3 = radius * sqrt(3)
    size_ratio = radius * (3. / 2.)
    tile_h = radius * 2
    tile_w = (sqrt(3) / 2) * tile_h
    mw = (data.width - 1) * tile_w
    mh = (data.height - 1) * tile_h * 3 / 4
    hw = (w / 2) - (mw / 2)
    hh = (h / 2) - (mh / 2)
    screen_offset = Vector3(hw, hh, 0)
    map_rect = pygame.Rect((hw, hh), (mw, mh))

    def project(i, cell):
        # convert => cart
        coords = size_sqrt3 * (i[0] + i[1] / 2.), size_ratio * i[1]

        # project tilt and return
        coords = mat * Vector3(*coords)

        # translate on screen
        coords += screen_offset

        return coords

    # cache of the expensive axial => cart transform
    cache = dict()
    def cached_project(i, cell=None, use_cache=True):
        if use_cache:
            try:
                return cache[i]
            except KeyError:
                coords = project(i, cell)
                cache[i] = coords
                return coords
        else:
            return project(i, cell)

    return map_rect, cached_project


class HexMapView(pygame.sprite.Group):
    border_color = 61, 55, 42, 64
    line_color = 61, 42, 42
    fill_color = 161, 92, 120
    hover_color = 192, 184, 190, 128
    select_color = 195, 177, 142

    def __init__(self, data, radius):
        super(HexMapView, self).__init__()
        self.data = data
        self.dirty = False
        self._rect = None
        self._old_hovered = None
        self._hovered = None
        self._selected = list()
        self._hex_draw = None
        self._hex_tile = None
        self._project = None
        self.hex_radius = None
        self.refresh_map = None
        self.dirty_rects = None
        self.prj = None
        self.inv_prj = None
        self.tilt = 43
        self._buffer = None
        self._thread = None
        self.reproject(self.tilt)
        self.set_radius(radius)

    def reproject(self, tilt):
        self.prj = Matrix4()
        self.prj.rotate_axis(radians(tilt), Vector3(1, 0, 0))
        self.inv_prj = self.prj.inverse()
        if self.hex_radius:
            self.set_radius(self.hex_radius)
        self.dirty = True
        self.refresh_map = True

    def set_radius(self, radius):
        self.hex_radius = radius
        self._hex_draw = get_hex_draw(self.prj, radius)
        self._hex_tile = get_hex_tile(self.prj, radius)
        self._project = None
        self.dirty = True
        self.refresh_map = True

    def select_cell(self, cell):
        # when clicked
        self._selected.append(cell)
        self.dirty = True
        self.refresh_map = True

    def highlight_cell(self, cell):
        # hightlight cell (like for picking with mouse)
        if self._old_hovered is not cell:
            self._old_hovered = self._hovered
            self._hovered = cell
            self.refresh_map = True

    def point_from_surface(self, point):
        # # return a point in map space from the surface (broken!)
        if self._rect is None:
            return None

        x, y = point[:2]
        x -= self._map_rect.left
        y -= self._map_rect.top
        point = Vector3(x, y, 0)
        point = self.inv_prj * point

        # hack?  yes
        point.y = point.y * (90.0 / (90 - self.tilt))

        x, y, z = vec(pixel_to_axial(point, self.hex_radius))
        return x, y

    def point_from_local(self, point):
        # if self._rect is None:
        # return None
        #
        # point = Vector3(*point) - (self._rect.left, self._rect.top, 0)
        # return point[0] + self._hw, point[1] + self._hh
        raise NotImplementedError

    def clear(self, surface, bgk=None):
        if self._buffer is None: return
        blit = surface.blit
        _buffer = self._buffer
        [blit(_buffer, rect, rect) for rect in self.dirty_rects]

    def draw(self, surface):
        # all temp variable to speed up the axial => screen space conversion
        self._rect = surface.get_rect()

        _dirty = list()

        if self.dirty:
            self._buffer = pygame.Surface(self._rect.size)
            self.reproject(self.tilt)
            self.dirty = False
            _dirty = [self._rect]

        if self._thread is None:
            self._queue = queue.Queue()
            self.thread = BlitThread(self._queue, self._buffer.blit)
            self.thread.start()

        if self._project is None:
            self._map_rect, \
            self._project = get_projection(self.data,
                                           self.hex_radius,
                                           self.prj,
                                           self._rect)

        put_tile = self._queue.put
        project = self._project
        draw_tile = self._hex_tile
        draw_hex = self._hex_draw
        _buffer = self._buffer

        # draw the cell tiles
        # get in draw order
        if self.refresh_map:
            for qq, rr in product(range(10), range(10)):
                # convert => axial
                q, r = evenr_to_axial((rr, qq))
                cell = self.data.get_cell((q, r))

                # convert => screen
                pos = Vector3(*project((q, r), cell))

                if cell.height > 0:
                    # draw cell at base layer
                    pos.y -= self.hex_radius / 2 * float(cell.height)
                    draw_tile(put_tile, cell.filename, pos)

                    # translate the cell height
                    pos.y -= self.hex_radius / 2 * float(cell.height)
                    draw_tile(put_tile, cell.filename, pos)

                else:
                    draw_tile(put_tile, cell.filename, pos)

            self._queue.join()
            self.refresh_map = False
            _dirty = [self._rect]

        # draw cell lines (outlines and highlights)
        _buffer.lock()
        for pos, cell in self.data.cells:
            if cell in self._selected:
                fill = self.select_color

            elif cell is self._hovered:
                fill = self.hover_color

            else:
                continue

            # convert => screen
            pos = project(pos)
            draw_hex(_buffer, pos, self.border_color, fill)
        _buffer.unlock()

        for rect in _dirty:
            surface.blit(_buffer, rect.topleft, rect)

        _sprite_dirty = list()

        # # draw sprites to the surface, not the buffer
        for sprite in self.sprites():
            # convert => axial
            q, r = evenr_to_axial(sprite.position[:2])

            # convert => screen
            # no cache here since we may be dealing with fractional coordinates
            x, y, z = project((q, r), use_cache=False)

            # translate anchor and blit
            pos = (int(x - sprite.anchor.x), int(y - sprite.anchor.y))
            rect = surface.blit(sprite.image, pos)
            _sprite_dirty.append(rect)

        _dirty.extend(_sprite_dirty)
        self.dirty_rects = _dirty

        return _dirty