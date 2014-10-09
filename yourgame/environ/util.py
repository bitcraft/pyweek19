### AXIAL
neighbor_mat = ((
    (1, 0),  (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
))


def clip(vector, lowest, highest):
    return type(vector)(map(min, map(max, vector, lowest), highest))


def surrounding_clip(coord, lower, upper):
    return (clip(i, lower, upper) for i in
            surrounding_noclip(coord))


def surrounding_noclip(coord):
    return ((coord[0]+n[0], coord[1]+n[1]) for n in neighbor_mat)


def surrounding(lower=None, upper=None):

    if lower is not None or upper is not None:
        def f(coord):
            return surrounding_clip(coord, lower, upper)
    else:
        def f(coord):
            return surrounding_noclip(coord)

    return f