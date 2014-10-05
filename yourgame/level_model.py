from array import array
from math import hypot
from itertools import product
from collections import defaultdict, namedtuple
from heapq import heappush, heappop
import math
import time


__all__ = ['LevelModel']

MapTile = namedtuple("MapTile", "")


def distance2((ax, ay), (bx, by)):
    return hypot((ax - bx), (ay - by))


class LevelModel(object):
    def __init__(self, size, seed=0):
        self.height, self.width = size
        self.data = list()
        self.renderer = None
        self.totals = defaultdict(int)
        self.scan_cache = dict()
        self.data = tuple([seed] * self.width for i in range(self.height))

    def set_renderer(self, r):
        self.renderer = r

    def set_tile(self, (x, y), value):
        self.data[y][x] = value
        if self.renderer:
            self.renderer.mark_changed((x, y))

    def get_tile(self, (x, y)):
        return self.data[y][x]

    def tiles_of_type(self, types):
        assert isinstance(types, (list, tuple, set))
        for y, row in enumerate(self.data):
            for x, value in enumerate(row):
                if isinstance(value, types):
                    yield (x, y), type

    def nearest_tiles(self, origin, types, blacklist=list()):
        """ return a heap of tiles closest to a origin """
        origin = origin[0], origin[1]
        dx, dy = origin[0] - int(origin[0]), origin[1] - int(origin[1])
        heap = list()

        for (tx, ty), tile in self.tiles_of_type(types):
            if (tx, ty) not in blacklist:
                p = (tx + dx, ty + dy)
                heappush(heap, (distance2(p, origin), p))

        return heap

    def pathfind_type(self, current, targets, blacklist, impassable=None):
        """ pathfind to a tile type """

        possible = self.nearest_tiles(current, targets, blacklist)
        if not possible:
            return list(), True

        path = list()
        complete = True
        start_time = time.time()
        while possible:
            if time.time() - start_time > .05:
                return path, complete
            position = heappop(possible)[1]
            path, complete = self.pathfind(current, position, list(),
                                           impassable)
            if path:
                return path, complete

        return list(), True

    def pathfind(self, current, end, blacklist, impassable=None):
        """ modified: http://stackoverflow.com/questions/4159331/python-speed-up-an-a-star-pathfinding-algorithm """

        def clip(vector, lowest, highest):
            return type(vector)(map(min, map(max, vector, lowest), highest))

        def surrounding_clip((x, y), limit):
            return [clip(i, (0, 0), limit) for i in
                    ((x - 1, y - 1), (x - 1, y), (x - 1, y + 1), (x, y - 1),
                     (x, y + 1), (x + 1, y - 1), (x + 1, y), (x + 1, y + 1))]

        def surrounding_noclip((x, y), limit):
            return (x - 1, y - 1), (x - 1, y), (x - 1, y + 1), (x, y - 1), \
                   (x, y + 1), (x + 1, y - 1), (x + 1, y), (x + 1, y + 1)

        def retrace_path(c):
            path = [c]
            while parent.get(c, None) is not None:
                c = parent[c]
                path.append(c)
            return path

        start_time = time.time()
        parent = dict()
        open_heap = list()
        open_set = set()
        closed_set = set()
        limit = self.width - 1, self.height - 1
        surrounding = surrounding_clip
        current = current[0], current[1]
        open_set.add(current)
        open_heap.append((0, current))
        while open_set:
            if time.time() - start_time > .0125:
                try:
                    return retrace_path(current), False
                except:
                    return list(), True

            current = heappop(open_heap)[1]

            if map(int, current) == map(int, end):
                return retrace_path(current), True

            open_set.remove(current)
            closed_set.add(current)
            for tile in surrounding(current, limit):
                try:
                    if self.get_tile(map(int, tile))[0] == impassable:
                        continue
                except IndexError:
                    pass

                if tile not in closed_set:
                    parent[tile] = current
                    if tile not in open_set:
                        open_set.add(tile)
                        heappush(open_heap, (distance2(tile, end), tile))

        return list(), True
