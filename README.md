simDHT:
======
基于tornado/Kademlia而写的高效DHT爬虫.


依赖包:
======
1. [tornado](https://pypi.python.org/pypi/tornado/3.2)
2. [bencode](https://pypi.python.org/pypi/bencode/1.0)


在Linux启动*simDHT*:
================
1. `python simDHT.py &`


在Linux关闭*simDHT*
============
1. `ps aux | grep simDHT.py`
2. `kill -9 PID`


配置文件:
========
1. `kademlia/constants.py`


其他:
====
1. 请在有公网IP的机子运行.
2. 因只实现了DHT协议, 未实现种子下载, 所收集到的**infohash**将会存储在**infohash.log**文件中.
3. 种子下载可去迅雷种子库下载、使用[libtorrent](http://libtorrent.org)、实现种子协议([bep0003](www.bittorrent.org/beps/bep_0003.html), [bep0009](www.bittorrent.org/beps/bep_0009.html), [bep0010](www.bittorrent.org/beps/bep_0010.html))