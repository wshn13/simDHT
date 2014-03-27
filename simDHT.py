#encoding: utf-8
from kademlia.kdht import Server
from kademlia.ktable import KTable
from kademlia.utils import random_id

class Master(object):
    def __init__(self, f):
        self.f = f

    def log(self, infohash):
        self.f.write(infohash.encode("hex")+"\n")
        self.f.flush()
        
try:
    f = open("infohash.log", "a")

    k = KTable(random_id())
    m = Master(f)

    s = Server(k, m)
    s.start()     
except KeyboardInterrupt:
    s.socket.close()