from heapq import heappush, heappop
import itertools
import random

from yourgame.hex_model import HexMapModel, Cell, evenr_to_axial
from yourgame.environ import util


def build_maze_from_hex(model, lower_limit=None, upper_limit=None,
                        height=1.0,
                        raised_tile='tileRock_full.png',
                        lowered_tile='tileGrass.png',
                        num_adjacent=1,
                        start_raised=True,
                        closed_set=set()):
    def available_neighbors(coord):
        return [c for c in neighbors(coord) if coord_available(c)]

    def coord_available(coord):
        return coord not in closed_set and \
            len(closed_neighbors(coord)) <= num_adjacent

    def closed_neighbors(coord):
        return set(neighbors(coord)) - {current, current} & closed_set

    def neighbors(coord):
        return surrounding(coord)

    def raise_cell(cell):
        cell.raised = True
        cell.height = height
        cell.filename = raised_tile

    def lower_cell(cell):
        cell.raised = False
        cell.height = 0.0
        cell.filename = lowered_tile

    if start_raised:
        # Set all cells to raised
        for cell in model.cells:
            if cell[0] not in closed_set:
                raise_cell(cell[1])

    open_heap = []
    if lower_limit is None:
        lower_limit = (1, 1)

    if upper_limit is None:
        upper_limit = (model.width - 2, model.height - 2)

    start = (random.randint(lower_limit[0], upper_limit[0]),
             random.randint(lower_limit[1], upper_limit[1]))
    surrounding = util.surrounding(lower_limit, upper_limit)

    current = start
    heappush(open_heap, start)
    closed_set.add(start)
    lower_cell(model.get_cell(evenr_to_axial(start)))

    open_neighbors = available_neighbors(start)

    while open_heap or open_neighbors:
        try:
            current = random.choice(open_neighbors)
            heappush(open_heap, current)
            closed_set.add(current)
            lower_cell(model.get_cell(evenr_to_axial(current)))
        except IndexError:
            current = heappop(open_heap)
        open_neighbors = available_neighbors(current)
    return


def new_maze(map_width=10,
             map_height=10,
             tile_height=1.0,
             raised_tile='tileRock_full.png',
             lowered_tile='tileGrass.png',
             num_adjacent=1):
    model = HexMapModel()
    for q, r in itertools.product(range(map_width), range(map_height)):
        coords = evenr_to_axial((q, r))
        cell = Cell()
        cell.filename = lowered_tile
        model.add_cell(coords, cell)
    build_maze_from_hex(
        model,
        lower_limit=(1, 1),
        upper_limit=(model.width - 2,
                     model.height - 2),
        height=tile_height,
        raised_tile=raised_tile,
        lowered_tile=lowered_tile,
        num_adjacent=num_adjacent)
    return model
