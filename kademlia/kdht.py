#encoding: utf-8
from time import time
from hashlib import sha1
from bencode import bencode, bdecode
from functools import partial
import socket
from tornado.ioloop import PeriodicCallback
import tornado.ioloop

from utils import *
from constants import *
from ktable import *


def timer(callback, time):
    PeriodicCallback(callback, time * 1000).start()


class KRPC(object):
    def __init__(self, ioloop):
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
        self.ioloop = ioloop
        self.ioloop.add_handler(self.socket.fileno(), self.data_received, self.ioloop.READ)

    def data_received(self, fd, events):
        (data, address) = self.socket.recvfrom(65536)
        try:
            res = bdecode(data)
            self.types[res["y"]](res, address)
        except Exception:
            pass

    def response_received(self, res, address):
        self.find_node_handler(res)

    def query_received(self, res, address):
        try:
            self.actions[res["q"]](res, address)
        except KeyError:
            pass

    def send_krpc(self, msg, address):
        self.socket.sendto(bencode(msg), address)

    def send_query(self, msg, address):
        self.send_krpc(msg, address)

    def send_response(self, msg, address):
        self.send_krpc(msg, address)


class Client(KRPC):
    def __init__(self, table, ioloop):
        KRPC.__init__(self, ioloop)
        self.table = table
        self.version = "simDHT"

        timer(self.timeout, KRPC_TIMEOUT)
        timer(self.reborn, 5 * 60)

    def find_node(self, address, nid=None):
        nid = self.get_neighbor(nid) if nid else self.table.nid
        tid = entropy(TID_LENGTH)
        
        msg = {
            "v": self.version,
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
                self.ioloop.add_timeout(time()+0.01, 
                    partial(self.find_node, (ip, port), nid))                
        except KeyError:
            pass

    def joinDHT(self):
        for address in BOOTSTRAP_NODES: self.find_node(address)

    def timeout(self):
        if len(self.table.buckets) < 2: self.joinDHT()

    def reborn(self):
        self.table.buckets = [ KBucket(0, 2 ** 160) ]

    def start(self):
        self.joinDHT()
        self.ioloop.start()

    def get_neighbor(self, nid):
        return nid[:10]+self.table.nid[10:]


class Server(Client):
    def __init__(self, table, master, ioloop):
        Client.__init__(self, table, ioloop)
        self.master = master

    def ping_received(self, res, address):
        try:
            nid = res["a"]["id"]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.get_neighbor(nid)}
            }
            (ip, port) = address
            self.send_response(msg, address)
        except KeyError:
            pass

    def find_node_received(self, res, address):
        try:
            target = res["a"]["target"]
            close_nodes = self.table.find_close_nodes(target, 8)
            if not close_nodes: return
            nid = res["a"]["id"]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.get_neighbor(target), "nodes": encode_nodes(close_nodes)}
            }
            (ip, port) = address
            self.send_response(msg, address)
        except KeyError:
            pass

    def get_peers_received(self, res, address):
        try:
            infohash = res["a"]["info_hash"]
            close_nodes = self.table.find_close_nodes(infohash, 8)
            if not close_nodes: return

            nid = res["a"]["id"]
            h = sha1()
            h.update(infohash+nid)
            token = h.hexdigest()[:TOKEN_LENGTH]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.get_neighbor(infohash), "nodes": encode_nodes(close_nodes), "token": token}
            }
            (ip, port) = address
            self.table.append(KNode(nid, ip, port))
            self.send_response(msg, address)
        except KeyError:
            pass

    def announce_peer_received(self, res, address):
        try:
            infohash = res["a"]["info_hash"]
            token = res["a"]["token"]
            nid = res["a"]["id"]
            h = sha1()
            h.update(infohash+nid)
            if h.hexdigest()[:TOKEN_LENGTH] == token:
                (ip, port) = address
                try:
                    implied_port  = res["a"]["implied_port"]
                    if int(implied_port) == 0:
                        port = res["a"]["port"]
                except (KeyError,ValueError):
                    pass

                self.master.log(ip, port, infohash)
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.get_neighbor(infohash)}
            }
            self.send_response(msg, address)
        except KeyError:
            pass