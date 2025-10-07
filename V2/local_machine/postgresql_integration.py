#!/usr/bin/env python3
"""
PostgreSQL Integration for Fingerprint System
Sends fingerprint data to PostgreSQL database
"""

import psycopg2
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class PostgreSQLIntegration:
    def __init__(self, db_config=None):
        """Initialize PostgreSQL connection"""
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'whac_master',
            'user': 'postgres',
            'password': 'Admin123',
            'port': 5432
        }
        self.connection = None
        self.connect()
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("✓ Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {e}")
            self.connection = None
    
    def is_connected(self):
        """Check if database is connected"""
        try:
            if self.connection and not self.connection.closed:
                return True
            else:
                self.connect()
                return self.connection is not None
        except:
            return False
    
    def log_fingerprint_scan(self, user_id: Optional[int], store_id: str, 
                           finger_template_id: Optional[int], timestamp: datetime = None):
        """Log fingerprint scan to log_data table"""
        try:
            if not self.is_connected():
                logger.error("Database not connected")
                return False
            
            if timestamp is None:
                timestamp = datetime.now()
            
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO log_data (user_id, store_id, timestamp, finger_template_id)
                VALUES (%s, %s, %s, %s)
            """, (user_id, store_id, timestamp, finger_template_id))
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✓ Logged fingerprint scan: User {user_id}, Store {store_id}, Template {finger_template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging fingerprint scan: {e}")
            return False
    
    def log_action(self, user_id: Optional[int], store_id: str, username: Optional[str],
                  action: str, granted_denied: str, timestamp: datetime = None):
        """Log action to log_action table"""
        try:
            if not self.is_connected():
                logger.error("Database not connected")
                return False
            
            if timestamp is None:
                timestamp = datetime.now()
            
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO log_action (user_id, store_id, username, timestamp, action, granted_denied)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, store_id, username, action, granted_denied, timestamp))
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✓ Logged action: {action} - {granted_denied} for User {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging action: {e}")
            return False
    
    def get_user_info(self, user_id: int) -> Optional[dict]:
        """Get user information from store_001 table"""
        try:
            if not self.is_connected():
                logger.error("Database not connected")
                return None
            
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT user_id, username, finger_template_id
                FROM store_001
                WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'finger_template_id': result[2]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def add_user(self, user_id: int, username: str, finger_template_id: int) -> bool:
        """Add user to store_001 table"""
        try:
            if not self.is_connected():
                logger.error("Database not connected")
                return False
            
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO store_001 (user_id, username, finger_template_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    finger_template_id = EXCLUDED.finger_template_id,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, username, finger_template_id))
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✓ Added/updated user: {username} (ID: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def process_fingerprint_result(self, fingerprint_id: int, confidence: int, 
                                 action: str, store_id: str = "Store001"):
        """Process fingerprint scan result and log to database"""
        try:
            # Get user info if fingerprint_id > 0
            user_info = None
            if fingerprint_id > 0:
                user_info = self.get_user_info(fingerprint_id)
            
            # Determine granted/denied status
            granted_denied = "granted" if action == "access_granted" else "denied"
            
            # Log fingerprint scan
            self.log_fingerprint_scan(
                user_id=user_info['user_id'] if user_info else None,
                store_id=store_id,
                finger_template_id=fingerprint_id if fingerprint_id > 0 else None
            )
            
            # Log action
            self.log_action(
                user_id=user_info['user_id'] if user_info else None,
                store_id=store_id,
                username=user_info['username'] if user_info else None,
                action=action,
                granted_denied=granted_denied
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing fingerprint result: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        try:
            if self.connection and not self.connection.closed:
                self.connection.close()
                logger.info("✓ PostgreSQL connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

# Example usage
if __name__ == "__main__":
    # Test the integration
    db = PostgreSQLIntegration()
    
    # Test logging a fingerprint scan
    db.log_fingerprint_scan(
        user_id=1,
        store_id="Store001",
        finger_template_id=1
    )
    
    # Test logging an action
    db.log_action(
        user_id=1,
        store_id="Store001",
        username="John Doe",
        action="access_granted",
        granted_denied="granted"
    )
    
    # Test processing a complete fingerprint result
    db.process_fingerprint_result(
        fingerprint_id=1,
        confidence=85,
        action="access_granted"
    )
    
    db.close()

