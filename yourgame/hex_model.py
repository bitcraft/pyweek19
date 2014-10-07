from math import sqrt
from yourgame.euclid import Vector2, Vector3
import pygame

from collections import defaultdict
from heapq import heappush, heappop
from itertools import chain
from math import sqrt
from functools import reduce
from operator import itemgetter
import time

# even-r : 'pointy top'

__all__ = ['HexMapModel',
           'Cell',
           'evenr_to_axial',
           'pixel_to_axial',
           'sprites_to_axial',
           'collide_hex']


def pixel_to_axial(coords, size):
    x, y, z = coords
    return (1. / 3. * sqrt(3) * x - 1. / 3. * y) / size, (2. / 3.) * y / size


def axial_to_cube(coords):
    return coords[0], coords[1], -coords[0]-coords[1]


def cube_to_axial(coords):
    return coords[0], coords[1]


def axial_to_oddr(coords):
    # axial => cube
    x = coords[0]
    z = coords[1]
    #y = -x-z

    # cube => odd-r
    q = x + (z - (z & 1)) / 2
    r = z

    return q, r


def axial_to_evenr(coords):
    # axial => cube
    x = coords[0]
    z = coords[1]
    #y = -x-z

    # cube => evenr
    q = x + (z + (z & 1)) / 2
    r = z

    return q, z


def oddr_to_axial(coords):
    # odd-r => cube
    q, r = coords
    x = q - (r - (r & 1)) / 2
    z = r
    #y = -z-x

    # cube => axial
    q = x
    r = z

    return q, r


def evenr_to_axial(coords):
    # even-r => cube
    q, r = coords
    x = q - (r + (int(round(r, 0)) & 1)) / 2
    z = r
    #y = -x-z

    # cube => axial
    q = x
    r = z

    return q, r


def sprites_to_axial(coords):
    q, r = coords
    x = q - (r + (int(round(r, 0)) & 1)) / 2
    z = r
    #y = -x-z

    # cube => axial
    q = x
    r = z

    return q, r


def collide_hex(left, right, radius=None):
    """ Fast approximation of collisions between hex cells in axial space
    """
    distancesquared = dist_hex(left.position[:2], right.position[:2]) ** 2
    leftradius = left.radius
    rightradius = right.radius
    return distancesquared <= (leftradius + rightradius) ** 2


def dist_hex(cell0, cell1):
    q0, r0 = cell0
    q1, r1 = cell1
    return (abs(q0 - q1) + abs(r0 - r1) +
            abs(q0 + r0 - q1 - r1)) / 2.0


class Cell(object):

    def __init__(self):
        self.kind = None
        self.cost = 0
        self.filename = None
        self.raised = False
        self.height = 0.0


class HexMapModel(object):

    ### AXIAL
    neighbor_mat = ((
        (1, 0),  (1, -1), (0, -1),
        (-1, 0), (-1, 1), (0, 1)
    ))

    def __init__(self):
        self._data = dict()
        self._width = None
        self._height = None
        self._dirty = False

    def get_cell(self, coords):
        return self._data.get(tuple(coords), None)

    def get_nearest_cell(self, coords):
        # expects coords in fractional axial coordinates
        coords = cube_to_axial([int(round(i, 0)) for i in axial_to_cube(coords)])
        return self.get_cell(coords)

    def add_cell(self, coords, cell):
        coords = tuple(coords)
        assert(len(coords) == 2)
        self._data[coords] = cell
        self._trigger_bounds_update()

    def remove_cell(self, coords):
        del self._data[coords]
        self._trigger_bounds_update()

    def _trigger_bounds_update(self):
        self._width = None
        self._height = None

    def _calc_bounds(self):
        x_list = list()
        y_list = list()
        for cell in self._data.keys():
            x, y = axial_to_evenr(cell)
            x_list.append(x)
            y_list.append(y)

        if len(x_list):
            self._width = int(max(x_list) - min(x_list) + 1)
        else:
            self._width = 0

        if len(y_list):
            self._height = int(max(y_list) - min(y_list) + 1)
        else:
            self._height = 0

    @property
    def width(self):
        if self._width is None:
            self._calc_bounds()
        return self._width

    @property
    def height(self):
        if self._height is None:
            self._calc_bounds()
        return self._height

    @property
    def size(self):
        if self._height is None or self._width is None:
            self._calc_bounds()
        return self._width, self._height

    @property
    def cells(self):
        return self._data.items()

    @staticmethod
    def get_neighbors(cell):
        for other in HexMapModel.neighbor_mat:
            yield (other[0] + cell[0], other[1], cell[1])

    @staticmethod
    def get_facing(cell, facing):
        return (cell[0] + HexMapModel.neighbor_mat[facing],
                cell[1] + HexMapModel.neighbor_mat[facing])

    def walls(self):
        walls = list()
        for pos, cell in self._data.items():
            if cell.raised:
                sprite = pygame.sprite.Sprite()
                sprite.position = Vector2(*pos)
                sprite.radius = .25
                walls.append(sprite)
        return walls

    @staticmethod
    def dist(cell0, cell1):
        q0, r0 = cell0
        q1, r1 = cell1
        return (abs(q0 - q1) + abs(r0 - r1) +
                abs(q0 + r0 - q1 - r1)) / 2.0

    def pathfind_evenr(self, current, end, blacklist=set(),
                       impassable=set()):
        current = evenr_to_axial(current)
        end = evenr_to_axial(end)
        blacklist = {evenr_to_axial(coord) for coord in blacklist}
        return self.pathfind(current, end, blacklist, impassable)

    def pathfind(self, current, end, blacklist=set(),
                 impassable=set()):
        blacklist.update({coord for coord in self._data if self._data[coord].raised})

        def cell_available(cell):
            return coord_available(cell[1])

        def coord_available(coord):
            return coord not in closed_set \
                and coord not in blacklist \
                and self.get_cell(coord).kind not in impassable

        def clip(vector, lowest, highest):
            return type(vector)(map(min, map(max, vector, lowest), highest))

        def surrounding_clip(coord, limit):
            x, y = coord
            return (clip(i, (0, 0), limit) for i in
                    ((x - 1, y - 1), (x - 1, y), (x - 1, y + 1), (x, y - 1),
                     (x, y + 1), (x + 1, y)))

        def surrounding_noclip(coord, limit):
            x, y = coord
            return ((x - 1, y - 1), (x - 1, y), (x - 1, y + 1), (x, y - 1),
                   (x, y + 1), (x + 1, y))

        def retrace_path(c):
            path = [c]
            while parent.get(c, None) is not None:
                c = parent[c]
                path.append(c)
            return reversed(path)

        start_time = time.time()
        parent = {}
        open_heap = []
        open_set = set()
        closed_set = set()
        limit = self.width - 1, self.height - 1
        surrounding = surrounding_clip
        current = current[0], current[1]
        open_set.add(current)
        open_heap.append(current)
        while open_set:
            if time.time() - start_time > .0125:
                try:
                    return retrace_path(current), False
                except:
                    return (), True

            current = heappop(open_heap)

            if current == end:
                return retrace_path(current), True

            open_set.remove(current)
            closed_set.add(current)
            cells = filter(cell_available,
                           ((self.dist(coord, end)+self.get_cell(coord).cost, coord)
                            for coord in surrounding(current, limit)))
            # Push the highest costing tiles first, so we'll check them last
            # Should keep working when there's a dead end
            for cell in sorted(cells, key=itemgetter(0), reverse=True):
                parent[cell[1]] = current
                if cell[1] not in open_set:
                    open_set.add(cell[1])
                    heappush(open_heap, cell[1])

        return (), True
