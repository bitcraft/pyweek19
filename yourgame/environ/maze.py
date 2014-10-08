from heapq import heappush, heappop
import random

from yourgame.hex_model import evenr_to_axial, clip


def surrounding_clip(coord, lower, upper):
    x, y = coord
    print(lower, upper)
    return (clip(i, lower, upper) for i in
            ((x - 1, y - 1), (x - 1, y), (x - 1, y + 1), (x, y - 1),
           (x, y + 1), (x + 1, y)))


def build_maze_from_hex(model, lower_limit=None, upper_limit=None,
                        height=1.0,
                        raised_tile='tileRock_full.png',
                        lowered_tile='tileGrass.png',
                        num_adjacent=1):
    def coord_available(coord):
        cell = model.get_cell(evenr_to_axial(coord))
        return cell.raised and len(open_neighbors(coord)) <= num_adjacent

    def open_neighbors(coord):
        neighbors = set(c for c in
                        surrounding_clip(coord, lower_limit, upper_limit))
        neighbors.discard(current)
        return neighbors & closed_set

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
        lower_limit = (0, 0)

    if upper_limit is None:
        upper_limit = (model.width - 1, model.height - 1)

    start = (random.randint(0, model.width - 1),
             random.randint(0, model.height - 1))
    current = start
    heappush(open_heap, start)
    lower_cell(model.get_cell(evenr_to_axial(start)))

    while open_heap:
        open_coords = set(
            filter(coord_available,
                   (coord for coord in
                    surrounding_clip(current, lower_limit, upper_limit))))
        if len(open_coords):
            current = open_coords.pop()
            heappush(open_heap, current)
            closed_set.add(current)
            lower_cell(model.get_cell(evenr_to_axial(current)))
        else:
            current = heappop(open_heap)
            closed_set.add(current)

    return