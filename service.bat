@echo off
REM DBSBM Master Service Manager
REM Manages Discord Bot and Web Server indefinitely

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

if "%1"=="" (
    echo.
    echo ============================================================
    echo   DBSBM Master Service Manager
    echo ============================================================
    echo.
    echo Usage: %0 [command]
    echo.
    echo Commands:
    echo   start   - Start master service manager ^(runs indefinitely^)
    echo   stop    - Stop all services
    echo   restart - Restart all services
    echo   status  - Show current service status
    echo   logs    - Show recent service logs
    echo.
    echo Features:
    echo   * Runs Discord Bot ^(DBSBM^) and Web Server ^(DBSBMWEB^)
    echo   * Auto-restart on failure with exponential backoff
    echo   * Monthly restart on first Monday at 3 AM
    echo   * Health monitoring every 30 seconds
    echo   * Comprehensive logging and status tracking
    echo.
    echo Examples:
    echo   %0 start     ^(starts and runs indefinitely^)
    echo   %0 status    ^(check if services are running^)
    echo.
    goto :eof
)

if /i "%1"=="start" (
    echo ============================================================
    echo   Starting DBSBM Master Service Manager
    echo ============================================================
    echo.
    echo Starting services:
    echo   Discord Bot: DBSBM\bot\main.py
    echo   Web Server:  DBSBMWEB\flask_service.py  
    echo   Web Proxy:   DBSBMWEB\port80_proxy.py
    echo.
    echo This will run indefinitely until stopped with Ctrl+C
    echo.
    python master_service_manager.py start
) else if /i "%1"=="stop" (
    echo Stopping all DBSBM services...
    python master_service_manager.py stop
) else if /i "%1"=="restart" (
    echo Restarting all DBSBM services...
    python master_service_manager.py restart
) else if /i "%1"=="status" (
    python master_service_manager.py status
) else if /i "%1"=="logs" (
    echo.
    echo Recent master service logs:
    echo ============================
    if exist "service_logs\master_service_*.log" (
        for /f %%i in ('dir /b /o-d "service_logs\master_service_*.log" 2^>nul') do (
            echo.
            echo Latest log file: %%i
            echo.
            type "service_logs\%%i" | findstr /v "GET /" | tail -20
            goto :done_logs
        )
    ) else (
        echo No log files found.
    )
    :done_logs
) else (
    echo Unknown command: %1
    echo Use "%0" without arguments to see usage help.
)
