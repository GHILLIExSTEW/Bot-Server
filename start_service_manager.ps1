# DBSBM Service Manager Launcher
# PowerShell version for better Windows integration

Set-Location $PSScriptRoot
$Host.UI.RawUI.WindowTitle = "DBSBM Service Manager"

Write-Host "Starting DBSBM Integrated Service Manager..." -ForegroundColor Green
Write-Host "This will open a GUI window to control all services." -ForegroundColor Yellow
Write-Host ""

try {
    python integrated_service_manager.py
} catch {
    Write-Host "Error starting service manager: $_" -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
