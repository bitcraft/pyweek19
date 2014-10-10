#!/usr/bin/env python

"""
Generates a random map file.

Usage:

python makemap.py file_path [--num-adjacent=1] [--width=10] [--height=10]
"""

from argparse import ArgumentParser

from zort.environ.maze import new_maze


def main(args):
    hex_maze = new_maze(map_width=args.width,
                        map_height=args.height,
                        num_adjacent=args.num_adjacent)

    hex_maze.save_to_disk(args.file_path)
    print("Wrote maze to %s" % args.file_path)


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="makemap.py",
        description="Generate a mapfile for Zort the Explorer")

    parser.add_argument(
        "file_path",
        help="Path and filename to where the json file should be written. "
        "i.e. data/maps/awesomemap.json")

    parser.add_argument(
        "--num-adjacent", required=False, default=1, type=int,
        help="Modifies the behavior of the maze generator. "
        "More neighbors means a more dense map")

    parser.add_argument(
        "--width", required=False, default=10, type=int,
        help="The width of the map in hex tiles")

    parser.add_argument(
        "--height", required=False, default=10, type=int,
        help="The height of the map in hex tiles")

    args = parser.parse_args()
    main(args)
