#!/usr/bin/env python3
"""
WHAC Fingerprint System Startup Script
Starts all components of the system
"""

import subprocess
import time
import sys
import os
import signal
import threading
from datetime import datetime

class WHACSystem:
    def __init__(self):
        self.processes = {}
        self.running = True
        
    def start_component(self, name, command, cwd=None):
        """Start a system component"""
        try:
            print(f"🚀 Starting {name}...")
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes[name] = process
            print(f"✅ {name} started (PID: {process.pid})")
            return process
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return None
    
    def start_all(self):
        """Start all system components"""
        print("=" * 60)
        print("WHAC Fingerprint System - Starting All Components")
        print("=" * 60)
        print(f"Startup time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Start MQTT Data Processor (Server)
        self.start_component(
            "MQTT Data Processor",
            "python3 mqtt_data_processor.py",
            cwd="server"
        )
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Start Web UI
        self.start_component(
            "Web UI",
            "python3 app.py",
            cwd="web_ui"
        )
        
        print("=" * 60)
        print("🎉 All components started!")
        print("=" * 60)
        print("📱 Web UI: http://localhost:5000")
        print("🔐 Login: admin / admin123")
        print("=" * 60)
        print("💡 To start local machine:")
        print("   cd local_machine/")
        print("   python3 fingerprint_simple_client.py")
        print("=" * 60)
        print("Press Ctrl+C to stop all components")
        print("=" * 60)
    
    def monitor_processes(self):
        """Monitor running processes"""
        while self.running:
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    print(f"⚠️  {name} stopped unexpectedly (exit code: {process.returncode})")
                    del self.processes[name]
            
            time.sleep(5)
    
    def stop_all(self):
        """Stop all system components"""
        print("\n🛑 Stopping all components...")
        self.running = False
        
        for name, process in self.processes.items():
            try:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"⚠️  Force killing {name}...")
                process.kill()
                process.wait()
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        print("✅ All components stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n📡 Received signal {signum}")
        self.stop_all()
        sys.exit(0)

def main():
    """Main function"""
    system = WHACSystem()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, system.signal_handler)
    signal.signal(signal.SIGTERM, system.signal_handler)
    
    try:
        # Start all components
        system.start_all()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=system.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive
        while system.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        system.stop_all()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        system.stop_all()
        sys.exit(1)

if __name__ == "__main__":
    main()
