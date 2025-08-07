# DBSBM Master Service Manager
# PowerShell script to manage Discord Bot and Web Server

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "help")]
    [string]$Command = "help"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

function Show-Help {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   DBSBM Master Service Manager" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\service.ps1 [command]" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Green
    Write-Host "  start   - Start master service manager (runs indefinitely)" -ForegroundColor Gray
    Write-Host "  stop    - Stop all services" -ForegroundColor Gray
    Write-Host "  restart - Restart all services" -ForegroundColor Gray
    Write-Host "  status  - Show current service status" -ForegroundColor Gray
    Write-Host "  logs    - Show recent service logs" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Features:" -ForegroundColor Green
    Write-Host "  • Runs Discord Bot (DBSBM) and Web Server (DBSBMWEB)" -ForegroundColor Gray
    Write-Host "  • Auto-restart on failure with exponential backoff" -ForegroundColor Gray
    Write-Host "  • Monthly restart on first Monday at 3 AM" -ForegroundColor Gray
    Write-Host "  • Health monitoring every 30 seconds" -ForegroundColor Gray
    Write-Host "  • Comprehensive logging and status tracking" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\service.ps1 start     (starts and runs indefinitely)" -ForegroundColor Gray
    Write-Host "  .\service.ps1 status    (check if services are running)" -ForegroundColor Gray
    Write-Host ""
}

function Start-Services {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   Starting DBSBM Master Service Manager" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Starting services:" -ForegroundColor Green
    Write-Host "   Discord Bot: DBSBM\bot\main.py" -ForegroundColor White
    Write-Host "   Web Server:  DBSBMWEB\flask_service.py" -ForegroundColor White
    Write-Host "   Web Proxy:   DBSBMWEB\port80_proxy.py" -ForegroundColor White
    Write-Host ""
    Write-Host "This will run indefinitely until stopped with Ctrl+C" -ForegroundColor Yellow
    Write-Host ""
    
    python master_service_manager.py start
}

function Stop-Services {
    Write-Host "Stop: Stopping all DBSBM services..." -ForegroundColor Red
    python master_service_manager.py stop
    Write-Host "Done: Services stopped" -ForegroundColor Green
}

function Restart-Services {
    Write-Host "Restart: Restarting all DBSBM services..." -ForegroundColor Yellow
    python master_service_manager.py restart
    Write-Host "Done: Services restarted" -ForegroundColor Green
}

function Show-Status {
    python master_service_manager.py status
}

function Show-Logs {
    Write-Host ""
    Write-Host "Recent master service logs:" -ForegroundColor Cyan
    Write-Host "=============================" -ForegroundColor Cyan
    
    $logFiles = Get-ChildItem -Path "service_logs" -Filter "master_service_*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    
    if ($logFiles) {
        $latestLog = $logFiles[0]
        Write-Host ""
        Write-Host "Latest log file: $($latestLog.Name)" -ForegroundColor Yellow
        Write-Host ""
        
        # Show last 30 lines, filtering out noise
        Get-Content $latestLog.FullName -Tail 40 | Where-Object { 
            $_ -notmatch "GET /" -and 
            $_ -notmatch "404 -" -and 
            $_ -notmatch "health check" 
        } | Select-Object -Last 25
    } else {
        Write-Host "No log files found." -ForegroundColor Red
    }
    Write-Host ""
}

# Main script logic
switch ($Command.ToLower()) {
    "start" { Start-Services }
    "stop" { Stop-Services }
    "restart" { Restart-Services }
    "status" { Show-Status }
    "logs" { Show-Logs }
    "help" { Show-Help }
    default { Show-Help }
}
