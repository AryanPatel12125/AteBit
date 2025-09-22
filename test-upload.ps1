# Test upload script for GCP integration
$uri = "http://localhost:8000/api/test-upload/"
$filePath = "test.txt"

# Create multipart form data
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$bodyLines = @(
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"test.txt`"",
    "Content-Type: text/plain",
    "",
    (Get-Content $filePath -Raw),
    "--$boundary--"
)

$body = $bodyLines -join $LF

try {
    $response = Invoke-RestMethod -Uri $uri -Method POST -Body $body -ContentType "multipart/form-data; boundary=$boundary"
    Write-Host "✅ SUCCESS: Upload completed"
    Write-Host ($response | ConvertTo-Json -Depth 10)
} catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        Write-Host $reader.ReadToEnd()
    }
}