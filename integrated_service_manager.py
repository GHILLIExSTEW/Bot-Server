#!/usr/bin/env python3
"""
Integrated Service Manager for Discord Bot and Web Services
Standalone application with GUI interface and tabulated console output
"""

import os
import sys
import json
import time
import threading
import subprocess
import signal
import logging
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import queue


class ServiceManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.services = {
            'discord_bot': {
                'name': 'Discord Bot',
                'command': [sys.executable, 'DBSBM/bot/main.py'],
                'cwd': str(self.base_dir),
                'process': None,
                'status': 'Stopped',
                'last_output': '',
                'output_queue': queue.Queue(),
                'auto_restart': True
            },
            'flask_server': {
                'name': 'Flask Web Server',
                'command': [sys.executable, 'DBSBMWEB/flask_service.py'],
                'cwd': str(self.base_dir),
                'process': None,
                'status': 'Stopped',
                'last_output': '',
                'output_queue': queue.Queue(),
                'auto_restart': True
            },
            'port_proxy': {
                'name': 'Port 80 Proxy',
                'command': [sys.executable, 'DBSBMWEB/improved_port80_proxy.py'],
                'cwd': str(self.base_dir),
                'process': None,
                'status': 'Stopped',
                'last_output': '',
                'output_queue': queue.Queue(),
                'auto_restart': True
            }
        }
        
        self.status_file = self.base_dir / 'integrated_service_status.json'
        self.log_dir = self.base_dir / 'service_logs'
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # GUI components
        self.root = None
        self.service_frames = {}
        self.status_labels = {}
        self.output_texts = {}
        self.control_buttons = {}
        
        # Control flags
        self.running = True
        self.monitoring_thread = None
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.log_dir / f'integrated_manager_{datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ServiceManager')
        
    def save_status(self):
        """Save current service status to file"""
        status_data = {
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        for service_id, service in self.services.items():
            status_data['services'][service_id] = {
                'name': service['name'],
                'status': service['status'],
                'pid': service['process'].pid if service['process'] else None,
                'auto_restart': service['auto_restart']
            }
        
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save status: {e}")
    
    def validate_services(self):
        """Validate that all service files exist and are accessible"""
        validation_results = {}
        
        for service_id, service in self.services.items():
            results = {
                'name': service['name'],
                'command_file_exists': False,
                'working_directory_exists': False,
                'python_executable': sys.executable,
                'issues': []
            }
            
            # Check working directory
            cwd_path = Path(service['cwd'])
            if cwd_path.exists():
                results['working_directory_exists'] = True
            else:
                results['issues'].append(f"Working directory not found: {cwd_path}")
            
            # Check command file
            if len(service['command']) > 1:
                command_file = cwd_path / service['command'][1]
                if command_file.exists():
                    results['command_file_exists'] = True
                else:
                    results['issues'].append(f"Command file not found: {command_file}")
            
            validation_results[service_id] = results
        
        return validation_results
    
    def print_validation_report(self):
        """Print a validation report to help debug issues"""
        print("\n" + "="*60)
        print("SERVICE VALIDATION REPORT")
        print("="*60)
        
        results = self.validate_services()
        
        for service_id, result in results.items():
            print(f"\n{result['name']}:")
            print(f"  Working Directory: {'✓' if result['working_directory_exists'] else '✗'}")
            print(f"  Command File:      {'✓' if result['command_file_exists'] else '✗'}")
            print(f"  Python Executable: {result['python_executable']}")
            
            if result['issues']:
                print("  Issues:")
                for issue in result['issues']:
                    print(f"    - {issue}")
            else:
                print("  Status: All checks passed ✓")
        
        print("\n" + "="*60)
        
        # Test Python import capabilities
        print("PYTHON ENVIRONMENT TEST")
        print("="*60)
        
        test_imports = ['discord', 'flask', 'asyncio', 'asyncpg']
        for module in test_imports:
            try:
                __import__(module)
                print(f"  {module}: ✓ Available")
            except ImportError:
                print(f"  {module}: ✗ Missing (pip install {module})")
        
        print("="*60)
    
    def load_status(self):
        """Load previous service status"""
        if not self.status_file.exists():
            return
        
        try:
            with open(self.status_file, 'r') as f:
                status_data = json.load(f)
            
            for service_id, service_status in status_data.get('services', {}).items():
                if service_id in self.services:
                    self.services[service_id]['auto_restart'] = service_status.get('auto_restart', True)
        except Exception as e:
            self.logger.error(f"Failed to load status: {e}")
    
    def start_service(self, service_id):
        """Start a specific service"""
        service = self.services[service_id]
        
        if service['process'] and service['process'].poll() is None:
            self.logger.warning(f"{service['name']} is already running")
            return False
        
        try:
            self.logger.info(f"Starting {service['name']}...")
            
            # Check if the command file exists
            command_path = Path(service['cwd']) / service['command'][1]
            if not command_path.exists():
                error_msg = f"Command file not found: {command_path}"
                self.logger.error(error_msg)
                service['status'] = f'Failed: File not found'
                service['output_queue'].put(error_msg)
                self.update_service_display(service_id)
                return False
            
            # Create log file for this service
            log_file = self.log_dir / f'{service_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            
            # Add environment variables if needed
            env = os.environ.copy()
            
            service['process'] = subprocess.Popen(
                service['command'],
                cwd=service['cwd'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            service['status'] = 'Starting'
            self.update_service_display(service_id)
            
            # Start output monitoring thread for this service
            output_thread = threading.Thread(
                target=self.monitor_service_output,
                args=(service_id, log_file),
                daemon=True
            )
            output_thread.start()
            
            # Check if process is still running after a brief moment
            def check_startup_status():
                time.sleep(3)  # Wait 3 seconds
                if service['process'] and service['process'].poll() is None:
                    # Process is still running, likely successful
                    if service['status'] == 'Starting':
                        service['status'] = 'Running'
                        self.update_service_display(service_id)
            
            startup_check_thread = threading.Thread(target=check_startup_status, daemon=True)
            startup_check_thread.start()
            
            self.logger.info(f"{service['name']} started with PID {service['process'].pid}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to start {service['name']}: {e}"
            self.logger.error(error_msg)
            service['status'] = f'Failed: {str(e)}'
            service['output_queue'].put(error_msg)
            self.update_service_display(service_id)
            return False
    
    def stop_service(self, service_id):
        """Stop a specific service"""
        service = self.services[service_id]
        
        if not service['process'] or service['process'].poll() is not None:
            service['status'] = 'Stopped'
            self.update_service_display(service_id)
            return True
        
        try:
            self.logger.info(f"Stopping {service['name']}...")
            service['status'] = 'Stopping'
            self.update_service_display(service_id)
            
            # Graceful shutdown
            service['process'].terminate()
            
            # Wait for graceful shutdown
            try:
                service['process'].wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Force killing {service['name']}")
                service['process'].kill()
                service['process'].wait()
            
            service['process'] = None
            service['status'] = 'Stopped'
            self.update_service_display(service_id)
            
            self.logger.info(f"{service['name']} stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop {service['name']}: {e}")
            return False
    
    def restart_service(self, service_id):
        """Restart a specific service"""
        self.stop_service(service_id)
        time.sleep(2)  # Brief pause between stop and start
        return self.start_service(service_id)
    
    def monitor_service_output(self, service_id, log_file):
        """Monitor output from a service process"""
        service = self.services[service_id]
        
        try:
            with open(log_file, 'w') as log_f:
                while service['process'] and service['process'].poll() is None:
                    try:
                        # Read both stdout and stderr
                        stdout_line = service['process'].stdout.readline()
                        stderr_line = service['process'].stderr.readline()
                        
                        if stdout_line:
                            # Write to log file
                            log_f.write(f"STDOUT: {stdout_line}")
                            log_f.flush()
                            
                            # Add to output queue for GUI display
                            service['output_queue'].put(f"OUT: {stdout_line.strip()}")
                            service['last_output'] = stdout_line.strip()
                            
                            # Update status based on output
                            if any(keyword in stdout_line.lower() for keyword in ['ready', 'started', 'listening', 'connected', 'logged in']):
                                service['status'] = 'Running'
                                self.update_service_display(service_id)
                            elif any(keyword in stdout_line.lower() for keyword in ['error', 'failed', 'exception']):
                                service['status'] = f'Error: {stdout_line.strip()[:50]}...'
                                self.update_service_display(service_id)
                        
                        if stderr_line:
                            # Write to log file
                            log_f.write(f"STDERR: {stderr_line}")
                            log_f.flush()
                            
                            # Add to output queue for GUI display
                            service['output_queue'].put(f"ERR: {stderr_line.strip()}")
                            
                        if not stdout_line and not stderr_line:
                            time.sleep(0.1)
                            
                    except Exception as e:
                        error_msg = f"Error reading output from {service['name']}: {e}"
                        self.logger.error(error_msg)
                        service['output_queue'].put(error_msg)
                        break
        
        except Exception as e:
            error_msg = f"Error monitoring {service['name']}: {e}"
            self.logger.error(error_msg)
            service['output_queue'].put(error_msg)
        
        # Process has ended - capture any remaining output
        if service['process']:
            return_code = service['process'].poll()
            if return_code is not None:
                # Capture any remaining stderr
                try:
                    remaining_stdout, remaining_stderr = service['process'].communicate(timeout=5)
                    if remaining_stdout:
                        service['output_queue'].put(f"FINAL OUT: {remaining_stdout.strip()}")
                    if remaining_stderr:
                        service['output_queue'].put(f"FINAL ERR: {remaining_stderr.strip()}")
                        stderr_output = remaining_stderr.strip()
                    else:
                        stderr_output = "No additional error details"
                except subprocess.TimeoutExpired:
                    stderr_output = "Timeout reading final output"
                except Exception as e:
                    stderr_output = f"Error reading final output: {e}"
                
                if return_code == 0:
                    service['status'] = 'Stopped'
                else:
                    service['status'] = f'Crashed (exit code: {return_code})'
                    error_msg = f"{service['name']} crashed with return code {return_code}. Error: {stderr_output}"
                    self.logger.error(error_msg)
                    service['output_queue'].put(error_msg)
                
                self.update_service_display(service_id)
                
                # Auto-restart if enabled
                if service['auto_restart'] and return_code != 0:
                    restart_msg = f"Auto-restarting {service['name']} in 5 seconds..."
                    self.logger.info(restart_msg)
                    service['output_queue'].put(restart_msg)
                    time.sleep(5)
                    self.start_service(service_id)
    
    def create_gui(self):
        """Create the GUI interface"""
        self.root = tk.Tk()
        self.root.title("DBSBM Service Manager")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set application icon
        try:
            # Try to use converted .ico file first
            ico_path = self.base_dir / "dbsbm_icon.ico"
            webp_path = self.base_dir / "StaticFiles" / "DBSBMWEB" / "static" / "favicon.webp"
            
            if ico_path.exists():
                self.root.iconbitmap(str(ico_path))
            elif webp_path.exists():
                # Try to convert webp to ico
                try:
                    from PIL import Image
                    img = Image.open(webp_path)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img = img.resize((32, 32), Image.Resampling.LANCZOS)
                    img.save(ico_path, format='ICO')
                    self.root.iconbitmap(str(ico_path))
                    self.logger.info("App icon set successfully")
                except ImportError:
                    self.logger.warning("Pillow not available for icon conversion")
                except Exception as e:
                    self.logger.warning(f"Could not convert icon: {e}")
            else:
                self.logger.warning("No icon file found")
        except Exception as e:
            self.logger.warning(f"Error setting app icon: {e}")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="DBSBM Integrated Service Manager", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Global controls
        global_frame = ttk.LabelFrame(main_frame, text="Global Controls", padding="10")
        global_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(global_frame, text="Start All Services", 
                  command=self.start_all_services).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(global_frame, text="Stop All Services", 
                  command=self.stop_all_services).grid(row=0, column=1, padx=5)
        ttk.Button(global_frame, text="Restart All Services", 
                  command=self.restart_all_services).grid(row=0, column=2, padx=5)
        ttk.Button(global_frame, text="Refresh Status", 
                  command=self.refresh_all_status).grid(row=0, column=3, padx=5)
        ttk.Button(global_frame, text="Validate Services", 
                  command=self.show_validation_report).grid(row=0, column=4, padx=5)
        ttk.Button(global_frame, text="Save Status", 
                  command=self.save_status).grid(row=0, column=5, padx=(5, 0))
        
        # Service panels
        services_frame = ttk.Frame(main_frame)
        services_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        services_frame.columnconfigure(0, weight=1)
        services_frame.rowconfigure(0, weight=1)
        
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(services_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        for i, (service_id, service) in enumerate(self.services.items()):
            self.create_service_tab(notebook, service_id, service)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_bar = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)
        
        # Start GUI update thread
        self.start_gui_update_thread()
    
    def create_service_tab(self, notebook, service_id, service):
        """Create a tab for a specific service"""
        # Create tab frame
        tab_frame = ttk.Frame(notebook, padding="10")
        notebook.add(tab_frame, text=service['name'])
        
        # Configure grid
        tab_frame.columnconfigure(1, weight=1)
        tab_frame.rowconfigure(2, weight=1)
        
        # Service info frame
        info_frame = ttk.LabelFrame(tab_frame, text="Service Information", padding="10")
        info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(info_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=service['name']).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(info_frame, text="Status:").grid(row=1, column=0, sticky=tk.W)
        status_label = ttk.Label(info_frame, text=service['status'])
        status_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        self.status_labels[service_id] = status_label
        
        ttk.Label(info_frame, text="Command:").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=' '.join(service['command'])).grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Control frame
        control_frame = ttk.LabelFrame(tab_frame, text="Controls", padding="10")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        start_btn = ttk.Button(control_frame, text="Start", 
                              command=lambda: self.start_service(service_id))
        start_btn.grid(row=0, column=0, padx=(0, 5))
        
        stop_btn = ttk.Button(control_frame, text="Stop", 
                             command=lambda: self.stop_service(service_id))
        stop_btn.grid(row=0, column=1, padx=5)
        
        restart_btn = ttk.Button(control_frame, text="Restart", 
                                command=lambda: self.restart_service(service_id))
        restart_btn.grid(row=0, column=2, padx=5)
        
        # Auto-restart checkbox
        auto_restart_var = tk.BooleanVar(value=service['auto_restart'])
        auto_restart_cb = ttk.Checkbutton(control_frame, text="Auto-restart on crash", 
                                         variable=auto_restart_var,
                                         command=lambda: self.toggle_auto_restart(service_id, auto_restart_var.get()))
        auto_restart_cb.grid(row=0, column=3, padx=(10, 0))
        
        self.control_buttons[service_id] = {
            'start': start_btn,
            'stop': stop_btn,
            'restart': restart_btn
        }
        
        # Output frame
        output_frame = ttk.LabelFrame(tab_frame, text="Console Output", padding="10")
        output_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Output text with scrollbar
        output_text = scrolledtext.ScrolledText(output_frame, height=20, width=80)
        output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.output_texts[service_id] = output_text
        
        # Clear output button
        ttk.Button(output_frame, text="Clear Output", 
                  command=lambda: self.clear_output(service_id)).grid(row=1, column=0, pady=(5, 0))
    
    def update_service_display(self, service_id):
        """Update the display for a specific service"""
        if service_id in self.status_labels:
            service = self.services[service_id]
            self.status_labels[service_id].config(text=service['status'])
            
            # Color code the status
            if service['status'] == 'Running':
                self.status_labels[service_id].config(foreground='green')
            elif service['status'] == 'Stopped':
                self.status_labels[service_id].config(foreground='gray')
            elif service['status'] in ['Starting', 'Stopping']:
                self.status_labels[service_id].config(foreground='orange')
            elif service['status'] in ['Failed', 'Crashed']:
                self.status_labels[service_id].config(foreground='red')
    
    def start_gui_update_thread(self):
        """Start thread to update GUI with service output"""
        def update_gui():
            while self.running:
                try:
                    for service_id, service in self.services.items():
                        # Update output text
                        try:
                            while True:
                                line = service['output_queue'].get_nowait()
                                if service_id in self.output_texts:
                                    output_text = self.output_texts[service_id]
                                    output_text.insert(tk.END, line + '\n')
                                    output_text.see(tk.END)
                                    
                                    # Limit output text length
                                    if output_text.index(tk.END).split('.')[0] > '1000':
                                        output_text.delete('1.0', '100.0')
                        except queue.Empty:
                            pass
                    
                    # Update status bar
                    running_count = sum(1 for s in self.services.values() if s['status'] == 'Running')
                    total_count = len(self.services)
                    self.status_bar.config(text=f"Services Running: {running_count}/{total_count}")
                    
                    time.sleep(0.5)
                except Exception as e:
                    self.logger.error(f"GUI update error: {e}")
        
        update_thread = threading.Thread(target=update_gui, daemon=True)
        update_thread.start()
    
    def toggle_auto_restart(self, service_id, enabled):
        """Toggle auto-restart for a service"""
        self.services[service_id]['auto_restart'] = enabled
        self.logger.info(f"Auto-restart {'enabled' if enabled else 'disabled'} for {self.services[service_id]['name']}")
    
    def clear_output(self, service_id):
        """Clear output text for a service"""
        if service_id in self.output_texts:
            self.output_texts[service_id].delete('1.0', tk.END)
    
    def start_all_services(self):
        """Start all services"""
        for service_id in self.services:
            self.start_service(service_id)
    
    def stop_all_services(self):
        """Stop all services"""
        for service_id in self.services:
            self.stop_service(service_id)
    
    def restart_all_services(self):
        """Restart all services"""
        for service_id in self.services:
            self.restart_service(service_id)
    
    def refresh_all_status(self):
        """Refresh the status of all services"""
        for service_id, service in self.services.items():
            if service['process']:
                poll_result = service['process'].poll()
                if poll_result is None:
                    # Process is still running
                    service['status'] = 'Running'
                else:
                    # Process has ended
                    if poll_result == 0:
                        service['status'] = 'Stopped'
                    else:
                        service['status'] = f'Crashed (exit code: {poll_result})'
                    service['process'] = None
            else:
                service['status'] = 'Stopped'
            
            self.update_service_display(service_id)
        
        self.logger.info("Status refreshed for all services")
    
    def show_validation_report(self):
        """Show validation report in a popup window"""
        report_window = tk.Toplevel(self.root)
        report_window.title("Service Validation Report")
        report_window.geometry("800x600")
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(report_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Generate and display report
        results = self.validate_services()
        
        report = "SERVICE VALIDATION REPORT\n"
        report += "=" * 60 + "\n\n"
        
        for service_id, result in results.items():
            report += f"{result['name']}:\n"
            report += f"  Working Directory: {'✓' if result['working_directory_exists'] else '✗'}\n"
            report += f"  Command File:      {'✓' if result['command_file_exists'] else '✗'}\n"
            report += f"  Python Executable: {result['python_executable']}\n"
            
            if result['issues']:
                report += "  Issues:\n"
                for issue in result['issues']:
                    report += f"    - {issue}\n"
            else:
                report += "  Status: All checks passed ✓\n"
            report += "\n"
        
        report += "=" * 60 + "\n"
        report += "PYTHON ENVIRONMENT TEST\n"
        report += "=" * 60 + "\n"
        
        test_imports = ['discord', 'flask', 'asyncio', 'asyncpg']
        for module in test_imports:
            try:
                __import__(module)
                report += f"  {module}: ✓ Available\n"
            except ImportError:
                report += f"  {module}: ✗ Missing (pip install {module})\n"
        
        report += "=" * 60 + "\n"
        
        text_widget.insert(tk.END, report)
        text_widget.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to stop all services and quit?"):
            self.running = False
            self.stop_all_services()
            self.save_status()
            self.root.destroy()
    
    def run(self):
        """Run the service manager"""
        self.logger.info("Starting Integrated Service Manager")
        
        # Print validation report to console
        self.print_validation_report()
        
        # Load previous status
        self.load_status()
        
        # Create and run GUI
        self.create_gui()
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            self.running = False
            self.stop_all_services()
            self.save_status()


def main():
    """Main entry point"""
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Create and run service manager
    manager = ServiceManager()
    manager.run()


if __name__ == "__main__":
    main()
