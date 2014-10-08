import pygame
import pygame.gfxdraw
import threading
from pygame.transform import smoothscale
from six.moves import queue
from math import sin, cos, pi, sqrt, radians, ceil
from itertools import product
from collections import defaultdict

from yourgame.euclid import Vector2, Point3, Vector3, Matrix4
from yourgame import resources
from yourgame.hex_model import *


__all__ = ['HexMapView']


class BlitThread(threading.Thread):
    def __init__(self, q0, q1, blit):
        threading.Thread.__init__(self)
        self.q0 = q0
        self.q1 = q1
        self.blit = blit
        self.running = False
        self.daemon = True

    def run(self):
        blit = self.blit
        get = self.q0.get
        put = self.q1.put
        task_done = self.q0.task_done

        self.running = True
        while self.running:
            try:
                surface, cell, pos, layer = get(True, 30)
            except queue.Empty:
                self.running = False
                break

            else:
                rect = blit(surface, pos)
                put((cell, surface, rect, layer))
                task_done()


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
        self.hex_radius = None
        self.overlap_limit = None
        self.tilt = .84
        self.size_ratio = 1.3

        self.default_cell = Cell()
        self.default_cell.filename = 'tileGrass.png'

        # this must be set to true when tile size or tilt changes
        self.needs_cache = None

        # set this to True to trigger a map redraw
        self.needs_refresh = None

        self.upper_cells = list()
        self.rect = None
        self.lost_sprites = list()
        self.map_rect = None
        self._old_hovered = None
        self._hovered = None
        self._selected = list()
        self._hex_draw = None
        self._hex_tile = None
        self.project = None
        self._buffer = None
        self._thread = None
        self._blit_queue = None
        self._return_queue = None
        self.set_tilt(self.tilt)
        self.set_radius(radius)

        self.spritedict["hover"] = None

    def test_sprite_collisions(self):
        stale = set()
        sprites = self.sprites()
        for left in sprites:
            for right in sprites:
                if left is right:
                    continue
                if collide_hex(left, right) and (left, right) not in stale:
                    stale.add((right, left))
                    self.scene.raise_event("HexMapView",
                                           "Collision",
                                           left=left, right=right)

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
        def draw_tile(blit, cell, coords, layer):
            x, y, z = coords - (half_width, half_height, 0)
            tile = tile_dict[cell.filename]
            return blit((tile, cell, (int(x), int(y)), layer))

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
            coords = Vector3(size_sqrt3*(i[0]+i[1]/2.), size_ratio*i[1], 0)
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
        self._voff = size_ratio

        rw, rh = self.rect.size
        mw = pw * self.data.size[0] * 1.05
        mh = ph * self.data.size[1] * 3. / 4. * 1.15
        hw = int((rw / 2.) - (mw / 2.))
        hh = int((rh / 2.) - (mh / 2.))

        hh *= 1.6

        screen_offset = Vector3(hw + pw, hh + ph / 2., 0)
        map_rect = pygame.Rect((hw, hh), (mw, mh))

        self._pixel_offset = Vector2(*screen_offset[:2])

        def cached_project(i, cell=None, use_cache=True):
            if use_cache:
                try:
                    return cache[i]
                except KeyError:
                    coords = project(i, cell)
                    cache[i] = coords
                    return coords
            else:
                return project(i, cell)

        return map_rect, cached_project

    def set_tilt(self, tilt):
        self.tilt = tilt
        self.needs_cache = True
        self.needs_refresh = True

    def set_radius(self, radius):
        self.hex_radius = radius
        self.overlap_limit = int(radius * .25)
        self.needs_cache = True
        self.needs_refresh = True

    def select_cell(self, cell):
        self._selected.append(cell)

    def highlight_cell(self, cell):
        # hightlight cell (like for picking with mouse)
        if self._old_hovered is not cell:
            self._old_hovered = self._hovered
            self._hovered = cell

    def point_from_surface(self, point):
        if self.rect is None:
            return None

        x, y = point
        x -= self._pixel_offset.x
        y -= self._pixel_offset.y
        y *= 1.1

        point = Point3(x, y, 0)
        x, y, z = Vector3(*pixel_to_axial(point, self.hex_radius))
        return x, y

    def point_from_local(self, point):
        # if self._rect is None:
        # return None
        #
        # point = Vector3(*point) - (self._rect.left, self._rect.top, 0)
        # return point[0] + self._hw, point[1] + self._hh
        raise NotImplementedError

    def clear(self, surface, bgk=None):
        if self._buffer is None:
            return
        blit = surface.blit
        _buffer = self._buffer
        [blit(_buffer, r, r) for r in self.lostsprites]
        [blit(_buffer, r, r) for r in filter(None, self.spritedict.values())]

    def draw(self, surface):
        self.rect = surface.get_rect()

        if self.needs_cache:
            self.set_tilt(self.tilt)
            self._buffer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self.map_rect, self.project = self.get_projection()
            self._hex_draw = self.get_hex_draw()
            self._hex_tile = self.get_hex_tile()
            self.needs_cache = False
            self.needs_refresh = True

        dirty = self.lost_sprites
        project = self.project
        draw_tile = self._hex_tile
        draw_hex = self._hex_draw
        get_cell = self.data.get_cell
        surface_blit = surface.blit
        dirty_append = dirty.append
        spritedict = self.spritedict

        self.lost_sprites = list()
        refreshed = False

        # draw the cell tiles, a thread will blit the tiles in the background
        # this is rendering the background and all hex tiles
        if self.needs_refresh:
            if self._thread is None:
                def buffer_blit(*args):
                    return self._buffer.blit(*args)

                self._blit_queue = queue.Queue()
                self._return_queue = queue.Queue()
                self._thread = BlitThread(self._blit_queue,
                                          self._return_queue,
                                          buffer_blit)
                self._thread.start()

            self.upper_cells = list()
            put_tile = self._blit_queue.put

            # get in draw order
            ww, hh = self.data.size
            print ww, hh
            for qq, rr in product(range(hh), range(ww)):
                # convert => axial
                q, r = evenr_to_axial((rr, qq))
                cell = get_cell((q, r))

                # convert => screen
                pos = Vector3(*project((q, r), cell))

                draw_tile(put_tile, self.default_cell, pos, 0)

                # draw tall columns
                if cell.height > 0:
                    for i in range(int(ceil(cell.height))):
                        # translate the cell height
                        # pos.y -= self.hex_radius / 2 * float(cell.height)
                        pos.y -= self._voff / 2
                        draw_tile(put_tile, cell, pos, i)
                else:
                    draw_tile(put_tile, cell, pos, 0)

            sorter = defaultdict(list)
            self._blit_queue.join()
            while 1:
                try:
                    cell, _surf, rect, layer = self._return_queue.get_nowait()
                except queue.Empty:
                    break
                else:
                    sorter[cell].append((_surf, rect, layer))

            f = lambda i: len(i[1]) > 1
            for key, value in filter(f, sorter.items()):
                #surfaces = [i[0] for i in value]
                rects = [i[1] for i in value]
                #layers = [i[2] for i in value]
                rect = rects[0].unionall(rects[1:])
                #tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
                tmp = pygame.Surface(rect.size, pygame.RLEACCEL)
                tmp.fill((0, 0, 0))
                tmp.set_alpha(128)
                self.upper_cells.append((tmp, rect, 1))

            rect = surface_blit(self._buffer, self.rect)
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
            # convert => screen
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
        # draw sprites to the surface, not the buffer
        for sprite in self.sprites():

            # hover is the internal name for the tile cursor
            if sprite == "hover":
                continue

            old_rect = spritedict[sprite]

            # convert => axial
            pos = sprites_to_axial(sprite.position[:2])

            # convert => screen
            # no cache here since we may be dealing with fractional coordinates
            x, y, z = project(pos, use_cache=False)

            # translate anchor and blit
            pos = (int(round(x - sprite.anchor.x, 0)),
                   int(round(y - sprite.anchor.y - sprite.position.z, 0)))

            rect = surface_blit(sprite.image, pos)
            if not refreshed:
                if old_rect:
                    if rect.colliderect(rect):
                        dirty_append(rect.union(old_rect))
                    else:
                        dirty_append(rect)
                        dirty_append(rect)
                else:
                    dirty_append(rect)
            spritedict[sprite] = rect

            # TODO: quadtree or somthing similar would be good here
            # draw the upper sprites over the map
            sprite_layer = sprite._layer
            for up_surf, up_rect, layer in self.upper_cells:
                if sprite_layer <= layer:
                    if rect.bottom < up_rect.bottom - overlap_limit:
                        overlap = rect.clip(up_rect)
                        if overlap:
                            surface.set_clip(overlap)
                            surface_blit(up_surf, up_rect)
                            surface.set_clip(None)

        return dirty
