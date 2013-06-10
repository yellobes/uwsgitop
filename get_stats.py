#!python

import socket
import sys

argc = len(sys.argv)

if argc < 2:
    raise Exception("You have to specify the uWSGI stats socket")

addr = sys.argv[1]
sfamily = socket.AF_UNIX
addr_tuple = addr
if ':' in addr:
    sfamily = socket.AF_INET
    addr_parts = addr.split(':')
    addr_tuple = (addr_parts[0], int(addr_parts[1]))

freq = 3
try:
    freq = int(sys.argv[2])
except:
    pass


js = ''

try:
    s = socket.socket(sfamily, socket.SOCK_STREAM)
    s.connect(addr_tuple)

    while True:
        data = s.recv(4096)
        if len(data) < 1:
            break
        js += data
except:
    raise Exception("unable to get uWSGI statistics")

print js
sys.exit(0)
