import pygame
import pygame.gfxdraw
from math import sin, cos, pi, sqrt

from yourgame import hex_model


__all__ = ['HexMapView']


def get_draw_hex(size):
    def draw_hex(surface, coords, border_color, fill_color):
        new_points = [(coords[0] + x, coords[1] + y) for x, y in points]
        fill(surface, new_points, fill_color)
        outline(surface, new_points, border_color)

    points = list()
    temp = 2 * pi / 6.
    for i in range(6):
        angle = temp * (i + .5)
        points.append((size * cos(angle), size * sin(angle)))

    outline = pygame.gfxdraw.aapolygon
    fill = pygame.gfxdraw.filled_polygon
    return draw_hex


class HexMapView(pygame.sprite.Group):
    def __init__(self, data, radius, surface):
        super(HexMapView, self).__init__()
        self.data = data
        self.hex_radius = radius
        self.graph = hex_model.Graph()
        self._rect = None
        self._old_hovered = None
        self._hovered = None
        self._selected = list()
        self._hw = None
        self._hh = None

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

    def point_from_surface(self, point):
        if self._rect is None:
            return None
        return point[0] - self._hw, point[1] - self._hh

    def point_from_local(self, point):
        if self._rect is None:
            raise Exception
        return point[0] + self._hw, point[1] + self._hh

    def draw(self, surface):
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
        draw_hex = get_draw_hex(self.hex_radius)

        tile_h = self.hex_radius * 2
        tile_w = (sqrt(3) / 2) * tile_h
        mw = (self.data.width - 1) * tile_w
        mh = (self.data.height - 1) * tile_h * 3 / 4
        hw = (w / 2) - (mw / 2)
        hh = (h / 2) - (mh / 2)
        self._hw = hw
        self._hh = hh

        nodes = list(self.graph.nodes())
        position_mapping = dict()

        # render cells
        _clip = surface.get_clip()
        surface.set_clip(rect)
        surface.lock()
        for (q, r), cell in self.data.cells:
            pos = size_sqrt3 * (q + r / 2.) + hw, size_ratio * r + hh

            if cell in self._selected:
                fill = select_color

            elif cell is self._hovered:
                fill = hover_color

            else:
                fill = fill_color

            if cell in nodes:
                position_mapping[cell] = pos
            draw_hex(surface, pos, border_color, fill)

        # show the graph
        for edge in self.graph.edges():
            points = [position_mapping[i] for i in edge]
            pygame.draw.aalines(surface, line_color, 0, points, 1)

        surface.unlock()
        surface.set_clip(_clip)
