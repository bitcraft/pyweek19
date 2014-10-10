from heapq import heappush, heappop
from math import sqrt, ceil
from operator import itemgetter
import random
import json
import codecs
import time
from zort.environ import util


# even-r : 'pointy top'

__all__ = ['HexMapModel',
           'Cell',
           'evenr_to_axial',
           'axial_to_evenr',
           'pixel_to_axial',
           'sprites_to_axial',
           'axial_to_sprites',
           'sprites_to_hex',
           'collide_hex',
           'hex_round']


ratio_13 = 1./3.
ratio_23 = 2./3.
ratio_32 = 3./2
sqrt_3 = sqrt(3)


# round axial coordinates
def hex_round(coords):
    x, y, z = axial_to_cube(coords)
    rx, ry, rz = [round(i, 0) for i in (x, y, z)]
    dx = abs(rx - x)
    dy = abs(ry - y)
    dz = abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry-rz
    elif dy > dz:
        ry = -rx-rz
    else:
        rz = -rx-ry
    assert (rx + ry + rz == 0)
    return cube_to_axial((rx, ry, rz))


def axial_to_pixel(coords, size):
    return size * sqrt_3 * (coords[0] - 0.5 * (coords[1] & 1)), \
           size * 3/2 * coords[1]


def pixel_to_axial(coords, size):
    x, y = [float(i) for i in coords[:2]]
    size = float(size)
    return (ratio_13 * sqrt_3 * x - ratio_13 * y) / size, ratio_32 * y / size


def axial_to_cube(coords):
    return coords[0], coords[1], -coords[0] - coords[1]


def cube_to_axial(coords):
    return coords[0], coords[1]


def axial_to_oddr(coords):
    # axial => cube
    x = coords[0]
    z = coords[1]
    # y = -x-z

    # cube => odd-r
    q = x + (z - (z & 1)) / 2
    r = z

    return q, r


def axial_to_evenr(coords):
    # axial => cube
    x = coords[0]
    z = coords[1]
    # y = -x-z

    # cube => evenr
    q = x + (z + (z & 1)) / 2
    #r = z

    return q, z


def oddr_to_axial(coords):
    # odd-r => cube
    q, r = coords
    qq = q - (r - (r & 1)) / 2
    rr = r
    return qq, rr


def evenr_to_axial(coords):
    # even-r => cube
    q, r = coords
    qq = q - (r + (r & 1)) / 2
    return qq, r


# special purpose function for sprites only
def sprites_to_axial(coords):
    x, y = coords[:2]
    return int(ratio_13 * sqrt_3 * x - ratio_13 * y), int(ratio_23 * y)


# special purpose function for sprites only
def axial_to_sprites(coords):
    q, r = coords[:2]
    return sqrt_3 * (q + r/2.), ratio_32 * r


# special purpose function for sprites only
def sprites_to_hex(coords):
    return hex_round(sprites_to_axial(coords))


def cube_to_pixel(coords, radius):
    cx, cy, cz = coords
    y = ratio_32 * radius * cz
    #b = 2/3 * y / s
    #x = sqrt_3 * radius * (cz / 2. + cx)
    x = - sqrt_3 * radius * (cz / 2. + cy)
    #r = (sqrt(3)/3 * x - y/3 ) / s
    #g = -(sqrt(3)/3 * x + y/3 ) / s
    return x, y


def collide_hex(left, right, left_radius=1.0, right_radius=1.0):
    """ Fast approximation of collisions between circles in axial space
    """
    dx, dy = dist_axial2(left, right)
    rr = left_radius + right_radius
    return (dx * dx) + (dy * dy) < rr * rr


# slower collision test for testing level geometry
def collide_hex2(cell0, cell1, left_radius=1.0, right_radius=1.0):
    x0, y0 = cube_to_pixel(axial_to_cube(cell0), 100.)
    x1, y1 = cube_to_pixel(axial_to_cube(cell1), 100.)
    dx = x1 - x0
    dy = y1 - y0
    rr = (left_radius * 100.) + (right_radius * 100.)
    return (dx * dx) + (dy * dy) < rr * rr


# returns x and y
def dist_axial2(cell0, cell1):
    q0, r0 = cell0[:2]
    q1, r1 = cell1[:2]
    return abs(q0 - q1) + abs(r0 - r1), abs(q0 + r0 - q1 - r1) / 2


# returns x + y
def dist_axial(cell0, cell1):
    q0, r0 = cell0[:2]
    q1, r1 = cell1[:2]
    return (abs(q0 - q1) + abs(r0 - r1) +
            abs(q0 + r0 - q1 - r1)) / 2.0


class Cell(object):
    def __init__(self, **kwargs):
        self.cost = int(kwargs.get("cost", 0))
        self.filename = kwargs.get("filename", None)
        self.raised = kwargs.get("raised", False)
        self.height = float(kwargs.get("height", 0.0))

    def to_json(self):
        return {
            "cost": self.cost,
            "filename": self.filename,
            "raised": self.raised,
            "height": self.height
        }


class HexMapModel(object):
    def __init__(self):
        self._data = dict()
        self._width = None
        self._height = None
        self._dirty = False

    def surrounding(self, coords):
        # this is some gigantic hack
        #s = util.surrounding_clip(coord, (0, 0), (self.width, self.height))
        s = util.surrounding_clip(coords, (0, 0), (self.width, self.height))
        for coords in s:
            coords = [int(i) for i in coords]
            coords = [int(i) for i in evenr_to_axial(coords)]
            yield tuple(coords)

    def collidecircle(self, coords, radius):
        """test if circle overlaps level geometry above layer 0 only

        :param coords: axial coords
        :param radius: axial coords
        :return: list of coords
        """
        retval = list()
        round_coords = [int(i) for i in hex_round(coords)]
        neighbors = list(self.surrounding(round_coords))
        for n in neighbors:
            neigh = tuple([int(i) for i in n])
            cell = self._data.get(neigh, None)
            if not cell:
                continue

            if cell.height <= 0:
                continue

            if collide_hex2(coords, neigh, radius, .75):
                retval.append(neigh)
        #print retval
        return retval

    def _make_file_data(self):
        return {
            "width": self._width,
            "height": self._height,
            "data": {str(key): value.to_json() for key, value in
                     self._data.items()}
        }

    def save_to_disk(self, path):
        with codecs.open(path, "wb", encoding="utf-8") as fob:
            data = self._make_file_data()
            json.dump(data, fob, indent=2)

    def load_from_disk(self, path):
        with codecs.open(path, "rb", encoding="utf-8") as fob:
            data = json.load(fob)
            self._width = data["width"]
            self._height = data["height"]
            self._data = dict()
            for key, cell_data in data["data"].items():
                self._data[eval(key)] = Cell(**cell_data)

    def get_cell(self, coords):
        return self._data.get(tuple(coords), None)

    def get_nearest_cell(self, coords):
        # expects coords in fractional axial coordinates
        return hex_round(coords)

    def add_cell(self, coords, cell):
        coords = tuple(coords)
        assert (len(coords) == 2)
        coords = tuple(int(i) for i in coords)
        self._data[coords] = cell
        self._trigger_bounds_update()

    def remove_cell(self, coords):
        del self._data[coords]
        self._trigger_bounds_update()

    def _trigger_bounds_update(self):
        self._width = None
        self._height = None
        self.quadtree = None

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
    def get_facing(cell, facing):
        return (cell[0] + util.neighbor_mat[facing],
                cell[1] + util.neighbor_mat[facing])

    @staticmethod
    def dist(cell0, cell1):
        q0, r0 = cell0
        q1, r1 = cell1
        return (abs(q0 - q1) + abs(r0 - r1) +
                abs(q0 + r0 - q1 - r1)) / 2.0

    def neighboring_radius(self, center, radius, blacklist=set()):
        center = {center, center}
        neighbors = center
        for i in range(radius):
            tmp = set()
            for n in neighbors:
                tmp.update(set(self.surrounding(n)))
            neighbors.update(tmp)

        neighbors.difference_update(blacklist-center)
        #neighbors.update({center, center})

        return neighbors

    def pathfind_evenr(self, current, end, blacklist=set()):
        current = evenr_to_axial(current)
        end = evenr_to_axial(end)
        blacklist = {evenr_to_axial(coord) for coord in blacklist}
        return self.pathfind(current, end, blacklist)

    def pathfind_ramble(self, current, home, radius, blacklist=set()):
        neighbors = self.neighboring_radius(home, radius, blacklist)

        blacklist.update(
            {coord for coord in self._data})
        print(len(blacklist), blacklist)
        blacklist.difference_update(neighbors)
        print(len(blacklist), blacklist)
        end = random.choice(list(neighbors)) \
            if len(neighbors) > 1 else neighbors
        return self.pathfind(current, end, blacklist)

    def pathfind(self, current, end, blacklist=set()):
        blacklist.update(
            {coord
             for coord in self._data if self._data[coord].raised})
        print(len(blacklist), blacklist)

        def cell_available(cell):
            return coord_available(cell[1])

        def coord_available(coord):
            print(coord, coord in closed_set, coord in blacklist)

            return coord not in closed_set and coord not in blacklist

        def retrace_path(c):
            path = [c]
            while parent.get(c, None) is not None:
                c = parent[c]
                path.append(c)
            return path

        start_time = time.time()
        parent = {}
        open_heap = []
        open_set = set()
        closed_set = set()
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
            print(closed_set)
            cells = filter(
                cell_available,
                ((self.dist(coord, end) + self.get_cell(coord).cost, coord)
                 for coord in self.surrounding(current)))
            # Push the highest costing tiles first, so we'll check them last
            # Should keep working when there's a dead end
            for cell in sorted(cells, key=itemgetter(0), reverse=True):
                parent[cell[1]] = current
                if cell[1] not in open_set:
                    open_set.add(cell[1])
                    heappush(open_heap, cell[1])
        print()
        return (), True
