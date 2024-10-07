import socket
import re
import base64
import hashlib

# IP and Port to listen on
UDP_IP = "0.0.0.0"
UDP_PORT = 53

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Dictionary to store the chunks
file_chunks = {}
# Variables to store the file name, extension, and MD5 hash
file_name = None
client_md5 = None

def pad_base32(encoded_str):
    """Ensure the Base32 encoded string is padded correctly."""
    missing_padding = len(encoded_str) % 8
    if missing_padding:
        encoded_str += '=' * (8 - missing_padding)
    return encoded_str

def save_file(chunks, file_name):
    """Reassembles and saves the file from the collected chunks."""
    with open(file_name, 'wb') as f:
        for i in sorted(chunks):
            f.write(chunks[i])

def calculate_md5(file_name):
    """Calculates the MD5 hash of the reassembled file."""
    md5 = hashlib.md5()
    with open(file_name, 'rb') as file:
        while chunk := file.read(4096):
            md5.update(chunk)
    return md5.hexdigest()

print(f"Listening for DNS requests on {UDP_IP}:{UDP_PORT}...")

# Listen for incoming DNS requests
while True:
    # Receive data from the socket
    byteData, addr = sock.recvfrom(2048)  # buffer size is 2048 bytes
    try:
        # Check if it's the file name and MD5 hash (file info should be sent as plain text)
        try:
            domain_str = byteData.decode('utf-8')  # Attempt to decode as a string

            # Check if it's the file info message with the file name and MD5 hash
            file_info_match = re.match(r'(.+)\.([a-f0-9]{32})\.fileinfo\.fileupload\.yourdomain\.com', domain_str)
            if file_info_match:
                file_name = file_info_match.group(1)
                client_md5 = file_info_match.group(2)
                print(f"Received file name: {file_name}, MD5 hash: {client_md5}")
                continue

            # Check if the message is the end-of-transmission signal
            if domain_str.startswith("end.chunk999.fileupload.yourdomain.com"):
                print("Received end of transmission signal.")
                if file_name:
                    # Reassemble and save the file
                    save_file(file_chunks, file_name)

                    # Calculate the MD5 hash of the reassembled file
                    server_md5 = calculate_md5(file_name)
                    print(f"MD5 hash of the reassembled file: {server_md5}")

                    # Compare MD5 hashes
                    if server_md5 == client_md5:
                        print(f"File '{file_name}' reconstructed successfully with matching MD5 hash!")
                    else:
                        print(f"MD5 mismatch! File '{file_name}' may be corrupted.")

                else:
                    print("File name not received, cannot save the file.")
                # Reset the dictionary for the next file transfer
                file_chunks.clear()
                file_name = None
                client_md5 = None
                continue

        except UnicodeDecodeError:
            # If decoding fails, assume this is a binary chunk
            pass

        # Process binary chunk (Base32 encoded data)
        chunk_match = re.search(r'([A-Z2-7]+)\.chunk(\d+)\.fileupload\.yourdomain\.com', byteData.decode('utf-8', errors='ignore'))

        if chunk_match:
            encoded_chunk = chunk_match.group(1)
            sequence_number = int(chunk_match.group(2))

            # Add padding and decode the Base32 string
            padded_encoded_chunk = pad_base32(encoded_chunk)
            chunk_data = base64.b32decode(padded_encoded_chunk)

            # Store the chunk data in the dictionary
            file_chunks[sequence_number] = chunk_data
            print(f"Received chunk {sequence_number} from {addr}")

    except Exception as e:
        print(f"Error: {e}")
        continue
