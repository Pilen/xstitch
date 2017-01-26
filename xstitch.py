#!/usr/bin/python3

import argparse
import csv
import glob
import re
import os
import pathlib
import sys
import time
import math
import itertools
from PIL import Image

from kdtree import KDTree, NaiveNeighbour
from kmeans import kmeans
import report

scriptdir = os.path.dirname(os.path.abspath(sys.argv[0]))
color_system_format = ["name", "description", "red", "green", "blue", "hex"]

axises = [lambda c: c.red, lambda c: c.green, lambda c: c.blue]

class Color:
    def __init__(self, red, green, blue, name=None, description=None, hex=None):
        self.red = int(red)
        self.green = int(green)
        self.blue = int(blue)
        self.name = name
        self.description = description
        self.hex = hex
    def rgb(self):
        return (self.red, self.green, self.blue)
    def hsv(self):
        r = self.red/255.0
        g = self.green/255.0
        b = self.blue/255.0
        m = min(r,g,b)
        M = max(r,g,b)
        v = M
        delta = M - m
        if v == 0:
            return (0, 0, v)
        else:
            s = delta / M

        if delta == 0:
            h = 0
        if M == r:
            h = ((g - b)/delta)
        if M == g:
            h = (b-r)/delta + 2
        if M == b:
            h = (r-g)/delta + 4
        h *= 60
        if h < 0:
            h += 360
        return (h, s, v)

    def __repr__(self):
        return "Color({})".format(", ".join(str(x) for x in (self.red, self.green, self.blue, self.name) if x is not None))

def parse_arguments():
    color_systems = [x[len("color-systems/"):-4] for x in glob.glob("color-systems/*.csv")]
    parser = argparse.ArgumentParser(description="Create a cross-stitch embroidery from an image.")
    parser.add_argument("input", help="Input file to read from, eg 'embroidery.png', use '-' to read from stdin.")
    parser.add_argument("-o", "--output", type=argparse.FileType("w"), help="Output file to write to, eg 'embroidery.pdf', use '-' to print to stdout. (default: use the input filename)")
    parser.add_argument("-s", "--size", help="Size of final embroidery in crosses. Given as width*height, eg 400*300. (default: use image dimensions)", default=None)
    parser.add_argument("-p", "--page", default="A4", help="Page type type or page dimensions for the output")
    parser.add_argument("-c", "--colors", type=int, help="Maximum number of different colors to use")
    parser.add_argument("-b", "--brightness", "--brightness-cutoff", help="Brightness value to ignore, no stitches will be put at pixels brighter than this value, can either be one or three integers [0-255].")
    parser.add_argument("-m", "--margin", type=float, default=10.0, help="Width of margin of paper, in mm. (default: 10mm)")
    parser.add_argument("-g", "--grid", "--grid-size", type=float, default=3.0, help="Grid size of the pattern, in mm. (default: 3.0mm)")
    parser.add_argument("--method", default="tree", choices=["naive", "tree"], help="Algorithm to use")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--color-system", choices=color_systems, help="The yarn color system to use", default="DMC")
    group.add_argument("--color-system-file", help="The yarn color system file to use")
    args = parser.parse_args()
    return args

def load_colors(args):
    if args.color_system_file:
        filename = pathlib.Path(args.color_system_file)
    else:
        filename = pathlib.Path(scriptdir, "color-systems", args.color_system + ".csv")
    try:
        with filename.open(newline='') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=color_system_format)
            colors = [Color(row["red"], row["green"], row["blue"], row["name"], row["description"], row["hex"])
                      for row in reader]
            return colors
    except FileNotFoundError:
        print("ERROR: color system not found '{}'".format(filename))
        sys.exit(1)

def color_convert(image, colortree, colors=None):
    image = image.copy()
    duration = 0
    for i, pixel in enumerate(image.getdata()):
        y = i // image.width
        x = i % image.width
        pixel_color = Color(*pixel[:3])
        matched_color = colortree.nearest_neighbour(pixel_color)
        new_color = (matched_color.red, matched_color.green, matched_color.blue)
        image.putpixel((x, y), new_color)
    return image

def get_pixels(image):
    for i, pixel in enumerate(image.getdata()):
        y = i // image.width
        x = i % image.width
        yield Color(*pixel[:3])

def count_unique(items):
    result = dict()
    for item in items:
        if item in result:
            result[item] += 1
        else:
            result[item] = 1
    return result

def main():
    args = parse_arguments()

    print("================ LOAD:    ================")
    try:
        image = Image.open(args.input)
    except FileNotFoundError:
        print("ERROR: file not found '{}'".format(args.input))
        sys.exit(1)
    except IOError:
        print("ERROR: File is not a readable image '{}'".format(args.input))
        sys.exit(1)

    print("================ RESIZE:  ================")
    if args.size:
        match = re.match("(\d+)[*+,.-xX ](\d+)", args.size)
        size = [int(x) for x in match.groups()]
        image = image.resize(size)
    image.save("out.scaled.png")

    print("================ COLORS:  ================")
    colors = load_colors(args)

    if args.method == "tree":
        color_tree = KDTree(colors, axises)
    elif args.method == "naive":
        color_tree = NaiveNeighbour(colors, axises)
    else:
        print("ERROR: Invalid method selected")
        sys.exit(1)

    print("================ REDUCE:  ================")
    if args.colors is not None:
        timer("kmeans")
        colors = get_pixels(image)
        means = kmeans(args.colors, colors, axises)
        final_colors = set(color_tree.nearest_neighbour(Color(*mean)) for mean in means)
        if len(final_colors) != args.colors:
            print("Warning: You wanted {} but xstitch reduced to {} colors".format(args.colors, len(final_colors)))
            # sys.exit(1)
        final_color_tree = KDTree(final_colors, axises)
        reduced = color_convert(image, final_color_tree)
        if len(final_color_tree.selected) != args.colors:
            print("Warning: Fewer than the wanted colors ended up being used ({} != {})".format(len(final_color_tree.selected), args.colors))
        timer("true pixels")
        timer("kmeans")
    else:
        final_color_tree = color_tree

    print("================ CONVERT: ================")
    timer("convert")
    converted = color_convert(image, final_color_tree);
    timer("convert")

    print("================ OUTPUT:  ================")
    report.create(args, converted, final_color_tree.selected)

timemap = dict()
def timer(name):
    start = timemap.pop(name, None)
    if start is None:
        timemap[name] = time.time()
    else:
        duration = time.time() - start
        timemap[name] = None
        print("TIME ({}): {}".format(name, duration))

if __name__ == "__main__":
    timer("main")
    main()
    timer("main")







def old_kmeans():
    print("================ REDUCE:  ================")
    if args.colors is not None:
        timer("kmeans")
        print("Kmeans on selected colors")
        timer("selected")
        means = kmeans(args.colors, count_unique(color_tree.selected), axises)
        final_colors = set(color_tree.nearest_neighbour(Color(*mean)) for mean in means)
        if len(final_colors) != args.colors:
            print("Warning: you wanted", args.colors, "but xstitch reduced to", len(final_colors), "colors")
            sys.exit(1)
        final_color_tree = KDTree(final_colors, axises)
        reduced = color_convert(image, final_color_tree)
        reduced.save("out.1a.png")
        reduced_converted = color_convert(converted, final_color_tree)
        reduced_converted.save("out.1b.png")
        timer("selected")

        print("Kmeans on all pixels")
        timer("pixels")
        means = kmeans(args.colors, count_unique(color_tree.all), axises)
        final_colors = set(color_tree.nearest_neighbour(Color(*mean)) for mean in means)
        if len(final_colors) != args.colors:
            print("Warning: you wanted", args.colors, "but xstitch reduced to", len(final_colors), "colors")
            # sys.exit(1)
        final_color_tree = KDTree(final_colors, axises)
        reduced = color_convert(image, final_color_tree)
        reduced.save("out.2a.png")
        reduced_converted = color_convert(converted, final_color_tree)
        reduced_converted.save("out.2b.png")
        timer("pixels")

        print("Kmeans on original colors")
        timer("true colors")
        colors = count_unique(get_pixels(image))
        colors = {c:1 for c in colors}
        print(len(colors))
        means = kmeans(args.colors, colors, axises)
        assert means is not None
        final_colors = set(color_tree.nearest_neighbour(Color(*mean)) for mean in means)
        if len(final_colors) != args.colors:
            print("Warning: you wanted", args.colors, "but xstitch reduced to", len(final_colors), "colors")
            # sys.exit(1)
        final_color_tree = KDTree(final_colors, axises)
        reduced = color_convert(image, final_color_tree)
        reduced.save("out.3a.png")
        reduced_converted = color_convert(converted, final_color_tree)
        reduced_converted.save("out.3b.png")
        timer("true colors")

        print("Kmeans on log original colors")
        timer("true colors")
        colors = count_unique(get_pixels(image))
        colors = {c:1 for c in colors}
        print(len(colors))
        means = kmeans(args.colors, colors, axises)
        assert means is not None
        final_colors = set(color_tree.nearest_neighbour(Color(*mean)) for mean in means)
        if len(final_colors) != args.colors:
            print("Warning: you wanted", args.colors, "but xstitch reduced to", len(final_colors), "colors")
            # sys.exit(1)
        final_color_tree = KDTree(final_colors, axises)
        reduced = color_convert(image, final_color_tree)
        reduced.save("out.4a.png")
        reduced_converted = color_convert(converted, final_color_tree)
        reduced_converted.save("out.4b.png")
        timer("true colors")

        print("Kmeans on original pixels")
        timer("true pixels")
        colors = get_pixels(image)
        means = kmeans(args.colors, colors, axises)
        assert means is not None
        final_colors = set(color_tree.nearest_neighbour(Color(*mean)) for mean in means)
        if len(final_colors) != args.colors:
            print("Warning: you wanted", args.colors, "but xstitch reduced to", len(final_colors), "colors")
            # sys.exit(1)
        final_color_tree = KDTree(final_colors, axises)
        reduced = color_convert(image, final_color_tree)
        reduced.save("out.5a.png")
        reduced_converted = color_convert(converted, final_color_tree)
        reduced_converted.save("out.5b.png")
        timer("true pixels")

        timer("kmeans")
