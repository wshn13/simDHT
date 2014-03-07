#encoding: utf-8

#起始node
BOOTSTRAP_NODES = [("router.bittorrent.com", 6881),("dht.transmissionbt.com", 6881)] 

#网络超时
KRPC_TIMEOUT = 10 #10s

#进行下一个find_node请求前的暂停时间
NEXT_FIND_NODE_INTERVAL = 15 / 1000.0 #15ms

#每bucket最多含多少node
K = 8

#传输ID的长度
TID_LENGTH = 3

#token的长度
TOKEN_LENGTH = 4

#监听端口
DHT_PORT = 6881