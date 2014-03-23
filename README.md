simDHT:
-------
A DHT crawler based on Kademlia/Tornado, written in Python, the code is very simple.

dependencies:
------------
1. [tornado](https://pypi.python.org/pypi/tornado/3.2)
2. [bencode](https://pypi.python.org/pypi/bencode/1.0)


start simDHT on *nix
--------------------
1. `python simDHT.py`


stop simDHT on *nix
-------------------
1. `ps aux | grep simDHT.py`
2. `kill -9 PID`


configure file:
---------------
1. `kademlia/constants.py`

UDP "connection" limit using iptables on Linux(example):
--------------------------------------------------------
1. `iptables -A INPUT -p udp -m limit --limit 500/s --limit-burst 1000 -j RETURN`
2. `iptables -A INPUT -p udp -j DROP`

note:
-----
1. `infohash` is saved in the `infohash.log`.
2. Please on the server running simDHT with a public IP.
