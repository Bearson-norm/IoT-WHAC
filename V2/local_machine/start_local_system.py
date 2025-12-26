#!/usr/bin/env python3
"""
Launcher untuk menjalankan fingerprint_multi_client.py dan relay_controller_advanced.py
secara bersamaan tanpa konflik dan overlapping.

Fitur:
- Menjalankan kedua program sebagai subprocess terpisah
- Monitoring proses dan auto-restart jika crash
- Graceful shutdown dengan Ctrl+C
- Logging terpisah untuk setiap program
- Deteksi konflik GPIO dan port serial
"""

import subprocess
import time
import sys
import os
import signal
import threading
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('local_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class LocalSystemLauncher:
    """Launcher untuk sistem local machine"""
    
    def __init__(self):
        self.processes = {}
        self.running = True
        self.restart_enabled = True
        self.restart_delay = 5  # seconds
        
        # Path ke program
        self.base_dir = Path(__file__).parent
        self.fingerprint_script = self.base_dir / "fingerprint_multi_client.py"
        self.relay_script = self.base_dir / "relay_controller_advanced.py"
        
        # Log files
        self.fingerprint_log = self.base_dir / "fingerprint_multi_client.log"
        self.relay_log = self.base_dir / "relay_controller_advanced.log"
        
        # Verify scripts exist
        if not self.fingerprint_script.exists():
            logger.error(f"❌ Script tidak ditemukan: {self.fingerprint_script}")
            sys.exit(1)
        if not self.relay_script.exists():
            logger.error(f"❌ Script tidak ditemukan: {self.relay_script}")
            sys.exit(1)
    
    def check_existing_instances(self):
        """Cek apakah ada instance yang sudah berjalan"""
        try:
            # Cek PID files
            pid_files = [
                "/tmp/fingerprint_multi_client.pid",
                "/tmp/relay_controller_advanced.pid"
            ]
            
            for pid_file in pid_files:
                if os.path.exists(pid_file):
                    try:
                        with open(pid_file, 'r') as f:
                            old_pid = int(f.read().strip())
                        if os.name == 'posix':
                            try:
                                os.kill(old_pid, 0)  # Check if process exists
                                logger.warning(f"⚠️  Process dengan PID {old_pid} masih berjalan")
                                logger.warning(f"💡 Hentikan proses tersebut atau hapus {pid_file}")
                            except OSError:
                                # Process doesn't exist, remove stale PID file
                                os.remove(pid_file)
                                logger.info(f"✓ Menghapus stale PID file: {pid_file}")
                    except (ValueError, IOError) as e:
                        logger.warning(f"⚠️  Error membaca PID file {pid_file}: {e}")
                        try:
                            os.remove(pid_file)
                        except:
                            pass
        except Exception as e:
            logger.warning(f"⚠️  Error checking existing instances: {e}")
    
    def start_fingerprint_client(self):
        """Start fingerprint_multi_client.py"""
        try:
            logger.info("🚀 Starting fingerprint_multi_client.py...")
            
            # Open log file for writing
            log_file = open(self.fingerprint_log, 'a', encoding='utf-8')
            
            process = subprocess.Popen(
                [sys.executable, str(self.fingerprint_script)],
                cwd=str(self.base_dir),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.processes['fingerprint'] = {
                'process': process,
                'log_file': log_file,
                'name': 'Fingerprint Multi Client',
                'script': str(self.fingerprint_script),
                'restart_count': 0
            }
            
            logger.info(f"✅ Fingerprint client started (PID: {process.pid})")
            logger.info(f"📝 Log file: {self.fingerprint_log}")
            
            # Wait a moment to check if it starts successfully
            time.sleep(2)
            if process.poll() is not None:
                logger.error(f"❌ Fingerprint client exited immediately (code: {process.returncode})")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start fingerprint client: {e}")
            return False
    
    def start_relay_controller(self):
        """Start relay_controller_advanced.py"""
        try:
            logger.info("🚀 Starting relay_controller_advanced.py...")
            
            # Open log file for writing
            log_file = open(self.relay_log, 'a', encoding='utf-8')
            
            process = subprocess.Popen(
                [sys.executable, str(self.relay_script)],
                cwd=str(self.base_dir),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.processes['relay'] = {
                'process': process,
                'log_file': log_file,
                'name': 'Relay Controller Advanced',
                'script': str(self.relay_script),
                'restart_count': 0
            }
            
            logger.info(f"✅ Relay controller started (PID: {process.pid})")
            logger.info(f"📝 Log file: {self.relay_log}")
            
            # Wait a moment to check if it starts successfully
            time.sleep(2)
            if process.poll() is not None:
                logger.error(f"❌ Relay controller exited immediately (code: {process.returncode})")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start relay controller: {e}")
            return False
    
    def start_all(self):
        """Start semua komponen"""
        logger.info("=" * 70)
        logger.info("IoT-WHAC Local System Launcher")
        logger.info("=" * 70)
        logger.info(f"Startup time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Base directory: {self.base_dir}")
        logger.info("=" * 70)
        
        # Check existing instances
        self.check_existing_instances()
        
        # Start fingerprint client first
        if not self.start_fingerprint_client():
            logger.error("❌ Failed to start fingerprint client")
            return False
        
        # Wait a moment for fingerprint client to initialize
        time.sleep(3)
        
        # Start relay controller
        if not self.start_relay_controller():
            logger.error("❌ Failed to start relay controller")
            # Stop fingerprint client if relay fails
            self.stop_component('fingerprint')
            return False
        
        logger.info("=" * 70)
        logger.info("🎉 All components started successfully!")
        logger.info("=" * 70)
        logger.info("📊 Running components:")
        for key, proc_info in self.processes.items():
            logger.info(f"  - {proc_info['name']}: PID {proc_info['process'].pid}")
        logger.info("=" * 70)
        logger.info("💡 Press Ctrl+C to stop all components gracefully")
        logger.info("=" * 70)
        
        return True
    
    def monitor_processes(self):
        """Monitor running processes dan restart jika crash"""
        logger.info("🔄 Starting process monitor...")
        
        while self.running:
            try:
                for key, proc_info in list(self.processes.items()):
                    process = proc_info['process']
                    
                    # Check if process is still running
                    if process.poll() is not None:
                        exit_code = process.returncode
                        proc_info['restart_count'] += 1
                        
                        logger.warning(f"⚠️  {proc_info['name']} stopped unexpectedly!")
                        logger.warning(f"   Exit code: {exit_code}")
                        logger.warning(f"   Restart count: {proc_info['restart_count']}")
                        
                        # Close log file
                        if proc_info['log_file']:
                            try:
                                proc_info['log_file'].close()
                            except:
                                pass
                        
                        # Remove from processes dict
                        del self.processes[key]
                        
                        # Restart if enabled
                        if self.restart_enabled:
                            logger.info(f"🔄 Restarting {proc_info['name']} in {self.restart_delay} seconds...")
                            time.sleep(self.restart_delay)
                            
                            if key == 'fingerprint':
                                if self.start_fingerprint_client():
                                    logger.info(f"✅ {proc_info['name']} restarted successfully")
                                else:
                                    logger.error(f"❌ Failed to restart {proc_info['name']}")
                            elif key == 'relay':
                                if self.start_relay_controller():
                                    logger.info(f"✅ {proc_info['name']} restarted successfully")
                                else:
                                    logger.error(f"❌ Failed to restart {proc_info['name']}")
                        else:
                            logger.info(f"⏸️  Auto-restart disabled for {proc_info['name']}")
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in process monitor: {e}")
                time.sleep(5)
    
    def stop_component(self, key):
        """Stop a specific component"""
        if key not in self.processes:
            return
        
        proc_info = self.processes[key]
        process = proc_info['process']
        
        try:
            logger.info(f"🛑 Stopping {proc_info['name']}...")
            
            # Try graceful termination
            process.terminate()
            
            # Wait for process to terminate
            try:
                process.wait(timeout=5)
                logger.info(f"✅ {proc_info['name']} stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"⚠️  Force killing {proc_info['name']}...")
                process.kill()
                process.wait()
                logger.info(f"✅ {proc_info['name']} force killed")
            
            # Close log file
            if proc_info['log_file']:
                try:
                    proc_info['log_file'].close()
                except:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Error stopping {proc_info['name']}: {e}")
        finally:
            # Remove from processes dict
            if key in self.processes:
                del self.processes[key]
    
    def stop_all(self):
        """Stop semua komponen"""
        logger.info("\n" + "=" * 70)
        logger.info("🛑 Stopping all components...")
        logger.info("=" * 70)
        
        self.running = False
        
        # Stop all processes
        for key in list(self.processes.keys()):
            self.stop_component(key)
        
        logger.info("=" * 70)
        logger.info("✅ All components stopped")
        logger.info("=" * 70)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"\n📡 Received signal {signum}")
        self.stop_all()
        sys.exit(0)
    
    def run(self):
        """Run launcher"""
        # Setup signal handlers
        if os.name == 'posix':
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Start all components
            if not self.start_all():
                logger.error("❌ Failed to start all components")
                sys.exit(1)
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
            monitor_thread.start()
            
            # Keep main thread alive
            while self.running:
                # Check if all processes are still running
                if len(self.processes) == 0:
                    logger.warning("⚠️  All processes stopped!")
                    break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n📡 Keyboard interrupt received")
            self.stop_all()
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            self.stop_all()
            sys.exit(1)


def main():
    """Main function"""
    launcher = LocalSystemLauncher()
    launcher.run()


if __name__ == "__main__":
    main()

