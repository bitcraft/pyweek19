#!/usr/bin/env python

"""
Generates a random map file.

Usage:

python makemap.py file_path [--num-adjacent=1] [--width=10] [--height=10]
"""

from argparse import ArgumentParser


def main(args):
    pass


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
        help="The width of map in hex tiles")

    parser.add_argument(
        "--height", required=False, default=10, type=int,
        help="The height of the map in hex tiles")

    args = parser.parse_args()
    main(args)
