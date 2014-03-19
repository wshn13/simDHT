#encoding: utf-8
from time import time
from random import randint
from bisect import bisect_left

from constants import *
from utils import intify

class BucketFull(Exception):
    pass


class KTable(object):
    def __init__(self, nid):
        self.nid = nid
        self.buckets = [ KBucket(0, 2**160) ]

    def append(self, node):
        index = self.bucket_index(node.nid)
        try:
            bucket = self.buckets[index]
            bucket.append(node)
        except IndexError:
            return
        except BucketFull:
            if not bucket.in_range(self.nid): return

            self.split_bucket(index)
            self.append(node)

    def find_close_nodes(self, target, n=K):
        nodes = []
        if len(self.buckets) == 0: return nodes
        if len(target) != 20 : return nodes

        index = self.bucket_index(target)
        try:
            nodes = self.buckets[index].nodes
            min = index - 1
            max = index + 1

            while len(nodes) < n and ((min >= 0) or (max < len(self.buckets))):
                if min >= 0:
                    nodes.extend(self.buckets[min].nodes)

                if max < len(self.buckets):
                    nodes.extend(self.buckets[max].nodes)

                min -= 1
                max += 1

            num = intify(target)
            nodes.sort(lambda a, b, num=num: cmp(num^intify(a.nid), num^intify(b.nid)))
            return nodes[:n]
        except IndexError:
            return nodes

    def bucket_index(self, target):
        return bisect_left(self.buckets, intify(target))

    def split_bucket(self, index):
        old = self.buckets[index]
        point = old.max - (old.max - old.min)/2
        new = KBucket(point, old.max)
        old.max = point
        self.buckets.insert(index + 1, new)
        for node in old.nodes[:]:
            if new.in_range(node.nid):
                new.append(node)
                old.remove(node)

    def __iter__(self):
        for bucket in self.buckets:
            yield bucket

    def __len__(self):
        length = 0
        for bucket in self:
            length += len(bucket)
        return length


class KBucket(object):
    __slots__ = ("min", "max", "nodes")

    def __init__(self, min, max):
        self.min = min
        self.max = max
        self.nodes = []

    def append(self, node):
        if node in self:
            self.remove(node)
            self.nodes.append(node)
        else:
            if len(self) < K:
                self.nodes.append(node)
            else:
                raise BucketFull

    def remove(self, node):
        self.nodes.remove(node)

    def in_range(self, target):
        return self.min <= intify(target) < self.max

    def __len__(self):
        return len(self.nodes)

    def __contains__(self, node):
        return node in self.nodes

    def __iter__(self):
        for node in self.nodes:
            yield node

    def __lt__(self, target):
        return self.max <= target


class KNode(object):
    __slots__ = ("nid", "ip", "port")
    
    def __init__(self, nid, ip, port):
        self.nid = nid
        self.ip = ip
        self.port = port

    def __eq__(self, other):
        return self.nid == other.nid