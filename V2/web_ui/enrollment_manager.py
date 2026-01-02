#!/usr/bin/env python3
"""
Enrollment Manager for Web UI
Handles enrollment status tracking, timeout, and communication with local machine
"""

import threading
import time
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class EnrollmentManager:
    """Manages enrollment requests and tracks their status"""
    
    def __init__(self, timeout=120):
        """
        Initialize enrollment manager
        
        Args:
            timeout: Timeout in seconds for enrollment (default: 120 seconds / 2 minutes)
        """
        self.timeout = timeout
        self.active_enrollments = {}  # {enrollment_id: enrollment_data}
        self.lock = threading.Lock()
        self.cleanup_thread = None
        self.running = True
        
        # Start cleanup thread
        self.start_cleanup_thread()
    
    def generate_enrollment_id(self, user_id, username):
        """Generate unique enrollment ID"""
        timestamp = int(time.time() * 1000)  # milliseconds
        return f"enroll_{user_id}_{timestamp}"
    
    def start_enrollment(self, user_id, username, requested_by='admin', target_sensor=None):
        """
        Start tracking an enrollment request
        
        Returns:
            dict: Enrollment info with enrollment_id
        """
        enrollment_id = self.generate_enrollment_id(user_id, username)
        
        enrollment_data = {
            'enrollment_id': enrollment_id,
            'user_id': user_id,
            'username': username,
            'requested_by': requested_by,
            'target_sensor': target_sensor,
            'status': 'pending',  # pending, in_progress, success, error, timeout
            'started_at': datetime.now(),
            'completed_at': None,
            'device_id': None,
            'sensor_location': None,
            'error_message': None,
            'progress': 0,  # 0-100
            'progress_message': 'Waiting for enrollment to start...'
        }
        
        with self.lock:
            self.active_enrollments[enrollment_id] = enrollment_data
        
        logger.info(f"📝 Started tracking enrollment: {enrollment_id} for user {username} (ID: {user_id})")
        return enrollment_data
    
    def update_enrollment_status(self, enrollment_id, status, **kwargs):
        """
        Update enrollment status
        
        Args:
            enrollment_id: Enrollment ID
            status: New status (pending, in_progress, success, error, timeout)
            **kwargs: Additional data to update (device_id, error_message, progress, etc.)
        """
        with self.lock:
            if enrollment_id not in self.active_enrollments:
                logger.warning(f"⚠️  Enrollment ID {enrollment_id} not found")
                return False
            
            enrollment = self.active_enrollments[enrollment_id]
            enrollment['status'] = status
            
            # Update additional fields
            for key, value in kwargs.items():
                enrollment[key] = value
            
            if status in ['success', 'error', 'timeout']:
                enrollment['completed_at'] = datetime.now()
            
            logger.info(f"📊 Updated enrollment {enrollment_id}: status={status}, {kwargs}")
            return True
    
    def get_enrollment_status(self, enrollment_id):
        """Get current enrollment status"""
        with self.lock:
            return self.active_enrollments.get(enrollment_id)
    
    def get_enrollment_by_user_id(self, user_id):
        """Get active enrollment for a user ID"""
        with self.lock:
            for enrollment_id, enrollment in self.active_enrollments.items():
                if enrollment['user_id'] == user_id and enrollment['status'] in ['pending', 'in_progress']:
                    return enrollment
            return None
    
    def complete_enrollment(self, enrollment_id, success=True, **kwargs):
        """Mark enrollment as completed"""
        status = 'success' if success else 'error'
        return self.update_enrollment_status(enrollment_id, status, **kwargs)
    
    def cleanup_old_enrollments(self):
        """Remove old completed enrollments (older than 1 hour)"""
        with self.lock:
            now = datetime.now()
            to_remove = []
            
            for enrollment_id, enrollment in self.active_enrollments.items():
                if enrollment['completed_at']:
                    age = now - enrollment['completed_at']
                    if age > timedelta(hours=1):
                        to_remove.append(enrollment_id)
            
            for enrollment_id in to_remove:
                del self.active_enrollments[enrollment_id]
                logger.debug(f"🧹 Cleaned up old enrollment: {enrollment_id}")
    
    def check_timeouts(self):
        """Check for timed out enrollments"""
        with self.lock:
            now = datetime.now()
            timed_out = []
            
            for enrollment_id, enrollment in self.active_enrollments.items():
                if enrollment['status'] in ['pending', 'in_progress']:
                    age = now - enrollment['started_at']
                    if age > timedelta(seconds=self.timeout):
                        timed_out.append(enrollment_id)
            
            for enrollment_id in timed_out:
                enrollment = self.active_enrollments[enrollment_id]
                self.update_enrollment_status(
                    enrollment_id,
                    'timeout',
                    error_message=f'Enrollment timed out after {self.timeout} seconds',
                    progress_message='Enrollment timed out - please try again'
                )
                logger.warning(f"⏱️  Enrollment {enrollment_id} timed out")
    
    def cleanup_loop(self):
        """Background thread to cleanup old enrollments and check timeouts"""
        while self.running:
            try:
                self.check_timeouts()
                self.cleanup_old_enrollments()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                time.sleep(10)
    
    def start_cleanup_thread(self):
        """Start background cleanup thread"""
        if self.cleanup_thread is None or not self.cleanup_thread.is_alive():
            self.cleanup_thread = threading.Thread(
                target=self.cleanup_loop,
                daemon=True,
                name="EnrollmentCleanup"
            )
            self.cleanup_thread.start()
            logger.info("✅ Enrollment cleanup thread started")
    
    def stop(self):
        """Stop the enrollment manager"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=2)
        logger.info("🛑 Enrollment manager stopped")

# Global enrollment manager instance
enrollment_manager = EnrollmentManager(timeout=120)

