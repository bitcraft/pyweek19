from heapq import heappush, heappop
import random

from yourgame.hex_model import evenr_to_axial, clip


def surrounding_clip(coord, lower, upper):
    x, y = coord
    return (clip(i, lower, upper) for i in
            ((x - 1, y - 1), (x - 1, y), (x - 1, y + 1), (x, y - 1),
           (x, y + 1), (x + 1, y)))


def build_maze_from_hex(model, lower_limit=None, upper_limit=None,
                        height=1.0,
                        raised_tile='tileRock_full.png',
                        lowered_tile='tileGrass.png',
                        num_adjacent=1):
    def coord_available(coord):
        return coord not in closed_set and len(closed_neighbors(coord)) <= num_adjacent

    def closed_neighbors(coord):
        return set(neighbors(coord)) - {current} & closed_set

    def neighbors(coord):
        return (c for c in surrounding_clip(coord, lower_limit, upper_limit))

    def raise_cell(cell):
        cell.raised = True
        cell.height = height
        cell.filename = raised_tile

    def lower_cell(cell):
        cell.raised = False
        cell.height = 0.0
        cell.filename = lowered_tile

    # Set all cells to raised
    for cell in model._data.items():
        raise_cell(cell[1])

    open_heap = []
    closed_set = set()
    if lower_limit is None:
        lower_limit = (1, 1)

    if upper_limit is None:
        upper_limit = (model.width - 2, model.height - 2)

    start = (random.randint(lower_limit[0], upper_limit[0]),
             random.randint(lower_limit[1], upper_limit[1]))
    current = start
    heappush(open_heap, start)
    closed_set.add(start)
    lower_cell(model.get_cell(evenr_to_axial(start)))

    open_neighbors = [coord for coord in neighbors(start) if coord_available(coord)]

    while open_heap or open_neighbors:
        try:
            current = random.choice(open_neighbors)
            heappush(open_heap, current)
            closed_set.add(current)
            lower_cell(model.get_cell(evenr_to_axial(current)))
        except IndexError:
            current = heappop(open_heap)
        open_neighbors = [coord for coord in neighbors(current) if coord_available(coord)]
    return