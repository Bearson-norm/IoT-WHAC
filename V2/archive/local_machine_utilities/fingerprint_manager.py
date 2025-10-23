#!/usr/bin/env python3
"""
Fingerprint Data Management System
Provides backup, restore, and database management for AS608 fingerprint sensor
"""

import serial
import adafruit_fingerprint
import json
import time
import logging
import sys
import sqlite3
import os
from datetime import datetime
from config import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FingerprintManager:
    def __init__(self, database_file="fingerprints.db"):
        self.uart = None
        self.finger = None
        self.db_file = database_file
        self.init_database()
        
    def connect_sensor(self, retries=3):
        """Connect to AS608 fingerprint sensor"""
        for attempt in range(retries):
            try:
                logger.info(f"Connecting to fingerprint sensor on {FINGERPRINT_PORT} (attempt {attempt + 1})")
                self.uart = serial.Serial(FINGERPRINT_PORT, baudrate=BAUD_RATE, timeout=2)
                time.sleep(0.5)
                self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)
                
                if self.finger.read_templates() == adafruit_fingerprint.OK:
                    logger.info(f"✓ Sensor connected! Templates: {self.finger.template_count}")
                    return True
                else:
                    raise Exception("Failed to read templates from sensor")
                    
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if self.uart:
                    self.uart.close()
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    raise
        return False
    
    def init_database(self):
        """Initialize SQLite database for fingerprint management"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create fingerprints table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fingerprints (
                    id INTEGER PRIMARY KEY,
                    template_id INTEGER UNIQUE,
                    name TEXT,
                    template_data BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    use_count INTEGER DEFAULT 0
                )
            ''')
            
            # Create backup_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backup_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_name TEXT,
                    template_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"✓ Database initialized: {self.db_file}")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def backup_sensor_to_database(self):
        """Backup all templates from sensor to database"""
        try:
            if not self.finger:
                logger.error("Sensor not connected")
                return False
            
            # Get template count
            if self.finger.read_templates() != adafruit_fingerprint.OK:
                logger.error("Failed to read templates from sensor")
                return False
            
            template_count = self.finger.template_count
            logger.info(f"Backing up {template_count} templates to database...")
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            backed_up = 0
            for template_id in range(1, 129):  # AS608 supports 1-128
                try:
                    # Try to load template from sensor
                    if self.finger.load_model(template_id) == adafruit_fingerprint.OK:
                        # Get template data
                        template_data = self.finger.get_fpdata("char", 1)
                        
                        # Store in database
                        cursor.execute('''
                            INSERT OR REPLACE INTO fingerprints 
                            (template_id, template_data, created_at) 
                            VALUES (?, ?, ?)
                        ''', (template_id, bytes(template_data), datetime.now()))
                        
                        backed_up += 1
                        logger.debug(f"Backed up template {template_id}")
                        
                except Exception as e:
                    logger.debug(f"Template {template_id} not found or error: {e}")
                    continue
            
            # Record backup in history
            cursor.execute('''
                INSERT INTO backup_history (template_count, created_at)
                VALUES (?, ?)
            ''', (backed_up, datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✓ Backup complete: {backed_up} templates saved to database")
            return True
            
        except Exception as e:
            logger.error(f"Backup error: {e}")
            return False
    
    def restore_database_to_sensor(self):
        """Restore templates from database to sensor"""
        try:
            if not self.finger:
                logger.error("Sensor not connected")
                return False
            
            # Clear sensor first
            logger.info("Clearing sensor memory...")
            if self.finger.empty_library() != adafruit_fingerprint.OK:
                logger.error("Failed to clear sensor memory")
                return False
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get all templates from database
            cursor.execute('SELECT template_id, template_data FROM fingerprints ORDER BY template_id')
            templates = cursor.fetchall()
            
            restored = 0
            for template_id, template_data in templates:
                try:
                    # Upload template to sensor
                    self.finger.upload_model(template_id, list(template_data))
                    
                    # Store template in sensor
                    if self.finger.store_model(template_id) == adafruit_fingerprint.OK:
                        restored += 1
                        logger.debug(f"Restored template {template_id}")
                    else:
                        logger.warning(f"Failed to store template {template_id}")
                        
                except Exception as e:
                    logger.warning(f"Error restoring template {template_id}: {e}")
                    continue
            
            conn.close()
            
            logger.info(f"✓ Restore complete: {restored} templates restored to sensor")
            return True
            
        except Exception as e:
            logger.error(f"Restore error: {e}")
            return False
    
    def backup_to_file(self, filename=None):
        """Backup sensor templates to JSON file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"fingerprint_backup_{timestamp}.json"
            
            if not self.finger:
                logger.error("Sensor not connected")
                return False
            
            # Get template count
            if self.finger.read_templates() != adafruit_fingerprint.OK:
                logger.error("Failed to read templates from sensor")
                return False
            
            backup_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "sensor_type": "AS608",
                "template_count": self.finger.template_count,
                "templates": {}
            }
            
            # Backup each template
            for template_id in range(1, 129):
                try:
                    if self.finger.load_model(template_id) == adafruit_fingerprint.OK:
                        template_data = self.finger.get_fpdata("char", 1)
                        backup_data["templates"][str(template_id)] = {
                            "data": list(template_data),
                            "size": len(template_data)
                        }
                        logger.debug(f"Backed up template {template_id}")
                        
                except Exception as e:
                    logger.debug(f"Template {template_id} not found: {e}")
                    continue
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"✓ Backup saved to file: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"File backup error: {e}")
            return None
    
    def restore_from_file(self, filename):
        """Restore templates from JSON file to sensor"""
        try:
            if not os.path.exists(filename):
                logger.error(f"Backup file not found: {filename}")
                return False
            
            # Load backup data
            with open(filename, 'r') as f:
                backup_data = json.load(f)
            
            logger.info(f"Restoring from backup: {filename}")
            logger.info(f"Backup contains {len(backup_data['templates'])} templates")
            
            # Clear sensor first
            if self.finger.empty_library() != adafruit_fingerprint.OK:
                logger.error("Failed to clear sensor memory")
                return False
            
            restored = 0
            for template_id_str, template_info in backup_data["templates"].items():
                try:
                    template_id = int(template_id_str)
                    template_data = template_info["data"]
                    
                    # Upload template to sensor
                    self.finger.upload_model(template_id, template_data)
                    
                    # Store template in sensor
                    if self.finger.store_model(template_id) == adafruit_fingerprint.OK:
                        restored += 1
                        logger.debug(f"Restored template {template_id}")
                    else:
                        logger.warning(f"Failed to store template {template_id}")
                        
                except Exception as e:
                    logger.warning(f"Error restoring template {template_id_str}: {e}")
                    continue
            
            logger.info(f"✓ Restore complete: {restored} templates restored from file")
            return True
            
        except Exception as e:
            logger.error(f"File restore error: {e}")
            return False
    
    def get_database_stats(self):
        """Get statistics from database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get template count
            cursor.execute('SELECT COUNT(*) FROM fingerprints')
            template_count = cursor.fetchone()[0]
            
            # Get backup history
            cursor.execute('SELECT COUNT(*) FROM backup_history')
            backup_count = cursor.fetchone()[0]
            
            # Get last backup
            cursor.execute('SELECT created_at FROM backup_history ORDER BY created_at DESC LIMIT 1')
            last_backup = cursor.fetchone()
            last_backup = last_backup[0] if last_backup else "Never"
            
            conn.close()
            
            return {
                "database_templates": template_count,
                "backup_count": backup_count,
                "last_backup": last_backup
            }
            
        except Exception as e:
            logger.error(f"Database stats error: {e}")
            return None
    
    def list_backup_files(self):
        """List available backup files"""
        try:
            backup_files = []
            for file in os.listdir('.'):
                if file.startswith('fingerprint_backup_') and file.endswith('.json'):
                    backup_files.append(file)
            
            return sorted(backup_files, reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backup files: {e}")
            return []
    
    def cleanup(self):
        """Clean up resources"""
        if self.uart:
            self.uart.close()
            logger.info("Serial connection closed")

def main():
    """Main function with interactive menu"""
    manager = FingerprintManager()
    
    try:
        # Connect to sensor
        if not manager.connect_sensor():
            logger.error("Failed to connect to fingerprint sensor")
            return 1
        
        while True:
            print("\n" + "=" * 60)
            print("FINGERPRINT DATA MANAGEMENT SYSTEM")
            print("=" * 60)
            print("1. Backup sensor to database")
            print("2. Restore database to sensor")
            print("3. Backup sensor to file")
            print("4. Restore from file")
            print("5. Show database statistics")
            print("6. List backup files")
            print("7. Show sensor status")
            print("8. Exit")
            print("=" * 60)
            
            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == "1":
                manager.backup_sensor_to_database()
            
            elif choice == "2":
                confirm = input("This will clear sensor and restore from database. Continue? (y/N): ")
                if confirm.lower() == 'y':
                    manager.restore_database_to_sensor()
                else:
                    print("Restore cancelled")
            
            elif choice == "3":
                filename = input("Enter backup filename (or press Enter for auto): ").strip()
                if not filename:
                    filename = None
                manager.backup_to_file(filename)
            
            elif choice == "4":
                backup_files = manager.list_backup_files()
                if backup_files:
                    print("\nAvailable backup files:")
                    for i, file in enumerate(backup_files, 1):
                        print(f"{i}. {file}")
                    
                    try:
                        file_choice = int(input("Select file number: ")) - 1
                        if 0 <= file_choice < len(backup_files):
                            confirm = input("This will clear sensor and restore from file. Continue? (y/N): ")
                            if confirm.lower() == 'y':
                                manager.restore_from_file(backup_files[file_choice])
                            else:
                                print("Restore cancelled")
                        else:
                            print("Invalid file number")
                    except ValueError:
                        print("Invalid input")
                else:
                    print("No backup files found")
            
            elif choice == "5":
                stats = manager.get_database_stats()
                if stats:
                    print(f"\nDatabase Statistics:")
                    print(f"  Templates in database: {stats['database_templates']}")
                    print(f"  Backup operations: {stats['backup_count']}")
                    print(f"  Last backup: {stats['last_backup']}")
                else:
                    print("Failed to get database statistics")
            
            elif choice == "6":
                backup_files = manager.list_backup_files()
                if backup_files:
                    print(f"\nBackup files ({len(backup_files)}):")
                    for file in backup_files:
                        print(f"  {file}")
                else:
                    print("No backup files found")
            
            elif choice == "7":
                if manager.finger.read_templates() == adafruit_fingerprint.OK:
                    print(f"\nSensor Status:")
                    print(f"  Templates in sensor: {manager.finger.template_count}")
                    print(f"  Sensor connected: ✓")
                else:
                    print("Failed to read sensor status")
            
            elif choice == "8":
                print("\nExiting... Goodbye!")
                break
            
            else:
                print("Invalid option. Please select 1-8")
    
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        manager.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
