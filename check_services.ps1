# PowerShell Service Check Script
Write-Host "=== Service Status Check ===" -ForegroundColor Yellow

# Check if processes are running by PID
$pids = @(924, 6120, 204, 1396)
foreach ($pid in $pids) {
    try {
        $process = Get-Process -Id $pid -ErrorAction Stop
        Write-Host "PID $pid : RUNNING ($($process.ProcessName))" -ForegroundColor Green
    }
    catch {
        Write-Host "PID $pid : NOT RUNNING" -ForegroundColor Red
    }
}

Write-Host "`n=== Port Status ===" -ForegroundColor Yellow

# Check if ports are listening
$ports = @(5000, 80)
foreach ($port in $ports) {
    $listening = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($listening) {
        Write-Host "Port $port : LISTENING" -ForegroundColor Green
    } else {
        Write-Host "Port $port : NOT LISTENING" -ForegroundColor Red
    }
}

Write-Host "`n=== Manual Service Test ===" -ForegroundColor Yellow

# Test HTTP connectivity
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "HTTP localhost:5000 : WORKING (Status: $($response.StatusCode))" -ForegroundColor Green
}
catch {
    Write-Host "HTTP localhost:5000 : FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "HTTP localhost:80 : WORKING (Status: $($response.StatusCode))" -ForegroundColor Green
}
catch {
    Write-Host "HTTP localhost:80 : FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
