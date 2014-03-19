#encoding: utf-8
import tornado.ioloop

from kademlia.kdht import Server
from kademlia.ktable import KTable
from kademlia.utils import node_id

class Master(object):
    def __init__(self, f):
        self.f = f

    def log(self, ip, port, infohash):
        self.f.write(infohash.encode("hex")+"\n")
        self.f.flush()

ioloop = tornado.ioloop.IOLoop.instance()
f = open("infohash.log", "a")
try:
    Server(KTable(node_id()), Master(f), ioloop).start()
except KeyboardInterrupt:
    ioloop.stop()
    f.close()