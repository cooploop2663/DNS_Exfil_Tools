#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket

import re

import binascii

from dnslib import DNSRecord

UDP_IP = '0.0.0.0'

UDP_PORT = 53

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet
                                                         # UDP

sock.bind((UDP_IP, UDP_PORT))

while True:

    (byteData, addr) = sock.recvfrom(2048)  # buffer size is 2048 bytes

try:

    msg = binascii.unhexlify(binascii.b2a_hex(byteData))

    msg = DNSRecord.parse(msg)
except Exception, e:

    print e

    continue

m = re.search(r'\;(\S+)\.c2\.cooploop2663\.com', str(msg), re.MULTILINE)

if m:

    print ('got data:', m.group(1))
