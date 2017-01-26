#!/usr/bin/python3

import math
import itertools

class KDTree:
    class Node:
        def __init__(self, pivot, left, right):
            self.pivot = pivot
            self.left = left
            self.right = right

        def __repr__(self):
            return "Node({})".format(str((self.pivot, self.left, self.right)))

    def __init__(self, values, axises):
        values = list(values)
        self.axises = axises
        self.cache = dict()
        self.selected = set()
        self.all = []

        def recursive(values, depth):
            if len(values) == 0:
                return None
            axis = axises[depth % len(axises)]
            values.sort(key=axis)
            median = len(values)//2
            while median > 0 and axis(values[median]) == axis(values[median - 1]):
                # ensure median is at boundery
                median -= 1
            # while median + 1 < len(values) and axis(values[median]) == axis(values[median + 1]):
            #     # ensure median is at boundery
            #     median += 1
            return self.Node(values[median],
                             recursive(values[:median], depth + 1),
                             recursive(values[median + 1:], depth + 1))
        self.root = recursive(values, 0)
        self.i = 0
        self.point = None
        self.debug = False

    def nearest_neighbour(self, point):
        self.i += 1
        self.point = point
        if self.i == -1:
            self.debug = True
        # self.debug = True
        # print("NN")
        def recursive(node, depth):
            def pprint(*args, **kwargs):
                if self.debug:
                    print("  "*depth, end="")
                    print(*args, **kwargs)
                    return None
            pprint("NNrec", node.pivot if node else "-")
            if node is None:
                pprint(":None")
                return None
            axis = self.axises[depth % len(self.axises)]
            if axis(point) < axis(node.pivot):
                best = recursive(node.left, depth + 1)
                other = node.right
            else:
                best = recursive(node.right, depth + 1)
                other = node.left

            if best is None:
                # pprint("best none!")
                best = node.pivot
            best_distance = self.distance(point, best)
            current_distance = self.distance(point, node.pivot)
            if current_distance < best_distance:
                # pprint("choose current")
                best = node.pivot
                best_distance = current_distance
            pprint("b, c:", best_distance, current_distance)
            if best_distance >= abs(axis(point) - axis(node.pivot)):
                other_best = recursive(other, depth + 1)
                if other_best is None:
                    pprint("other none:", best, )
                    return best
                other_distance = self.distance(point, other_best)
                if best_distance <= other_distance:
                    pprint("best better:", best)
                    return best
                else:
                    pprint("other better:", other_best)
                    return other_best
            pprint("best:", best)
            return best
        if point in self.cache:
            self.all.append(self.cache[point])
            return self.cache[point]
        result = recursive(self.root, 0)
        assert result is not None
        self.cache[point] = result
        self.selected.add(result)
        self.all.append(result)
        return result

    def distance(self, pointa, pointb):
        return math.sqrt(sum((axis(pointa) - axis(pointb))** 2 for axis in self.axises))

    def in_order(self):
        def recursive(node):
            if node is None:
                return []
            return itertools.chain(recursive(node.left),
                                   [node.pivot],
                                    recursive(node.right))
        return recursive(self.root)

    def __repr__(self):
        def recursive(node):
            if node is None:
                return ""
            return "".join(["(", recursive(node.left), ")",
                            "<", ",".join(str(axis(node.pivot)) for axis in self.axises), ">"
                            "(", recursive(node.right), ")"])
        return recursive(self.root)
        nodes = (tuple(axis(node) for axis in self.axises) for node in self.in_order())
        return "KDTree<{}>".format(", ".join(str(x) for x in nodes))

class NaiveNeighbour:
    def __init__(self, values, axises):
        self.values = list(values)
        self.axises = axises
        self.cache = dict()
        self.selected = set()
    def nearest_neighbour(self, point):
        def distance(p):
            return math.sqrt(sum((axis(point) - axis(p))** 2 for axis in self.axises))
        if point in self.cache:
            return self.cache[point]
        result = min(self.values, key=distance)
        self.cache[point] = result
        self.selected.add(result)
        return result
