#!/usr/bin/python3

import math
import random
import sys
from PIL import Image

import xstitch
from kdtree import KDTree, NaiveNeighbour


def range_1d_test():
    n = 100
    input = range(n)
    tree = xstitch.KDTree(input, [lambda x: x])
    for i in range(n):
        v = tree.nearest_neighbour(i)
        if i != v:
            print("ERROR:", i, "!=", v)
            return False
    return True

def rand_1d_test():
    input = [random.randint(0, 255) for _ in range(10)]
    # input = [x for x in range(100)]
    tree = xstitch.KDTree(input, [lambda x: x])
    naive = xstitch.NaiveNeighbour(input, [lambda x: x])
    for i in range(1000):
        a = tree.nearest_neighbour(i)
        b = naive.nearest_neighbour(i)
        if a != b:
            da = abs(i - a)
            db = abs(i - b)
            print("ERROR: {} -> {} != {} ({},{})".format(i, a, b, da, db))
            print(tree)
            return False
    return True

def image_test():
    def distance(a, b):
        return math.sqrt((a.red-b.red)**2 + (a.green-b.green)**2 + (a.blue-b.blue)**2)
    image = Image.open("test/autumn-04.jpg")
    class CS:
        def __init__(self, v):
            self.color_system_file = None
            self.color_system = v
    colors = xstitch.load_colors(CS("DMC1"))
    width, height = 218, 218
    image.resize((width, height))
    tree = xstitch.KDTree(colors,
                  [lambda c: c.red,
                   lambda c: c.green,
                   lambda c: c.blue])
    naive = xstitch.NaiveNeighbour(colors,
                           [lambda c: c.red,
                            lambda c: c.green,
                            lambda c: c.blue])
    result = True
    for y in range(height):
        for x in range(width):
            pixel = image.getpixel((x, y))
            pixel_color = xstitch.Color(*pixel[:3])
            a = tree.nearest_neighbour(pixel_color)
            b = naive.nearest_neighbour(pixel_color)
            if a != b:
                result = False
                print("ERROR: {} -> {} =! {},  {}/{}".format(pixel, a, b, distance(pixel_color, a), distance(pixel_color, b)))
    return result


def run_tests(*fs):
    result = 0
    for f in fs:
        print("====", f.__name__, "====")
        if not f():
            result = 1
            print(f.__name__, "failed")
    sys.exit(result)

def main():
    run_tests(range_1d_test,
              rand_1d_test,
              image_test)

if __name__ == "__main__":
    main()
