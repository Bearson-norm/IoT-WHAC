#!/usr/bin/env python3
"""
Automatic Backup and Restore for AS608 Fingerprint Sensor
Runs automatically on startup to ensure data persistence
"""

import os
import sys
import time
import logging
from fingerprint_manager import FingerprintManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auto_backup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def auto_backup_restore():
    """Automatically backup sensor data and restore if needed"""
    manager = FingerprintManager()
    
    try:
        # Connect to sensor
        logger.info("Connecting to fingerprint sensor...")
        if not manager.connect_sensor():
            logger.error("Failed to connect to fingerprint sensor")
            return False
        
        # Get sensor status
        if manager.finger.read_templates() == adafruit_fingerprint.OK:
            sensor_count = manager.finger.template_count
            logger.info(f"Sensor has {sensor_count} templates")
        else:
            logger.error("Failed to read sensor templates")
            return False
        
        # Get database status
        db_stats = manager.get_database_stats()
        if db_stats:
            db_count = db_stats['database_templates']
            logger.info(f"Database has {db_count} templates")
        else:
            logger.error("Failed to get database statistics")
            return False
        
        # Decision logic
        if sensor_count == 0 and db_count > 0:
            # Sensor is empty but database has data - restore
            logger.info("Sensor is empty, restoring from database...")
            if manager.restore_database_to_sensor():
                logger.info("✓ Restore completed successfully")
                return True
            else:
                logger.error("✗ Restore failed")
                return False
                
        elif sensor_count > 0 and db_count == 0:
            # Sensor has data but database is empty - backup
            logger.info("Database is empty, backing up from sensor...")
            if manager.backup_sensor_to_database():
                logger.info("✓ Backup completed successfully")
                return True
            else:
                logger.error("✗ Backup failed")
                return False
                
        elif sensor_count > 0 and db_count > 0:
            # Both have data - check if they match
            if sensor_count == db_count:
                logger.info("✓ Sensor and database are in sync")
                return True
            else:
                # Counts don't match - backup sensor to update database
                logger.info("Template counts don't match, updating database...")
                if manager.backup_sensor_to_database():
                    logger.info("✓ Database updated successfully")
                    return True
                else:
                    logger.error("✗ Database update failed")
                    return False
        else:
            # Both are empty
            logger.info("Both sensor and database are empty - ready for new enrollments")
            return True
            
    except Exception as e:
        logger.error(f"Auto backup/restore error: {e}")
        return False
    finally:
        manager.cleanup()
    
    return True

if __name__ == "__main__":
    logger.info("Starting automatic backup/restore process...")
    
    # Wait a bit for system to stabilize
    time.sleep(2)
    
    if auto_backup_restore():
        logger.info("✓ Automatic backup/restore completed successfully")
        sys.exit(0)
    else:
        logger.error("✗ Automatic backup/restore failed")
        sys.exit(1)
