#encoding: utf-8

BOOTSTRAP_NODES = [
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881)
] 

KRPC_TIMEOUT = 10 #10s

K = 8

TID_LENGTH = 4

TOKEN_LENGTH = 4

DHT_PORT = 6881

REBORN = 5 * 60