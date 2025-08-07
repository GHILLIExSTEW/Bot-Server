# DBSBM Service Installer
# Creates a Windows Service for persistent operation

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("install", "uninstall", "start", "stop", "status")]
    [string]$Action = "help"
)

$ServiceName = "DBSBMasterService"
$ServiceDisplayName = "DBSBM Master Service Manager"
$ServiceDescription = "Manages DBSBM Discord Bot and Web Server with auto-restart and monthly scheduling"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "master_service_manager.py"

function Show-Help {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   DBSBM Windows Service Installer" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\install_service.ps1 [action]" -ForegroundColor White
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Green
    Write-Host "  install   - Install DBSBM as Windows Service" -ForegroundColor Gray
    Write-Host "  uninstall - Remove DBSBM Windows Service" -ForegroundColor Gray
    Write-Host "  start     - Start DBSBM Windows Service" -ForegroundColor Gray
    Write-Host "  stop      - Stop DBSBM Windows Service" -ForegroundColor Gray
    Write-Host "  status    - Show DBSBM Windows Service status" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Note: Run as Administrator for install/uninstall operations" -ForegroundColor Yellow
    Write-Host ""
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-DBSBMService {
    if (-not (Test-Administrator)) {
        Write-Host "❌ Administrator privileges required for service installation" -ForegroundColor Red
        Write-Host "Please run PowerShell as Administrator and try again" -ForegroundColor Yellow
        return
    }

    try {
        # Check if service already exists
        $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($existingService) {
            Write-Host "⚠️  Service '$ServiceName' already exists" -ForegroundColor Yellow
            Write-Host "Use 'uninstall' first to remove the existing service" -ForegroundColor Yellow
            return
        }

        # Create the service using sc.exe
        $pythonPath = (Get-Command python).Source
        $serviceCommand = "`"$pythonPath`" `"$PythonScript`" start"
        
        Write-Host "🔧 Installing DBSBM Windows Service..." -ForegroundColor Green
        Write-Host "Service Name: $ServiceName" -ForegroundColor Gray
        Write-Host "Display Name: $ServiceDisplayName" -ForegroundColor Gray
        Write-Host "Script Path: $PythonScript" -ForegroundColor Gray
        
        $result = & sc.exe create $ServiceName binPath= $serviceCommand DisplayName= $ServiceDisplayName start= auto
        
        if ($LASTEXITCODE -eq 0) {
            # Set service description
            & sc.exe description $ServiceName $ServiceDescription
            
            Write-Host "✅ DBSBM Windows Service installed successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "To start the service:" -ForegroundColor Yellow
            Write-Host "  .\install_service.ps1 start" -ForegroundColor White
            Write-Host ""
            Write-Host "Or use Windows Services Manager (services.msc)" -ForegroundColor Yellow
        } else {
            Write-Host "❌ Failed to install service" -ForegroundColor Red
            Write-Host $result -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error installing service: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Uninstall-DBSBMService {
    if (-not (Test-Administrator)) {
        Write-Host "❌ Administrator privileges required for service removal" -ForegroundColor Red
        Write-Host "Please run PowerShell as Administrator and try again" -ForegroundColor Yellow
        return
    }

    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if (-not $service) {
            Write-Host "⚠️  Service '$ServiceName' not found" -ForegroundColor Yellow
            return
        }

        # Stop service if running
        if ($service.Status -eq 'Running') {
            Write-Host "🛑 Stopping service..." -ForegroundColor Yellow
            Stop-Service -Name $ServiceName -Force
            Start-Sleep -Seconds 3
        }

        Write-Host "🗑️  Removing DBSBM Windows Service..." -ForegroundColor Red
        $result = & sc.exe delete $ServiceName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ DBSBM Windows Service removed successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to remove service" -ForegroundColor Red
            Write-Host $result -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error removing service: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Start-DBSBMService {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if (-not $service) {
            Write-Host "❌ Service '$ServiceName' not found. Install it first." -ForegroundColor Red
            return
        }

        if ($service.Status -eq 'Running') {
            Write-Host "✅ Service '$ServiceName' is already running" -ForegroundColor Green
            return
        }

        Write-Host "🚀 Starting DBSBM Windows Service..." -ForegroundColor Green
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 2
        
        $service = Get-Service -Name $ServiceName
        if ($service.Status -eq 'Running') {
            Write-Host "✅ DBSBM Windows Service started successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to start service" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error starting service: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Stop-DBSBMService {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if (-not $service) {
            Write-Host "❌ Service '$ServiceName' not found" -ForegroundColor Red
            return
        }

        if ($service.Status -ne 'Running') {
            Write-Host "Service '$ServiceName' is not running" -ForegroundColor Gray
            return
        }

        Write-Host "Stopping DBSBM Windows Service..." -ForegroundColor Yellow
        Stop-Service -Name $ServiceName -Force
        Start-Sleep -Seconds 2
        
        $service = Get-Service -Name $ServiceName
        if ($service.Status -eq 'Stopped') {
            Write-Host "DBSBM Windows Service stopped successfully!" -ForegroundColor Green
        } else {
            Write-Host "Failed to stop service" -ForegroundColor Red
        }
    } catch {
        Write-Host "Error stopping service: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Show-ServiceStatus {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if (-not $service) {
            Write-Host "Service '$ServiceName' not found" -ForegroundColor Red
            Write-Host "Install the service first with: .\install_service.ps1 install" -ForegroundColor Yellow
            return
        }

        Write-Host ""
        Write-Host "DBSBM Windows Service Status" -ForegroundColor Cyan
        Write-Host "================================" -ForegroundColor Cyan
        Write-Host "Service Name: $($service.Name)" -ForegroundColor White
        Write-Host "Display Name: $($service.DisplayName)" -ForegroundColor White
        Write-Host "Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq 'Running') { 'Green' } else { 'Red' })
        Write-Host "Start Type: $($service.StartType)" -ForegroundColor White
        Write-Host ""
        
        # Also show the application status
        Write-Host "Application Status:" -ForegroundColor Cyan
        & python master_service_manager.py status
        
    } catch {
        Write-Host "Error checking service status: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Main script logic
switch ($Action.ToLower()) {
    "install" { Install-DBSBMService }
    "uninstall" { Uninstall-DBSBMService }
    "start" { Start-DBSBMService }
    "stop" { Stop-DBSBMService }
    "status" { Show-ServiceStatus }
    default { Show-Help }
}
