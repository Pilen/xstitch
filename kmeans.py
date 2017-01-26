#!/usr/bin/python3

import random

from kdtree import KDTree, NaiveNeighbour

def groupby(items, key):
    result = {}
    for item in items:
        value = key(item)
        if value in result:
            result[value].append(item)
        else:
            result[value] = [item]
    return result

def kmeans(k, values, axises):
    def apply_axises(item):
        return tuple(axis(item) for axis in axises)

    def axis_grabber(x):
        return lambda item: item[x]

    random.seed(1337)
    print(random.randint(0, 100000))

    if isinstance(values, dict):
        new_values = []
        for item, count in values.items():
            new_values += [item]*count
        values = new_values
    dimensions = len(axises)
    tuple_axises = [axis_grabber(i) for i in range(dimensions)]
    values = [apply_axises(value) for value in values]
    startingmeans = list(set(values))
    random.shuffle(startingmeans)
    means = startingmeans[:k]

    # values = list(values)
    random.shuffle(values)
    means = values[:k]
    # means = [apply_axises(value) for value in values[:k]]

    iteration = 0
    while True:
        if iteration >= 1000:
            break
        print(iteration)
        # Assignment
        tree = KDTree(means, tuple_axises)
        groups = groupby(values, key=lambda x: tree.nearest_neighbour(x))
        # Update
        new_means = []
        for _, items in groups.items():
            l = 0
            new_mean = [0]*dimensions
            for item in items:
                l += 1
                for i in range(dimensions):
                    new_mean[i] += item[i]
            new_mean = tuple(x / l for x in new_mean)
            new_means.append(new_mean)
        if means == new_means:
            print("\nKmeans finished after", iteration, "iterations")
            return new_means
        means = new_means
        iteration += 1
    print("\nERROR: Ran out of iterations", iteration)
    return means
