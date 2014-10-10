from math import sin, cos, pi, sqrt, ceil
from itertools import product

import pygame
import pygame.gfxdraw
from pygame.transform import smoothscale

from yourgame.euclid import Vector2, Vector3
from yourgame import resources
from yourgame.hex_model import *
from yourgame import quadtree


__all__ = ['HexMapView']


class UpperLayerRect():
    def __init__(self, surface, rect, layer):
        self.rect = rect
        self.surface = surface
        self.layer = layer
        self.left = rect.left
        self.right = rect.right
        self.top = rect.top
        self.bottom = rect.bottom


class HexMapView(pygame.sprite.LayeredUpdates):
    border_color = 61, 55, 42, 64
    line_color = 61, 42, 42
    fill_color = 161, 92, 120
    hover_color = 192, 184, 190, 128
    select_color = 195, 177, 142

    def __init__(self, scene, data, radius):
        super(HexMapView, self).__init__(default_layer=1)
        self.scene = scene
        self.data = data
        self.hex_radius = radius
        self.tilt = .84
        self.size_ratio = 1.3

        self.default_cell = Cell()
        self.default_cell.filename = 'tileGrass.png'

        # this must be set to true when tile size or tilt changes
        self.needs_cache = None

        # set this to True to trigger a map redraw
        self.needs_refresh = None

        self.overlap_limit = None
        self.rect = None
        self.lostsprites = list()
        self.map_rect = None
        self._old_hovered = None
        self._hovered = None
        self._selected = list()
        self._hex_draw = None
        self._hex_tile = None
        self.project = None
        self.map_buffer = None
        self.voff = None
        self.pixel_offset = None
        self.layer_quadtree = None
        self.set_radius(radius)
        self.spritedict["hover"] = None

        self.background = resources.images['backdrop']

    def get_hex_draw(self):
        def draw_hex(surface, coords, border_color, fill_color):
            new_points = [(coords[0] + x, coords[1] + y) for x, y in points]
            if fill_color:
                fill(surface, new_points, fill_color)
            outline(surface, new_points, border_color)
            x1 = new_points[2][0]
            y1 = new_points[4][1]
            w = new_points[0][0] - x1
            h = new_points[1][1] - y1
            return pygame.Rect(x1, y1, w, h).inflate(4, 4)

        points = list()
        temp = 2 * pi / 6.
        for i in range(6):
            angle = temp * (i + .5)
            x, y = self.hex_radius * cos(angle), self.hex_radius * sin(angle)
            y *= self.tilt
            points.append((x, y))
        outline = pygame.gfxdraw.aapolygon
        fill = pygame.gfxdraw.filled_polygon
        return draw_hex

    def get_hex_tile(self):
        def draw_tile(blit, cell, coords):
            x, y = coords - (half_width, half_height)
            tile = tile_dict[cell.filename]
            return blit(tile, (int(x), int(y)))

        tile_dict = dict()
        ph = self.hex_radius * 2
        pw = (sqrt(3) / 2 * ph)
        ph *= self.tilt
        half_width = int(pw / 2.)
        half_height = int(ph / 2.)
        pw += 1

        for filename, image in resources.tiles.items():
            if filename.startswith('tile'):
                iw, ih = image.get_size()
                height = pw * (float(ih) / iw)
                image = smoothscale(image, (int(pw), int(height)))
                tile_dict[filename] = image

        return draw_tile

    def get_projection(self):
        def project(i, cell=None):
            coords = Vector2(size_sqrt3 * (i[0] + i[1] / 2.), size_ratio * i[1])
            coords += screen_offset
            return coords

        # cache of the expensive axial => cart transform
        cache = dict()
        size_sqrt3 = self.hex_radius * sqrt(3)
        size_ratio = self.hex_radius * 3. / 2.

        ph = self.hex_radius * 2
        pw = (sqrt(3) / 2 * ph)
        ph *= self.tilt

        size_ratio = self.hex_radius * pw / ph * self.size_ratio
        self.voff = size_ratio

        rw, rh = self.rect.size
        mw = pw * self.data.size[0] * 1.05
        mh = ph * self.data.size[1] * 3. / 4. * 1.15
        hw = int((rw / 2.) - (mw / 2.))
        hh = int((rh / 2.) - (mh / 2.))
        hh *= 1.6

        screen_offset = Vector2(hw + pw, hh + ph / 2.)
        map_rect = pygame.Rect((hw, hh), (mw, mh))

        self.map_rect = map_rect
        self.pixel_offset = screen_offset

        def cached_project(i, cell=None, use_cache=False):
            if use_cache:
                try:
                    return cache[i]
                except KeyError:
                    coords = project(i, cell)
                    cache[i] = coords
                    return coords
            else:
                return project(i, cell)

        return cached_project

    def set_radius(self, radius):
        self.hex_radius = radius
        self.overlap_limit = int(radius * .25)
        self.needs_cache = True

    def select_cell(self, cell):
        self._selected.append(cell)

    def highlight_cell(self, cell):
        if self._old_hovered is not cell:
            self._old_hovered = self._hovered
            self._hovered = cell

    def cell_from_surface(self, point):
        if self.rect is None:
            return None

        x, y = point
        x -= self.pixel_offset.x
        y -= self.pixel_offset.y
        y *= 1.1

        point = Vector3(x, y, 0)
        x, y, z = Vector3(*pixel_to_axial(point, self.hex_radius))
        return self.data.get_cell((x, y))

    def clear(self, surface, bgk=None):
        if self.map_buffer is None:
            return
        blit = surface.blit
        _buffer = self.map_buffer
        spritedict = self.spritedict
        [blit(_buffer, r, r) for r in self.lostsprites]
        for key, value in spritedict.items():
            if value:
                try:
                    if key.dirty:
                        blit(_buffer, value, value)
                except AttributeError:
                    pass

    def remove_internal(self, sprite):
        super(HexMapView, self).remove_internal(sprite)
        try:
            del self.dirtydict[sprite]
        except:
            pass

    def draw(self, surface):
        if self.needs_cache:
            buffer_size = surface.get_size()
            self.map_buffer = pygame.Surface(buffer_size, pygame.SRCALPHA)
            self.map_buffer.blit(self.background, (0, 0))
            self.rect = self.map_buffer.get_rect()
            self.project = self.get_projection()
            self._hex_draw = self.get_hex_draw()
            self._hex_tile = self.get_hex_tile()
            self.needs_cache = False
            self.needs_refresh = True

        self.rect = self.map_buffer.get_rect()
        dirty = self.lostsprites
        project = self.project
        draw_tile = self._hex_tile
        draw_hex = self._hex_draw
        get_cell = self.data.get_cell
        surface_blit = surface.blit
        surface_rect = surface.get_rect()
        buffer_blit = self.map_buffer.blit
        dirty_append = dirty.append
        spritedict = self.spritedict

        self.lostsprites = list()
        refreshed = False

        # draw the cell tiles, a thread will blit the tiles in the background
        # this is rendering the background and all hex tiles
        if self.needs_refresh:
            for sprite in spritedict.keys():
                try:
                    sprite.dirty = 1
                except:
                    pass

            upper_buffer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            buffer2_blit = upper_buffer.blit
            upper_cells = list()

            # get in draw order
            ww, hh = self.data.size
            for rr, qq in product(range(hh), range(ww)):
                pos = evenr_to_axial((qq, rr))
                cell = get_cell(pos)
                pos = Vector2(*project(pos, cell))

                # draw tall columns
                if cell.height > 0:
                    rects = list()

                    draw_tile(buffer_blit, self.default_cell, pos)
                    for i in range(int(ceil(cell.height))):
                        # pos.y -= self.hex_radius / 2 * float(cell.height)
                        pos.y -= self.voff / 2
                        draw_tile(buffer_blit, cell, pos)
                        rect = draw_tile(buffer2_blit, cell, pos)
                        rects.append(rect)

                    rect = rects[0].unionall(rects[:1])
                    surf = pygame.Surface(rect.size, pygame.SRCALPHA)
                    surf.blit(upper_buffer, (0, 0), rect)
                    upper_cells.append(UpperLayerRect(surf, rect, 1))
                else:
                    draw_tile(buffer_blit, cell, pos)

            self.layer_quadtree = quadtree.FastQuadTree(upper_cells, 4)
            rect = surface_blit(self.map_buffer, self.rect)
            dirty_append(rect)
            self.needs_refresh = False
            refreshed = True

        # draw cell lines (outlines and highlights) to the surface
        surface.lock()
        for pos, cell in self.data.cells:
            if cell in self._selected:
                fill = self.select_color
            elif cell is self._hovered:
                fill = self.hover_color
            else:
                continue
            old_rect = spritedict.get("hover", None)
            pos = Vector3(*project(pos, cell))
            rect = draw_hex(surface, pos, self.border_color, fill)
            if not refreshed:
                if old_rect:
                    if rect.colliderect(rect):
                        dirty_append(rect.union(old_rect))
                    else:
                        dirty_append(rect)
                        dirty_append(rect)
                else:
                    dirty_append(rect)
                spritedict["hover"] = rect
        surface.unlock()

        overlap_limit = self.overlap_limit
        for sprite in [s for s in self.sprites() if s.visible & s.dirty]:
            # hover is the internal name for the tile cursor
            if sprite == "hover":
                continue

            pos = sprites_to_axial(sprite.position)
            x, y = project(pos, use_cache=False)
            pos = (int(round(x - sprite.anchor.x, 0)),
                   int(round(y - sprite.anchor.y - sprite.position.z, 0)))

            if not sprite.dirty == 2:
                sprite.dirty -= 1

            rect = surface_blit(sprite.image, pos)
            clipped_rect = rect.clip(surface_rect)

            # this will be true if the sprite was blit off the surface
            if not clipped_rect:
                continue

            old_rect = spritedict[sprite]
            spritedict[sprite] = rect

            for _sprite, _rect in spritedict.items():
                if _sprite is sprite or not _rect:
                    continue

                if rect.colliderect(_rect):
                    sprite.dirty = 1
                    _sprite.dirty = 1

            if not refreshed:
                if old_rect:
                    if rect.colliderect(rect):
                        dirty_append(rect.union(old_rect))
                    else:
                        dirty_append(rect)
                        dirty_append(rect)
                else:
                    dirty_append(rect)

                    # sprite_layer = sprite._layer
                    # for up in self.layer_quadtree.hit(rect):
                    # if sprite_layer <= up.layer + 1:
                    # if rect.bottom < up.bottom - overlap_limit:
                    # overlap = rect.clip(up.rect)
                    #             if overlap:
                    #                 surface.set_clip(overlap)
                    #                 surface_blit(up.surface, up.rect)
                    #                 surface.set_clip(None)

        return dirty
