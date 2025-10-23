#!/usr/bin/env python3
"""
Resource Monitor for WHAC System
Monitors CPU, Memory, Network, and I/O usage
"""

import psutil
import time
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResourceMonitor:
    def __init__(self):
        """Initialize resource monitor"""
        self.start_time = time.time()
        self.initial_network = psutil.net_io_counters()
        self.initial_disk = psutil.disk_io_counters()
        
    def get_system_stats(self):
        """Get current system statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used / (1024**3)  # GB
            memory_total = memory.total / (1024**3)  # GB
            
            # Network usage
            network = psutil.net_io_counters()
            network_sent = (network.bytes_sent - self.initial_network.bytes_sent) / (1024**2)  # MB
            network_recv = (network.bytes_recv - self.initial_network.bytes_recv) / (1024**2)  # MB
            
            # Disk I/O
            disk = psutil.disk_io_counters()
            disk_read = (disk.read_bytes - self.initial_disk.read_bytes) / (1024**2)  # MB
            disk_write = (disk.write_bytes - self.initial_disk.write_bytes) / (1024**2)  # MB
            
            # Process count
            process_count = len(psutil.pids())
            
            # Uptime
            uptime = time.time() - self.start_time
            
            return {
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': uptime,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_used_gb': round(memory_used, 2),
                'memory_total_gb': round(memory_total, 2),
                'network_sent_mb': round(network_sent, 2),
                'network_recv_mb': round(network_recv, 2),
                'disk_read_mb': round(disk_read, 2),
                'disk_write_mb': round(disk_write, 2),
                'process_count': process_count
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return None
    
    def get_whac_processes(self):
        """Get WHAC-related processes"""
        try:
            whac_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if any(keyword in cmdline.lower() for keyword in ['whac', 'fingerprint', 'mqtt']):
                            whac_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_percent': proc.info['memory_percent'],
                                'cmdline': cmdline
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return whac_processes
            
        except Exception as e:
            logger.error(f"Error getting WHAC processes: {e}")
            return []
    
    def monitor_continuously(self, interval=30):
        """Monitor resources continuously"""
        logger.info(f"🔍 Starting continuous monitoring (interval: {interval}s)")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                stats = self.get_system_stats()
                if stats:
                    logger.info(f"📊 System Stats:")
                    logger.info(f"   CPU: {stats['cpu_percent']}%")
                    logger.info(f"   Memory: {stats['memory_percent']}% ({stats['memory_used_gb']:.1f}GB/{stats['memory_total_gb']:.1f}GB)")
                    logger.info(f"   Network: ↑{stats['network_sent_mb']:.1f}MB ↓{stats['network_recv_mb']:.1f}MB")
                    logger.info(f"   Disk I/O: R{stats['disk_read_mb']:.1f}MB W{stats['disk_write_mb']:.1f}MB")
                    logger.info(f"   Processes: {stats['process_count']}")
                    logger.info(f"   Uptime: {stats['uptime_seconds']:.0f}s")
                
                whac_processes = self.get_whac_processes()
                if whac_processes:
                    logger.info(f"🔧 WHAC Processes:")
                    for proc in whac_processes:
                        logger.info(f"   PID {proc['pid']}: {proc['name']} - CPU: {proc['cpu_percent']}%, Memory: {proc['memory_percent']:.1f}%")
                
                logger.info("-" * 50)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
    
    def save_stats_to_file(self, filename="resource_stats.json"):
        """Save current stats to file"""
        try:
            stats = self.get_system_stats()
            whac_processes = self.get_whac_processes()
            
            data = {
                'system_stats': stats,
                'whac_processes': whac_processes
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"📁 Stats saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving stats: {e}")

def main():
    """Main function"""
    try:
        monitor = ResourceMonitor()
        
        # Save initial stats
        monitor.save_stats_to_file()
        
        # Start continuous monitoring
        monitor.monitor_continuously(interval=30)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()




