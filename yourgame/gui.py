from math import ceil
from itertools import product
from pygame import Surface, Rect, RLEACCEL
import pygame

__all__ = ['GraphicBox',
           'draw_text',
           'render_outline_text']


class GraphicBox(object):
    """
    Generic class for drawing graphical boxes

    load it, then draw it wherever needed
    """
    def __init__(self, filename, hollow=False):
        self.hollow = hollow

        image = pygame.image.load(filename)
        iw, self.th = image.get_size()
        self.tw = iw / 9
        names = "nw ne sw se n e s w c".split()
        tiles = [image.subsurface((i * self.tw, 0, self.tw, self.th))
                 for i in range(9)]

        if self.hollow:
            ck = tiles[8].get_at((0, 0))
            [t.set_colorkey(ck, RLEACCEL) for t in tiles]

        self.tiles = dict(zip(names, tiles))
        self.background = self.tiles['c'].get_at((0, 0))

    def draw(self, surface, rect):
        ox, oy, w, h = Rect(rect)

        for x in range(self.tw + ox, w - self.tw + ox, self.tw):
            surface.blit(self.tiles['n'], (x, oy))
            surface.blit(self.tiles['s'], (x, h - self.th + oy))

        for y in range(self.th + oy, h - self.th + oy, self.th):
            surface.blit(self.tiles['w'], (w - self.tw + ox, y))
            surface.blit(self.tiles['e'], (ox, y))

        if not self.hollow:
            p = product(range(self.tw + ox, w - self.tw + ox, self.tw),
                        range(self.th + oy, h - self.th + oy, self.th))

            [surface.blit(self.tiles['c'], (x, y)) for x, y in p]

        surface.blit(self.tiles['nw'], (ox, oy))
        surface.blit(self.tiles['ne'], (w - self.tw + ox, oy))
        surface.blit(self.tiles['se'], (ox, h - self.th + oy))
        surface.blit(self.tiles['sw'], (w - self.tw + ox, h - self.th + oy))


def draw_text(surface, text, color, rect, font=None, aa=False, bkg=None):
    """ draw some text into an area of a surface

    automatically wraps words
    returns any text that didn't get blitted
    passing None as the surface is ok
    """
    rect = Rect(rect)
    y = rect.top
    line_spacing = -2

    if font is None:
        full_path = pygame.font.get_default_font()
        font = pygame.font.Font(full_path, 16)

    # get the height of the font
    font_height = font.size("Tg")[1]

    # for very small fonts, turn off antialiasing
    if font_height < 16:
        aa = 0
        bkg = None

    while text:
        i = 1

        # determine if the row of text will be outside our area
        if y + font_height > rect.bottom:
            break

        # determine maximum width of line
        while font.size(text[:i])[0] < rect.width and i < len(text):
            if text[i] == "\n":
                text = text[:i] + text[i + 1:]
                break
            i += 1
        else:
            # if we've wrapped the text, then adjust the wrap to the last word
            if i < len(text):
                i = text.rfind(" ", 0, i) + 1

        if surface:
            # render the line and blit it to the surface
            if bkg:
                image = font.render(text[:i], 1, color, bkg)
                image.set_colorkey(bkg)
            else:
                image = font.render(text[:i], aa, color)

            surface.blit(image, (rect.left, y))

        y += font_height + line_spacing

        # remove the text we just blitted
        text = text[i:]

    return text


def render_outline_text(text, color, border, fontFilename, size,
                      colorkey=(128, 128, 0)):
    font = pygame.font.Font(fontFilename, size + 4)
    image = pygame.Surface(font.size(text), pygame.SRCALPHA)
    inner = pygame.font.Font(fontFilename, size - 4)
    outline = inner.render(text, 2, border)
    w, h = image.get_size()
    ww, hh = outline.get_size()
    cx = w / 2 - ww / 2
    cy = h / 2 - hh / 2
    for x in xrange(-3, 3):
        for y in xrange(-3, 3):
            image.blit(outline, (x + cx, y + cy))
    image.blit(inner.render(text, 1, color), (cx, cy))
    return image


class ScrollingTextPanel(object):
    """
    Area that can display text and maintains a buffer
    """
    def __init__(self, rect, maxlen):
        self.rect = rect
        self.maxlen = maxlen
        self.background = (0, 0, 0)
        self.text = list()

    def add(self, text):
        if len(self.text) == maxlen:
            self.text.pop(0)
        self.text.append(text)

    def draw(self, surface):
        for line in self.text:
            banner = TextBanner(line, size=self.text_size)
            surface.blit(banner.render(self.background), (x, y))
            y += banner.font.size(line)[1]


class VisualTimer(object):
    """
    Display a timer/progress bar
    """
    def __init__(self, finish, rect=None, color=(255, 255, 255)):
        self.time = 0
        self.finish = float(finish)

        if rect == None:
            rect = Rect(0, 0, 100, 16)

        self.rect = Rect(rect)
        self.size = self.rect.width
        self.color = color
        self.image = Surface(self.rect.size)
        self.finished = 0

    def set_alarm(self, time):
        self.finish = float(time)
        self.reset()

    def reset(self):
        self.time = 0
        self.finished = 0

    def update(self, time):
        if self.finished: return

        time += self.time

        if time <= self.finish:
            self.time = time
        else:
            self.finished = 1

    def draw(self, surface):
        if not self.finished:
            self.render()

        surface.blit(self.image, self.rect.topleft)

    def render(self):
        i = ceil(self.size * (self.time / self.finish))

        w, h = self.rect.size
        self.image.lock()

        self.image.fill((32, 32, 32))
        self.image.fill(self.color, (0, 0, i, self.rect.height))

        # Make the corners look pretty
        self.image.fill((0, 0, 0), (0, 0, 1, 1))
        self.image.fill((0, 0, 0), (w - 1, 0, 1, 1))
        self.image.fill((0, 0, 0), (w - 1, h - 1, 1, 1))
        self.image.fill((0, 0, 0), (0, h - 1, 1, 1))

        self.image.unlock()
