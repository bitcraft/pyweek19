from math import sqrt
from itertools import chain
from collections import defaultdict

from yourgame.euclid import Vector3

# even-r : 'pointy top'

__all__ = ['HexMapModel',
           'Cell',
           'evenr_to_axial',
           'pixel_to_axial',
           'sprites_to_axial']


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


class Cell(object):

    def __init__(self):
        self.kind = None
        self.cost = None
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
            x, y = axial_to_oddr(cell)
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
        return HexMapModel.neighbor_mat + cell

    @staticmethod
    def get_facing(cell, facing):
        return (cell[0] + HexMapModel.neighbor_mat[facing],
                cell[1] + HexMapModel.neighbor_mat[facing])

    @staticmethod
    def dist(cell0, cell1):
        q0, r0 = cell0
        q1, r1 = cell1
        return (abs(q0 - q1) + abs(r0 - r1) +
                abs(q0 + r0 - q1 - r1)) / 2.0

