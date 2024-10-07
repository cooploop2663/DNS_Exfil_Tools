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

# Print the IP and port the server is listening on
print(f"Listening on {UDP_IP}:{UDP_PORT}")

file_chunks = {}
file_md5 = ""
file_name = ""
is_transmission_complete = False

def calculate_md5(data):
    """Calculates the MD5 hash of the given data."""
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()

# Listen for incoming DNS requests
while not is_transmission_complete:
    byteData, addr = sock.recvfrom(2048)

    try:
        # Since we are dealing with binary data, do not decode it as utf-8
        data = byteData.decode(errors="ignore")  # Ignoring decoding errors
    except Exception as e:
        print(f"Error decoding data: {e}")
        continue

    # Check for end of transmission signal
    if f"end.chunk999.{domain}" in data:
        print("Received end of transmission signal.")
        is_transmission_complete = True
        continue

    # Check for file info message (contains file name and md5)
    if f"fileinfo.{domain}" in data:
        parts = data.split('.')
        if len(parts) >= 3:
            file_name = parts[0]
            file_md5 = parts[1]
            print(f"Received file name: {file_name}, Expected MD5 hash: {file_md5}")
        continue

    # Extract the chunk number and data using regex
    match = re.match(rf'([A-Z0-9]+)\.chunk(\d+)\.{domain}', data)
    if match:
        encoded_chunk, sequence_number = match.groups()
        print(f"Received chunk {sequence_number} from {addr}")

        try:
            # Decode the base32 encoded chunk to get the original binary data
            chunk_data = base64.b32decode(encoded_chunk)
            file_chunks[int(sequence_number)] = chunk_data
            
            # Print the actual chunk data (for debugging, you might want to comment this out later)
            print(f"Chunk {sequence_number} data: {chunk_data[:50]}...")  # Display first 50 bytes of the chunk
        except Exception as e:
            print(f"Error decoding chunk {sequence_number}: {e}")

# Reassemble the file
if file_name and file_md5:
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
