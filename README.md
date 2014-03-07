simDHT:
======
基于twisted/Kademlia, 代码简单.


依赖包:
======
1. [twisted](https://pypi.python.org/pypi/Twisted/13.2.0)
2. [bencode](https://pypi.python.org/pypi/bencode/1.0)


启动*simDHT*服务:
================
`twistd -y simDHT.py`


停止*simDHT*服务:
================
1. `cat twistd.pid`
2. `kill -9 PID`


配置文件:
========
`kademlia/constants.py`


其他:
====
1. 请在有公网IP的机子运行.
2. 因只实现了DHT协议, 未实现种子下载, 所收集到的**infohash**将会存储在**infohash.log**文件中.
3. 种子下载可去迅雷种子库下载、使用[libtorrent](http://libtorrent.org)、实现种子协议([bep0003](www.bittorrent.org/beps/bep_0003.html), [bep0009](www.bittorrent.org/beps/bep_0009.html), [bep0010](www.bittorrent.org/beps/bep_0010.html))