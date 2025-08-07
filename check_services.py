import psutil
import json
import sys

# Read the status file
try:
    with open('master_service_status.json', 'r') as f:
        status = json.load(f)
    
    print("=== Process Status Check ===")
    print(f"Master PID: {status['manager_pid']}")
    
    # Check if master process is running
    try:
        master_proc = psutil.Process(status['manager_pid'])
        print(f"Master Process: RUNNING ({master_proc.name()})")
    except psutil.NoSuchProcess:
        print("Master Process: NOT RUNNING")
    
    print("\n=== Service Status ===")
    for service_name, service_info in status['services'].items():
        pid = service_info['pid']
        print(f"{service_info['name']} (PID: {pid}): ", end="")
        
        try:
            proc = psutil.Process(pid)
            if proc.is_running():
                print("RUNNING")
            else:
                print("NOT RUNNING")
        except psutil.NoSuchProcess:
            print("PROCESS NOT FOUND")
        except Exception as e:
            print(f"ERROR: {e}")
            
    print("\n=== Port Status ===")
    # Check ports
    for conn in psutil.net_connections():
        if conn.laddr.port in [5000, 80] and conn.status == 'LISTEN':
            print(f"Port {conn.laddr.port}: LISTENING")
            
except Exception as e:
    print(f"Error: {e}")
