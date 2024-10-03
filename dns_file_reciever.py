import socket
import re
import base64

# IP and Port to listen on
UDP_IP = "0.0.0.0"
UDP_PORT = 53

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Dictionary to store the chunks
file_chunks = {}

def pad_base32(encoded_str):
    missing_padding = len(encoded_str) % 8
    if missing_padding:
        encoded_str += '=' * (8 - missing_padding)
    return encoded_str

def save_file(chunks, file_path):
    """Reassembles and saves the file from the collected chunks."""
    with open(file_path, 'wb') as f:
        for i in sorted(chunks):
            f.write(chunks[i])

print(f"Listening for DNS requests on {UDP_IP}:{UDP_PORT}...")

# Listen for incoming DNS requests
while True:
    # Receive data from the socket
    byteData, addr = sock.recvfrom(2048)  # buffer size is 2048 bytes
    try:
        # Decode the DNS message manually (skip parsing for simplicity)
        domain_name = byteData.decode('utf-8')

        # Regex to extract Base32 encoded chunk and sequence number
        m = re.search(r'([A-Z2-7]+)\.chunk(\d+)\.fileupload\.yourdomain\.com', domain_name)

        if m:
            encoded_chunk = m.group(1)
            sequence_number = int(m.group(2))
            
            # Add padding and decode the Base32 string
            padded_encoded_chunk = pad_base32(encoded_chunk)
            chunk_data = base64.b32decode(padded_encoded_chunk)
            
            # Store the chunk data in the dictionary
            file_chunks[sequence_number] = chunk_data
            print(f"Received chunk {sequence_number} from {addr}")

            # Check if all chunks are received (you might add some logic to determine the total number of chunks)
            if len(file_chunks) == expected_number_of_chunks:
                save_file(file_chunks, 'reconstructed_file.ext')
                print("File reconstructed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        continue
