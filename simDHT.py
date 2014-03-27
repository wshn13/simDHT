#encoding: utf-8
from bencode import bencode, bdecode
import socket

from hashlib import sha1
from random import randint
from struct import unpack
from socket import inet_aton, inet_ntoa

BOOTSTRAP_NODES = [
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881)
] 
TID_LENGTH = 4
DHT_PORT = 6881

def entropy(bytes):
    s = ""
    for i in range(bytes):
        s += chr(randint(0, 255))
    return s

def random_id():
    hash = sha1()
    hash.update( entropy(20) )
    return hash.digest()

def decode_nodes(nodes):
    n = []
    length = len(nodes)
    if (length % 26) != 0: 
        return n
    for i in range(0, length, 26):
        nid = nodes[i:i+20]
        ip = inet_ntoa(nodes[i+20:i+24])
        port = unpack("!H", nodes[i+24:i+26])[0]
        n.append( (nid, ip, port) )
    return n

class KRPC(object):
    def __init__(self):
        self.types = {
            "r": self.response_received,
            "q": self.query_received
        }
        self.actions = {
            "get_peers": self.get_peers_received,
            "announce_peer": self.announce_peer_received,
        }

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("0.0.0.0", DHT_PORT))

    def response_received(self, res, address):
        self.find_node_handler(res)

    def query_received(self, res, address):
        try:
            self.actions[res["q"]](res, address)
        except KeyError:
            pass

    def send_krpc(self, msg, address):
        try:
            self.socket.sendto(bencode(msg), address)
        except:
            pass

class Client(KRPC):
    def __init__(self):
        KRPC.__init__(self)

    def find_node(self, address, nid=None):
        nid = random_id()
        tid = entropy(TID_LENGTH)
        msg = {
            "t": tid,
            "y": "q",
            "q": "find_node",
            "a": {"id": nid, "target": nid}
        }
        self.send_krpc(msg, address)

    def find_node_handler(self, res):
        try:
            nodes = decode_nodes(res["r"]["nodes"])
            for node in nodes:
                (nid, ip, port) = node
                if len(nid) != 20: continue
                self.find_node( (ip, port), nid )
        except KeyError:
            pass

    def joinDHT(self):
        for address in BOOTSTRAP_NODES: self.find_node(address)

    def start(self):
        self.joinDHT()

        while True:
            try:
                (data, address) = self.socket.recvfrom(65536)
                res = bdecode(data)
                self.types[res["y"]](res, address)
            except Exception:
                pass

class Server(Client):
    def __init__(self, master):
        Client.__init__(self)
        self.master = master

    def get_peers_received(self, res, address):
        try:
            infohash = res["a"]["info_hash"]
            self.master.log(infohash)
        except KeyError:
            pass

    def announce_peer_received(self, res, address):
        try:
            infohash = res["a"]["info_hash"]
            self.master.log(infohash)
        except KeyError:
            pass

#using example
class Master(object):
    def __init__(self, f):
        self.f = f

    def log(self, infohash):
        self.f.write(infohash.encode("hex")+"\n")
        self.f.flush()
try:
    f = open("infohash.log", "a")
    m = Master(f)
    s = Server(Master(f))
    s.start()     
except KeyboardInterrupt:
    s.socket.close()
    f.close()