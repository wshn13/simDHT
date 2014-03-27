#encoding: utf-8
from hashlib import sha1
from threading import Timer
from bencode import bencode, bdecode
import socket

from utils import *
from constants import *
from ktable import *

class KRPC(object):
    def __init__(self):
        self.types = {
            "r": self.response_received,
            "q": self.query_received
        }
        self.actions = {
            "ping": self.ping_received,
            "find_node": self.find_node_received,
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

    def send_query(self, msg, address):
        self.send_krpc(msg, address)

    def send_response(self, msg, address):
        self.send_krpc(msg, address)

class Client(KRPC):
    def __init__(self, table):
        KRPC.__init__(self)
        self.table = table
        Timer(REBORN, self.reborn).start()

    def find_node(self, address, nid=None):
        nid = self.get_neighbor(nid) if nid else self.table.nid
        tid = entropy(TID_LENGTH)
        
        msg = {
            "t": tid,
            "y": "q",
            "q": "find_node",
            "a": {"id": nid, "target": random_id()}
        }
        self.send_query(msg, address)

    def find_node_handler(self, res):
        try:
            nodes = decode_nodes(res["r"]["nodes"])
            for node in nodes:
                (nid, ip, port) = node
                if nid == self.table.nid: continue
                if len(nid) != 20: continue
                self.table.append(KNode(nid, ip, port))
                self.find_node( (ip, port), nid )
        except KeyError:
            pass

    def joinDHT(self):
        for address in BOOTSTRAP_NODES: self.find_node(address)

    def timeout(self):
        if len(self.table.buckets) < 2: self.joinDHT()

    def reborn(self):
        self.table.nid = random_id()
        self.table.buckets = [ KBucket(0, 2 ** 160) ]
        Timer(REBORN, self.reborn).start()

    def start(self):
        self.joinDHT()

        while True:
            try:
                (data, address) = self.socket.recvfrom(65536)
                res = bdecode(data)
                self.types[res["y"]](res, address)
            except Exception:
                pass        

    def get_neighbor(self, nid):
        return nid[:10]+self.table.nid[10:]

class Server(Client):
    def __init__(self, table, master):
        Client.__init__(self, table)
        self.master = master

    def ping_received(self, res, address):
        try:
            nid = res["a"]["id"]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.get_neighbor(nid)}
            }
            self.send_response(msg, address)
        except KeyError:
            pass

    def find_node_received(self, res, address):
        try:
            target = res["a"]["target"]
            neighbors = self.table.get_neighbors(target)

            if not neighbors: return

            nid = res["a"]["id"]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.get_neighbor(target), 
                    "nodes": encode_nodes(neighbors)
                }
            }
            self.send_response(msg, address)
        except KeyError:
            pass

    def get_peers_received(self, res, address):
        try:
            infohash = res["a"]["info_hash"]

            self.master.log(infohash)

            neighbors = self.table.get_neighbors(infohash)
            if not neighbors: return

            nid = res["a"]["id"]

            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.get_neighbor(infohash), 
                    "nodes": encode_nodes(neighbors)
                }
            }
            self.send_response(msg, address)
        except KeyError:
            pass

    def announce_peer_received(self, res, address):
        try:
            infohash = res["a"]["info_hash"]

            self.master.log(infohash)

            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.get_neighbor(infohash)}
            }
            self.send_response(msg, address)
        except KeyError:
            pass