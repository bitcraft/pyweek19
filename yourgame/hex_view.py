import time
import pygame
import pygame.gfxdraw
from pygame.transform import smoothscale
from math import sin, cos, pi, sqrt, radians
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
        x, y, z = mat * Point3(coords[0], coords[1] + radius, 0)
        surface.blit(tile_dict[filename], (int(x), int(y)))

    height = radius * 2
    width = sqrt(3) / 2 * height
    size = (int(width), int(height))
    tile_dict = dict()
    for filename, image in resources.tiles.items():
        if filename.startswith('tile'):
            image = smoothscale(image, size)
        tile_dict[filename] = image
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
        self.tilt = 0
        self.reproject(self.tilt)
        self.set_radius(radius)

    def reproject(self, tilt):
        self.prj = Matrix4()
        self.prj.rotate_axis(radians(tilt), Vector3(1, 0, 0))
        self.inv_prj = self.prj.inverse()

    def set_radius(self, radius):
        self.hex_radius = radius
        self._hex_draw = get_hex_draw(self.prj, radius)
        self._hex_tile = get_hex_tile(self.prj, radius)

    def select_cell(self, cell):
        self._selected.append(cell)
        self._handle_selected()

    def _handle_selected(self):
        if len(self._selected) > 2:
            prev_cell = self._selected[0]
            for cell in self._selected[1:]:
                self.graph.add_edge(prev_cell, cell)
            self._selected = list()

    def highlight_cell(self, cell):
        self._old_hovered = self._hovered
        self._hovered = cell

    def project(self, pos):
        ## convenience
        x, y, z = self.prj * Vector3(*pos)
        return x, y

    def point_from_surface(self, point):
        ## return a point in map space from the surface
        if self._rect is None:
            return None

        point = Vector3(*point) + (self._rect.left, self._rect.top, 0)
        v = vec(pixel_to_axial(point, self.hex_radius))

        x, y, z = self.inv_prj * v
        return x, y

    def point_from_local(self, point):
        if self._rect is None:
            return None

        point = Vector3(*point) - (self._rect.left, self._rect.top, 0)
        return point[0] + self._hw, point[1] + self._hh

    def draw(self, surface):
        self.reproject(self.tilt)
        print self.tilt
        self.draw_tiles(surface)
        self.draw_grid(surface)

    def draw_tiles(self, surface):
        self._rect = surface.get_clip()
        rect = self._rect
        size_sqrt3 = self.hex_radius * sqrt(3)
        size_ratio = self.hex_radius * (3. / 2.)
        w, h = rect.size
        draw_tile = self._hex_tile

        tile_h = self.hex_radius * 2
        tile_w = (sqrt(3) / 2) * tile_h
        mw = (self.data.width - 1) * tile_w
        mh = (self.data.height - 1) * tile_h * 3 / 4
        hw = (w / 2) - (mw / 2)
        hh = (h / 2) - (mh / 2)
        self._hw = hw
        self._hh = hh

        # render cells
        _clip = surface.get_clip()
        surface.set_clip(rect)
        for q, r in product(range(10), range(10)):
            q, r = evenr_to_axial((r, q))
            cell = self.data.get_cell((q, r))
            pos = size_sqrt3 * (q + r / 2.) + hw, size_ratio * r + hh
            pos = self.prj * Vector3(*pos)

            draw_tile(surface, cell.filename, pos)

        surface.set_clip(_clip)

    def draw_grid(self, surface):
        self._rect = surface.get_clip()
        rect = self._rect
        size_sqrt3 = self.hex_radius * sqrt(3)
        size_ratio = self.hex_radius * (3. / 2.)
        border_color = 61, 42, 42
        line_color = 61, 42, 42
        fill_color = 161, 92, 120
        hover_color = 192, 184, 190
        select_color = 195, 177, 142
        w, h = rect.size
        draw_hex = self._hex_draw

        tile_h = self.hex_radius * 2
        tile_w = (sqrt(3) / 2) * tile_h
        mw = (self.data.width - 1) * tile_w
        mh = (self.data.height - 1) * tile_h * 3 / 4
        hw = (w / 2) - (mw / 2)
        hh = (h / 2) - (mh / 2)
        self._hw = hw
        self._hh = hh

        # render cells
        _clip = surface.get_clip()
        surface.set_clip(rect)
        surface.lock()
        for (q, r), cell in self.data.cells:
            pos = size_sqrt3 * (q + r / 2.) + hw, size_ratio * r + hh
            pos = self.prj * Vector3(*pos)

            if cell in self._selected:
                fill = select_color

            elif cell is self._hovered:
                fill = hover_color

            else:
                fill = None

            draw_hex(surface, pos, border_color, fill)

        surface.unlock()
        surface.set_clip(_clip)
