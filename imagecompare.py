#!/usr/bin/python3

import math
import sys
from PIL import Image

fails = None

def equals(items):
    it = iter(items)
    try:
        first = next(it)
    except StopIteration:
        return True
    return all(item == first for item in it)

def unique(items):
    items = list(items)
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result

def distance(pointa, pointb):
    return math.sqrt(sum((a - b)**2 for a,b in zip(pointa, pointb)))

def image_compare(images):
    width = images[0].width
    height = images[0].height
    global fails
    fails = Image.new("RGB", (width, height))
    if not equals(image.size for image in images):
        print ("Images of different size")
        return False
    if not equals(image.mode for image in images):
        print ("Images of different color modes")
        return False
    for y in range(height):
        for x in range(width):
            found = unique(image.getpixel((x, y)) for image in images)
            if len(found) > 1:
                fails.putpixel((x, y), (255, 255, 255))
                print("Colors does not match at ({},{}) {} -> {}".format(x, y, found, distance(found[0], found[1])))
            # if not equals(image.getpixel((x, y)) for image in images):
            #     print("Colors does not match at ({},{})".format(x, y))
            #     return False
    return True

def main():
    image_names = sys.argv[1:]
    try:
        images = [Image.open(name) for name in image_names]
    except FileNotFoundError as exn:
        print("ERROR: file not found '{}'".format(exn.filename))
        sys.exit(1)
    except IOError :
        print("ERROR: File is not a readable image {}", str(exn)[27:])
        sys.exit(1)


    global fails
    result = image_compare(images)
    if fails:
        fails.save("fails.png")
    if not result:
        sys.exit(1)

if __name__ == "__main__":
    main()
