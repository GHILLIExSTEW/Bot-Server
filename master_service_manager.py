#!/usr/bin/env python3
"""
DBSBM Master Service Manager
Manages both Discord Bot (DBSBM) and Web Server (DBSBMWEB) services
Features:
- Runs indefinitely with automatic restart on failure
- Schedules restart on first Monday of every month
- Health monitoring and logging
- Process management with graceful shutdown
"""

import os
import sys
import time
import signal
import logging
import subprocess
import threading
import schedule
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import json
from typing import Optional, Dict, Any
import calendar

class MasterServiceManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.dbsbm_dir = self.base_dir / "DBSBM"
        self.dbsbmweb_dir = self.base_dir / "DBSBMWEB"
        self.log_dir = self.base_dir / "service_logs"
        self.pid_file = self.base_dir / "master_service.pid"
        self.status_file = self.base_dir / "master_service_status.json"
        
        # Ensure directories exist
        self.log_dir.mkdir(exist_ok=True)
        
        # Service configuration - BOTH DISCORD BOT AND WEB SERVER
        self.services = {
            "discord_bot": {
                "name": "Discord Bot (DBSBM)",
                "script": "main.py",
                "working_dir": str(self.dbsbm_dir / "bot"),
                "python_path": str(self.dbsbm_dir),
                "process": None,
                "pid": None,
                "status": "stopped",
                "restart_count": 0,
                "last_restart": None,
                "last_health_check": None,
                "consecutive_failures": 0
            },
            "web_server": {
                "name": "Web Server (DBSBMWEB)",
                "script": "flask_service.py",
                "working_dir": str(self.dbsbmweb_dir),
                "python_path": str(self.dbsbmweb_dir),
                "process": None,
                "pid": None,
                "status": "stopped",
                "restart_count": 0,
                "last_restart": None,
                "last_health_check": None,
                "consecutive_failures": 0
            },
            "web_proxy": {
                "name": "Web Proxy (Port 80)",
                "script": "port80_proxy.py",
                "working_dir": str(self.dbsbmweb_dir),
                "python_path": str(self.dbsbmweb_dir),
                "process": None,
                "pid": None,
                "status": "stopped",
                "restart_count": 0,
                "last_restart": None,
                "last_health_check": None,
                "consecutive_failures": 0
            }
        }
        
        self.running = False
        self.last_monthly_restart = None
        self.setup_logging()
        self.setup_scheduler()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        log_file = self.log_dir / f'master_service_{datetime.now().strftime("%Y%m%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('MasterServiceManager')
        
    def setup_scheduler(self):
        """Setup scheduled tasks"""
        # Schedule restart on first Monday of every month at 3 AM
        schedule.every().monday.at("03:00").do(self.check_monthly_restart)
        
    def check_monthly_restart(self):
        """Check if today is the first Monday of the month"""
        today = datetime.now()
        
        # Find the first Monday of this month
        first_day = today.replace(day=1)
        first_monday = first_day + timedelta(days=(7 - first_day.weekday()) % 7)
        
        # If today is the first Monday and we haven't restarted this month
        if (today.date() == first_monday.date() and 
            (self.last_monthly_restart is None or 
             self.last_monthly_restart.month != today.month or 
             self.last_monthly_restart.year != today.year)):
            
            self.logger.info("[SCHEDULE] Performing scheduled monthly restart (First Monday)")
            self.last_monthly_restart = today
            self.restart_all_services()
            
    def write_pid_file(self):
        """Write current process PID to file"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            self.logger.info(f"PID file written: {self.pid_file}")
        except Exception as e:
            self.logger.error(f"Failed to write PID file: {e}")
            
    def remove_pid_file(self):
        """Remove PID file"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                self.logger.info("PID file removed")
        except Exception as e:
            self.logger.error(f"Failed to remove PID file: {e}")
            
    def update_status(self):
        """Update service status file"""
        try:
            status_data = {
                "manager_pid": os.getpid(),
                "last_update": datetime.now().isoformat(),
                "last_monthly_restart": self.last_monthly_restart.isoformat() if self.last_monthly_restart else None,
                "services": {}
            }
            
            for service_name, service_info in self.services.items():
                status_data["services"][service_name] = {
                    "name": service_info["name"],
                    "status": service_info["status"],
                    "pid": service_info["pid"],
                    "restart_count": service_info["restart_count"],
                    "last_restart": service_info["last_restart"],
                    "last_health_check": service_info["last_health_check"],
                    "consecutive_failures": service_info["consecutive_failures"]
                }
                
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to update status file: {e}")
    
    def is_process_running(self, pid: int) -> bool:
        """Check if process with given PID is running"""
        try:
            return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
        except:
            return False
            
    def start_service(self, service_name: str) -> bool:
        """Start a specific service"""
        service = self.services[service_name]
        
        try:
            # Check if already running
            if service["pid"] and self.is_process_running(service["pid"]):
                self.logger.info(f"[OK] {service['name']} is already running (PID: {service['pid']})")
                service["status"] = "running"
                service["consecutive_failures"] = 0
                return True
                
            # Verify script exists
            script_path = Path(service["working_dir"]) / service["script"]
            if not script_path.exists():
                self.logger.error(f"[ERROR] Service script not found: {script_path}")
                service["status"] = "error"
                service["consecutive_failures"] += 1
                return False
                
            self.logger.info(f"[START] Starting {service['name']}...")
            
            # Setup environment
            env = os.environ.copy()
            env["PYTHONPATH"] = service["python_path"]
            
            # Start the service
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=service["working_dir"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Capture both stdout and stderr
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
                text=True,
                bufsize=1
            )
            
            # Give it a moment to start and capture initial output
            time.sleep(5)
            
            if process.poll() is None:  # Process is still running
                service["process"] = process
                service["pid"] = process.pid
                service["status"] = "running"
                service["restart_count"] += 1
                service["last_restart"] = datetime.now().isoformat()
                service["consecutive_failures"] = 0
                
                self.logger.info(f"[OK] {service['name']} started successfully (PID: {process.pid})")
                return True
            else:
                # Process terminated, get output
                try:
                    output, _ = process.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    output = "Process terminated without output"
                
                self.logger.error(f"[ERROR] {service['name']} failed to start:")
                self.logger.error(f"Exit code: {process.returncode}")
                if output:
                    self.logger.error(f"OUTPUT: {output}")
                    
                service["status"] = "error"
                service["consecutive_failures"] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to start {service['name']}: {e}")
            service["status"] = "error"
            service["consecutive_failures"] += 1
            return False
            
    def stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        service = self.services[service_name]
        
        try:
            if service["process"] and service["process"].poll() is None:
                self.logger.info(f"[STOP] Stopping {service['name']} (PID: {service['pid']})...")
                
                # Graceful shutdown
                if os.name == 'nt':
                    service["process"].terminate()
                else:
                    service["process"].send_signal(signal.SIGTERM)
                    
                # Wait for graceful shutdown
                try:
                    service["process"].wait(timeout=15)
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"[WARNING] Force killing {service['name']}")
                    service["process"].kill()
                    service["process"].wait()
                    
                service["process"] = None
                service["pid"] = None
                service["status"] = "stopped"
                self.logger.info(f"[OK] {service['name']} stopped successfully")
                return True
            else:
                self.logger.info(f"[INFO] {service['name']} is not running")
                service["status"] = "stopped"
                service["pid"] = None
                return True
                
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to stop {service['name']}: {e}")
            return False
            
    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        self.logger.info(f"[RESTART] Restarting {self.services[service_name]['name']}...")
        self.stop_service(service_name)
        time.sleep(2)
        return self.start_service(service_name)
        
    def check_service_health(self, service_name: str) -> bool:
        """Check if service is healthy"""
        service = self.services[service_name]
        current_time = datetime.now().isoformat()
        service["last_health_check"] = current_time
        
        if not service["pid"]:
            return False
            
        if not self.is_process_running(service["pid"]):
            self.logger.warning(f"[WARNING] {service['name']} process died (PID: {service['pid']})")
            service["status"] = "died"
            service["pid"] = None
            service["process"] = None
            service["consecutive_failures"] += 1
            return False
            
        service["status"] = "running"
        service["consecutive_failures"] = 0
        return True
        
    def monitor_services(self):
        """Monitor services and restart if needed"""
        while self.running:
            try:
                # Check scheduled tasks
                schedule.run_pending()
                
                # Monitor each service
                for service_name, service_info in self.services.items():
                    if not self.check_service_health(service_name):
                        if service_info["status"] == "died":
                            # Exponential backoff for consecutive failures
                            if service_info["consecutive_failures"] <= 3:
                                wait_time = 2 ** service_info["consecutive_failures"]
                                self.logger.info(f"[RESTART] Restarting {service_info['name']} after {wait_time}s delay (failure #{service_info['consecutive_failures']})")
                                time.sleep(wait_time)
                                self.start_service(service_name)
                            else:
                                self.logger.error(f"[ERROR] {service_info['name']} has failed {service_info['consecutive_failures']} times. Waiting longer before retry.")
                                time.sleep(60)  # Wait 1 minute for severely failing services
                
                self.update_status()
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"[ERROR] Error in service monitoring: {e}")
                time.sleep(30)
                
    def start_all_services(self):
        """Start all services"""
        self.logger.info("[START] Starting DBSBM Master Service Manager")
        self.logger.info("=" * 80)
        
        success_count = 0
        for service_name in self.services:
            if self.start_service(service_name):
                success_count += 1
                
        self.logger.info(f"[STATUS] Started {success_count}/{len(self.services)} services")
        self.update_status()
        
        if success_count > 0:
            self.logger.info("[SERVICES] Services are now running:")
            if "discord_bot" in self.services and self.services["discord_bot"]["status"] == "running":
                self.logger.info("   [BOT] Discord Bot: Online")
            if "web_server" in self.services and self.services["web_server"]["status"] == "running":
                self.logger.info("   [WEB] Web Server: http://localhost:5000")
            if "web_proxy" in self.services and self.services["web_proxy"]["status"] == "running":
                self.logger.info("   [PROXY] Web Proxy: http://localhost")
            self.logger.info("=" * 80)
            
        return success_count == len(self.services)
        
    def stop_all_services(self):
        """Stop all services"""
        self.logger.info("[STOP] Stopping all services...")
        
        for service_name in self.services:
            self.stop_service(service_name)
            
        self.update_status()
        self.logger.info("[OK] All services stopped")
        
    def restart_all_services(self):
        """Restart all services"""
        self.logger.info("[RESTART] Restarting all services...")
        self.stop_all_services()
        time.sleep(5)
        self.start_all_services()
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"📡 Received signal {signum}, shutting down...")
        self.running = False
        self.stop_all_services()
        self.remove_pid_file()
        sys.exit(0)
        
    def run(self):
        """Main service manager loop"""
        try:
            # Setup signal handlers
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            self.write_pid_file()
            self.running = True
            
            # Start all services
            if not self.start_all_services():
                self.logger.warning("[WARNING] Some services failed to start, but continuing with monitoring...")
                
            # Start monitoring in background
            monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
            monitor_thread.start()
            
            self.logger.info("[INFO] Master service manager is now running indefinitely.")
            self.logger.info("   • Auto-restart on failure: [ENABLED]")
            self.logger.info("   • Monthly restart: First Monday @ 3 AM")
            self.logger.info("   • Health monitoring: Every 30 seconds")
            self.logger.info("   • Press Ctrl+C to stop")
            self.logger.info("=" * 80)
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("📡 Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"[ERROR] Master service manager error: {e}")
        finally:
            self.stop_all_services()
            self.remove_pid_file()
            
    def status(self):
        """Show current service status"""
        print("\n" + "=" * 80)
        print("[STATUS] DBSBM Master Service Manager Status")
        print("=" * 80)
        
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    status_data = json.load(f)
                    
                print(f"Manager PID: {status_data.get('manager_pid', 'Unknown')}")
                print(f"Last Update: {status_data.get('last_update', 'Unknown')}")
                print(f"Last Monthly Restart: {status_data.get('last_monthly_restart', 'Never')}")
                print("\n[SERVICES] Services:")
                
                for service_name, service_info in status_data.get('services', {}).items():
                    if service_info['status'] == 'running':
                        status_icon = "[RUNNING]"
                    elif service_info['status'] == 'error':
                        status_icon = "[ERROR]"
                    else:
                        status_icon = "[UNKNOWN]"
                        
                    print(f"  {status_icon} {service_info['name']}")
                    print(f"     Status: {service_info['status']}")
                    print(f"     PID: {service_info['pid'] or 'N/A'}")
                    print(f"     Restarts: {service_info['restart_count']}")
                    print(f"     Failures: {service_info['consecutive_failures']}")
                    print(f"     Last Restart: {service_info['last_restart'] or 'Never'}")
                    print(f"     Last Health Check: {service_info['last_health_check'] or 'Never'}")
                    print()
                    
                # Show next monthly restart
                today = datetime.now()
                first_day_next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
                next_first_monday = first_day_next_month + timedelta(days=(7 - first_day_next_month.weekday()) % 7)
                print(f"[SCHEDULE] Next Monthly Restart: {next_first_monday.strftime('%Y-%m-%d at 3:00 AM')}")
                    
            except Exception as e:
                print(f"[ERROR] Error reading status: {e}")
        else:
            print("[ERROR] No status file found. Master service manager may not be running.")
            
        print("=" * 80)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python master_service_manager.py [start|stop|restart|status]")
        print("Commands:")
        print("  start   - Start master service manager and all services")
        print("  stop    - Stop all services and master service manager")
        print("  restart - Restart all services")
        print("  status  - Show current service status")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    manager = MasterServiceManager()
    
    if command == "start":
        manager.run()
    elif command == "stop":
        manager.stop_all_services()
    elif command == "restart":
        manager.restart_all_services()
    elif command == "status":
        manager.status()
    else:
        print(f"[ERROR] Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
