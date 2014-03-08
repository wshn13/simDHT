#encoding: utf-8
from time import time
from hashlib import sha1
from bencode import bencode, bdecode
import socket

import tornado.ioloop

from utils import *
from constants import *
from ktable import *

def timer(callback, time):
    tornado.ioloop.PeriodicCallback(callback, time * 1000).start()

class KRPC(object):
    def __init__(self, ioloop):
        self.types = {
            "r": self.response_received,
            "q": self.query_received,
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
        self.last_find_node = time()

        #每隔15分钟后重新加入DHT网络
        timer(self.rejoinDHT, 15 * 60)

        #每隔KRPC_TIMEOUT秒, 检查最后发送的find_node请求, 
        #看是否中断了find_node, 一旦中断了, 接着重来
        timer(self.timeout, KRPC_TIMEOUT)

    def find_node(self, address):
        tid = entropy(3)
        snid = self.table.nid
        msg = {
            "t": tid,
            "y": "q",
            "q": "find_node",
            "a": {"id": snid, "target": snid}
        }
        self.send_query(msg, address)

    def find_node_handler(self, res):
        try:
            nodes = decode_nodes(res["r"]["nodes"])
            for node in nodes:
                (nid, ip, port) = node
                if nid == self.table.nid: continue #不存自己
                self.table.append(KNode(nid, ip, port))
                self.last_find_node = time()
                self.find_node((ip, port))
        except KeyError:
            pass

    def joinDHT(self):
        for address in BOOTSTRAP_NODES: self.find_node(address)

    def rejoinDHT(self):
        self.table.nid = node_id()
        self.table.buckets = [ KBucket(0, 2**160) ]
        self.joinDHT()

    def timeout(self):
        if time() - self.last_find_node > KRPC_TIMEOUT: self.joinDHT()

    def start(self):
        self.joinDHT()
        self.ioloop.start()


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
                "r": {"id": self.table.nid}
            }
            (ip, port) = address
            self.table.append(KNode(nid, ip, port))
            self.send_response(msg, address)
        except KeyError:
            pass


    def find_node_received(self, res, address):
        try:
            target = res["a"]["target"]
            close_nodes = self.table.find_close_nodes(target, 16)
            if not close_nodes: return

            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid, "nodes": encode_nodes(close_nodes)}
            }
            nid = res["a"]["id"]
            (ip, port) = address
            self.table.append(KNode(nid, ip, port))
            self.send_response(msg, address)
        except KeyError:
            pass

    def get_peers_received(self, res, address):
        try:
            infohash = res["a"]["info_hash"]
            close_nodes = self.table.find_close_nodes(infohash, 16)
            if not close_nodes: return

            nid = res["a"]["id"]
            h = sha1()
            h.update(infohash+nid)
            token = h.hexdigest()[:TOKEN_LENGTH]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid, "nodes": encode_nodes(close_nodes), "token": token}
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

                #验证token成功, 开始下载种子
                self.master.download_torrent(ip, port, infohash)
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid}
            }
            self.send_response(msg, address)
        except KeyError:
            pass