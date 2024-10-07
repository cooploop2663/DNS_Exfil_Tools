import socket
import base64
import hashlib
import re

UDP_IP = "0.0.0.0"
UDP_PORT = 53

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

file_chunks = {}
file_md5 = ""
file_name = ""
is_transmission_complete = False

def calculate_md5(data):
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()

# Listen for incoming DNS requests
while not is_transmission_complete:
    byteData, addr = sock.recvfrom(2048)
    data = byteData.decode('utf-8')
    
    # Check for end of transmission signal
    if "end.chunk999.fileupload.example.com" in data:
        is_transmission_complete = True
        continue

    # Check for file info message (contains file name and md5)
    if "fileinfo.fileupload.example.com" in data:
        parts = data.split('.')
        if len(parts) >= 3:
            file_name = parts[0]
            file_md5 = parts[1]
        continue

    # Extract the chunk number and data
    match = re.match(r'([A-Z0-9]+)\.chunk(\d+)\.fileupload\.example\.com', data)
    if match:
        encoded_chunk, sequence_number = match.groups()
        try:
            chunk_data = base64.b32decode(encoded_chunk)
            file_chunks[int(sequence_number)] = chunk_data
        except binascii.Error as e:
            print(f"Error decoding chunk {sequence_number}: {e}")

# Reassemble the file
if file_name and file_md5:
    file_data = b''.join([file_chunks[i] for i in sorted(file_chunks.keys())])
    
    # Calculate MD5 hash of the reassembled file
    received_file_md5 = calculate_md5(file_data)
    print(f"MD5 hash of the received file: {received_file_md5}")
    
    # Compare MD5 hashes
    if received_file_md5 == file_md5:
        print("File transmission successful, hash matches!")
        
        # Save the file with the correct name and extension
        with open(file_name, 'wb') as f:
            f.write(file_data)
        print(f"File saved as {file_name}")
    else:
        print("MD5 hash mismatch! The file may have been corrupted during transmission.")
