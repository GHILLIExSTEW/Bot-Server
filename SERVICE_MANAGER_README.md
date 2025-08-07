# 🎰 DBSBM Master Service Manager

A comprehensive service management system for the DBSBM (Discord Bot Sports Betting Manager) application that runs both the Discord bot and web server indefinitely with automatic restart capabilities and scheduled maintenance.

## 🚀 Features

- **Multi-Service Management**: Manages Discord Bot (DBSBM) and Web Server (DBSBMWEB) simultaneously
- **Automatic Restart**: Restarts failed services with exponential backoff strategy
- **Scheduled Maintenance**: Automatically restarts all services on the first Monday of every month at 3 AM
- **Health Monitoring**: Monitors service health every 30 seconds
- **Comprehensive Logging**: Detailed logs with daily rotation
- **Process Management**: Graceful shutdown with proper signal handling
- **Windows Service Support**: Can be installed as a Windows service for persistent operation

## 📁 File Structure

```
Bot+Server/
├── master_service_manager.py     # Main service manager
├── service.bat                   # Windows batch script
├── service.ps1                   # PowerShell management script
├── install_service.ps1           # Windows service installer
├── service_logs/                 # Log directory (auto-created)
├── DBSBM/                        # Discord bot directory
│   └── bot/
│       └── main.py              # Discord bot entry point
└── DBSBMWEB/                     # Web server directory
    ├── flask_service.py         # Flask web server
    └── port80_proxy.py          # HTTP proxy service
```

## 🛠️ Installation

### Prerequisites

```bash
pip install schedule psutil
```

### Quick Start

1. **Start Services** (runs indefinitely):
   ```bash
   python master_service_manager.py start
   ```

2. **Check Status**:
   ```bash
   python master_service_manager.py status
   ```

3. **Stop Services**:
   ```bash
   python master_service_manager.py stop
   ```

### Using Convenience Scripts

**Windows Batch File:**
```cmd
service.bat start    # Start and run indefinitely
service.bat status   # Check status
service.bat stop     # Stop all services
service.bat logs     # View recent logs
```

**PowerShell:**
```powershell
.\service.ps1 start    # Start and run indefinitely
.\service.ps1 status   # Check status
.\service.ps1 stop     # Stop all services
.\service.ps1 logs     # View recent logs
```

## 🪟 Windows Service Installation

For truly persistent operation (survives reboots, runs in background):

### Install as Windows Service

```powershell
# Run PowerShell as Administrator
.\install_service.ps1 install
.\install_service.ps1 start
```

### Manage Windows Service

```powershell
.\install_service.ps1 status     # Check service status
.\install_service.ps1 stop       # Stop service
.\install_service.ps1 start      # Start service
.\install_service.ps1 uninstall  # Remove service
```

## 📊 Service Monitoring

### Managed Services

1. **Discord Bot (DBSBM)**
   - Script: `DBSBM/bot/main.py`
   - Manages Discord bot connections and commands
   - Auto-restart on crash or connection loss

2. **Web Server (Flask)**
   - Script: `DBSBMWEB/flask_service.py`
   - Serves web interface on port 5000
   - Handles API endpoints and dashboard

3. **Web Proxy (Port 80)**
   - Script: `DBSBMWEB/port80_proxy.py`
   - Forwards HTTP traffic from port 80 to Flask
   - Enables standard web access

### Health Monitoring

- **Check Interval**: Every 30 seconds
- **Restart Strategy**: Exponential backoff for consecutive failures
- **Failure Threshold**: Up to 3 immediate restarts, then 1-minute delays
- **Process Validation**: Verifies PID existence and process health

### Scheduled Maintenance

- **Monthly Restart**: First Monday of every month at 3:00 AM
- **Purpose**: Clear memory leaks, apply updates, refresh connections
- **Graceful**: 15-second graceful shutdown before force kill

## 📋 Logging

### Log Files

- **Location**: `service_logs/`
- **Format**: `master_service_YYYYMMDD.log`
- **Rotation**: Daily automatic rotation
- **Retention**: 30 days (configurable)

### Log Levels

- **INFO**: Normal operations, service starts/stops
- **WARNING**: Service failures, restart attempts
- **ERROR**: Critical errors, startup failures

### Viewing Logs

```bash
# Recent logs
service.bat logs
# or
.\service.ps1 logs

# Full log file
type service_logs\master_service_20250804.log
```

## ⚙️ Configuration

### Service Configuration

Edit `master_service_manager.py` to modify:

```python
self.services = {
    "discord_bot": {
        "name": "Discord Bot (DBSBM)",
        "script": "main.py",
        "working_dir": str(self.dbsbm_dir / "bot"),
        # ... other settings
    },
    # ... other services
}
```

### Monitoring Settings

```python
# Health check interval (seconds)
time.sleep(30)  # Line ~375

# Monthly restart schedule
schedule.every().monday.at("03:00").do(self.check_monthly_restart)
```

### Restart Behavior

```python
# Exponential backoff for failures
wait_time = 2 ** service_info["consecutive_failures"]

# Maximum consecutive failures before extended delay
if service_info["consecutive_failures"] <= 3:
    # Normal restart
else:
    # Extended delay (60 seconds)
```

## 🔧 Troubleshooting

### Common Issues

1. **Services Won't Start**
   ```bash
   # Check if scripts exist
   python master_service_manager.py status
   
   # Verify Python path
   where python
   
   # Check script permissions
   ```

2. **Frequent Restarts**
   ```bash
   # Check service logs
   service.bat logs
   
   # Verify dependencies
   pip list | grep -E "(schedule|psutil)"
   ```

3. **Monthly Restart Not Working**
   ```bash
   # Check current date calculation
   python -c "from datetime import datetime, timedelta; print(datetime.now())"
   ```

### Manual Service Control

```bash
# Start individual services
python DBSBM/bot/main.py
python DBSBMWEB/flask_service.py
python DBSBMWEB/port80_proxy.py

# Check processes
tasklist | findstr python

# Kill processes
taskkill /F /IM python.exe
```

## 📈 Status Monitoring

### Status File

Location: `master_service_status.json`

Contains:
- Manager PID
- Service status and PIDs
- Restart counts and timestamps
- Health check information
- Last monthly restart date

### Status Output Example

```
📊 DBSBM Master Service Manager Status
================================================================================
Manager PID: 1234
Last Update: 2025-08-04T12:00:00.000000
Last Monthly Restart: 2025-08-05T03:00:00.000000

🎯 Services:
  🟢 Discord Bot (DBSBM)
     Status: running
     PID: 5678
     Restarts: 1
     Failures: 0
     Last Restart: 2025-08-04T12:00:00.000000
     
📅 Next Monthly Restart: 2025-09-02 at 3:00 AM
```

## 🔄 Restart Scenarios

### Automatic Restarts

1. **Process Death**: Service process crashes or exits
2. **Health Check Failure**: Process becomes unresponsive
3. **Scheduled Maintenance**: Monthly restart on first Monday
4. **Manual Restart**: User-initiated restart command

### Restart Sequence

1. **Graceful Shutdown**: Send SIGTERM (15-second timeout)
2. **Force Kill**: Send SIGKILL if graceful fails
3. **Cleanup**: Clear process references
4. **Restart**: Start new process with fresh environment
5. **Verification**: Confirm successful startup

## 🛡️ Security Considerations

- **Process Isolation**: Each service runs in separate process
- **Resource Limits**: Monitor memory and CPU usage
- **Log Security**: Ensure log files have appropriate permissions
- **Service Account**: Consider running Windows service under dedicated account

## 📞 Support

For issues or questions:

1. Check the logs: `service.bat logs`
2. Verify service status: `service.bat status`
3. Review this documentation
4. Check individual service logs in respective directories

---

**Last Updated**: August 4, 2025  
**Version**: 1.0.0  
**Compatibility**: Windows 10/11, Python 3.7+
