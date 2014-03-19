#encoding: utf-8
from hashlib import sha1
from random import randint
from struct import pack, unpack
from socket import inet_aton, inet_ntoa

def entropy(bytes):
    s = ""
    for i in range(bytes):
        s += chr(randint(0, 255))
    return s

def intify(hstr):
    return long(hstr.encode('hex'), 16)

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

def encode_nodes(nodes):
    strings = []

    for node in nodes:
        s = "%s%s%s" % (node.nid, inet_aton(node.ip), pack("!H", node.port))
        strings.append(s)

    return "".join(strings)