import pygame
import pygame.gfxdraw
from pygame.transform import smoothscale
from math import sin, cos, pi, sqrt, radians, ceil
from itertools import product

from yourgame.euclid import Point3, Vector3, Matrix4
from yourgame import resources
from yourgame.hex_model import *


__all__ = ['HexMapView']


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
    def draw_tile(surface, filename, coords):
        x, y, z = coords
        tile = tile_dict[filename]
        surface.blit(tile, (int(x - half_width), int(y - radius)))

    height = radius * 2
    width = (sqrt(3) / 2 * height) + 1
    half_width = int(width / 2)
    size = (int(width), int(height))
    tile_dict = dict()
    for filename, image in resources.tiles.items():
        if filename.startswith('tile'):
            if not size[0] == image.get_width():
                image = smoothscale(image, size)
            tile_dict[filename] = image

    # this is a heck!
    radius -= 8

    return draw_tile


class HexMapView(pygame.sprite.Group):
    def __init__(self, data, radius):
        super(HexMapView, self).__init__()
        self.data = data
        self._rect = None
        self._old_hovered = None
        self._hovered = None
        self._selected = list()
        self._hw = None
        self._hh = None
        self._hex_draw = None
        self._hex_tile = None
        self.hex_radius = None
        self.prj = None
        self.inv_prj = None
        self.tilt = 45
        self.reproject(self.tilt)
        self.set_radius(radius)

    def reproject(self, tilt):
        self.prj = Matrix4()
        self.prj.rotate_axis(radians(tilt), Vector3(1, 0, 0))
        self.inv_prj = self.prj.inverse()
        if self.hex_radius:
            self.set_radius(self.hex_radius)

    def set_radius(self, radius):
        self.hex_radius = radius
        self._hex_draw = get_hex_draw(self.prj, radius)
        self._hex_tile = get_hex_tile(self.prj, radius)

    def select_cell(self, cell):
        # when clicked
        self._selected.append(cell)

    def highlight_cell(self, cell):
        # hightlight cell (like for picking with mouse)
        self._old_hovered = self._hovered
        self._hovered = cell

    def point_from_surface(self, point):
        ## return a point in map space from the surface (broken!)
        if self._rect is None:
            return None

        point = self.inv_prj * (Vector3(*point) - (self._hw, self._hh, 0))

        #hack?  yes
        point.y = point.y * (90.0 / (90 - self.tilt))

        x, y, z = vec(pixel_to_axial(point, self.hex_radius))
        return x, y

    def point_from_local(self, point):
        # if self._rect is None:
        #     return None
        #
        # point = Vector3(*point) - (self._rect.left, self._rect.top, 0)
        # return point[0] + self._hw, point[1] + self._hh
        raise NotImplementedError

    def draw(self, surface):
        # all temp variable to speed up the axial => screen space conversion
        self._rect = surface.get_rect()
        rect = self._rect
        w, h = rect.size
        size_sqrt3 = self.hex_radius * sqrt(3)
        size_ratio = self.hex_radius * (3. / 2.)
        tile_h = self.hex_radius * 2
        tile_w = (sqrt(3) / 2) * tile_h
        mw = (self.data.width - 1) * tile_w
        mh = (self.data.height - 1) * tile_h * 3 / 4
        hw = (w / 2) - (mw / 2)
        hh = (h / 2) - (mh / 2)
        self._hw = hw
        self._hh = hh
        draw_tile = self._hex_tile
        draw_hex = self._hex_draw

        border_color = 61, 55, 42, 64
        line_color = 61, 42, 42
        fill_color = 161, 92, 120
        hover_color = 192, 184, 190, 128
        select_color = 195, 177, 142

        # comment out later
        draw_outlines = 1
        self.reproject(self.tilt)

        _clip = surface.get_clip()
        surface.set_clip(rect)

        # draw the cell tiles
        # get in blitting/draw order
        for qq, rr in product(range(10), range(10)):
            # convert => axial
            q, r = evenr_to_axial((rr, qq))
            cell = self.data.get_cell((q, r))

            # convert => cart
            pos = size_sqrt3 * (q + r / 2.), size_ratio * r

            # project tilt
            pos = self.prj * Vector3(*pos)

            # handle raised tiles (fake y axis)
            # this has to be redrawn over the grid
            if cell.raised:
                pos[1] -= self.hex_radius / 2

            # translate map center
            pos += (hw, hh, 0)

            draw_tile(surface, cell.filename, pos)

        # draw cell lines (outlines and highlights)
        if draw_outlines:
            surface.lock()
            for (q, r), cell in self.data.cells:
                # convert => cart
                pos = size_sqrt3 * (q + r / 2.), size_ratio * r

                # project tilt
                pos = self.prj * Vector3(*pos)

                # translate map center
                pos += (hw, hh, 0)

                if cell in self._selected:
                    fill = select_color

                elif cell is self._hovered:
                    fill = hover_color

                else:
                    fill = None

                if fill is not None:
                    draw_hex(surface, pos, border_color, fill)
            surface.unlock()

        ## draw sprites
        for sprite in self.sprites():
            # convert => axial
            q, r = evenr_to_axial(sprite.position[:2])

            # convert => cart
            pos = size_sqrt3 * (q + r / 2.), size_ratio * r

            # project tilt
            pos = self.prj * Vector3(*pos)

            # translate map center
            x, y, z = pos + (hw, hh, 0)

            # translate anchor and blit
            pos = (int(x - sprite.anchor.x), int(y - sprite.anchor.y))
            surface.blit(sprite.image, pos)

        surface.set_clip(_clip)
