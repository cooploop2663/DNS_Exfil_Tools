import socket
import base64
import hashlib
import re

# Assign the domain directly here
domain = "fileupload.example.com"

UDP_IP = "0.0.0.0"
UDP_PORT = 53

# Create the UDP socket and bind it to the IP and port
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(10)  # Set a timeout of 10 seconds for receiving data

# Print the IP and port the server is listening on
print(f"Listening on {UDP_IP}:{UDP_PORT}")

file_chunks = {}
file_md5 = ""
file_name = ""
total_chunks = 0
received_chunks = 0
is_transmission_complete = False

def calculate_md5(data):
    """Calculates the MD5 hash of the given data."""
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()

# Listen for incoming DNS requests
while not is_transmission_complete:
    try:
        byteData, addr = sock.recvfrom(2048)
    except socket.timeout:
        print("Socket timed out waiting for data.")
        continue

    try:
        # Since we are dealing with binary data, do not decode it as utf-8
        data = byteData.decode(errors="ignore")  # Ignoring decoding errors
    except Exception as e:
        print(f"Error decoding data: {e}")
        continue

    # Check for end of transmission signal (static "end" prefix)
    if f"e.end.{domain}" in data:
        print("Received end of transmission signal.")
        is_transmission_complete = True
        continue

    # Check for file info message (static "fileinfo" prefix)
    if f"f." in data:
        parts = data.split('.')
        if len(parts) >= 5:
            try:
                file_name = base64.b32decode(parts[1] + "=" * ((8 - len(parts[1]) % 8) % 8)).decode('utf-8')  # Decode the file name
                file_md5 = base64.b32decode(parts[2] + "=" * ((8 - len(parts[2]) % 8) % 8)).decode('utf-8')   # Decode the expected hash
                total_chunks = int(base64.b32decode(parts[3] + "=" * ((8 - len(parts[3]) % 8) % 8)).decode('utf-8'))  # Decode the total chunks
                print(f"Received file info: {file_name}, Expected MD5 hash: {file_md5}, Total Chunks: {total_chunks}")
            except Exception as e:
                print(f"Error decoding file info: {e}")
        continue

    # Extract the chunk number and data using regex (static "chunk" prefix)
    match = re.match(rf'c(\d+)\.([A-Z0-9]+)\.{domain}', data)
    if match:
        sequence_number, encoded_chunk = match.groups()
        received_chunks += 1
        print(f"Received chunk {received_chunks}/{total_chunks} from {addr}")

        try:
            # Decode the base32 encoded chunk to get the original binary data
            chunk_data = base64.b32decode(encoded_chunk + "=" * ((8 - len(encoded_chunk) % 8) % 8))
            file_chunks[int(sequence_number)] = chunk_data
            
        except Exception as e:
            print(f"Error decoding chunk {sequence_number}: {e}")

# Reassemble the file
if file_name and file_md5:
    print("Reassembling the file...")
    # Sort the chunks by sequence number
    ordered_chunks = [file_chunks[i] for i in sorted(file_chunks.keys())]
    
    # Concatenate the chunks in the correct order
    file_data = b''.join(ordered_chunks)
    
    # Calculate MD5 hash of the reassembled file
    received_file_md5 = calculate_md5(file_data)
    print(f"MD5 hash of the received file: {received_file_md5}")
    
    # Compare the MD5 hashes to ensure file integrity
    if received_file_md5 == file_md5:
        print("File transmission successful, hash matches!")
        
        # Save the file with the correct name and extension
        with open(file_name, 'wb') as f:
            f.write(file_data)
        print(f"File saved as {file_name}")
    else:
        print("MD5 hash mismatch! The file may have been corrupted during transmission.")
        print(f"Expected MD5: {file_md5}, but received: {received_file_md5}")
