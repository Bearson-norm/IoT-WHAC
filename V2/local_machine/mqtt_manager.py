#!/usr/bin/env python3
"""
Centralized MQTT Manager for WHAC System
Manages single MQTT connection for all components to prevent conflicts
"""

import paho.mqtt.client as mqtt
import json
import logging
import threading
import time
from datetime import datetime
from config import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MQTTManager:
    """Centralized MQTT connection manager"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure single MQTT connection"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MQTTManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize MQTT manager"""
        if hasattr(self, 'initialized'):
            return
            
        self.mqtt_broker = MQTT_BROKER
        self.mqtt_port = MQTT_PORT
        self.mqtt_client = None
        self.connected = False
        self.running = True
        self.subscribers = {}  # Store callback functions for topics
        self.connection_retries = 0
        self.max_retries = 5
        self.retry_delay = 5
        
        # Connection monitoring
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 30
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Start connection monitor
        self.monitor_thread = threading.Thread(target=self.connection_monitor, daemon=True)
        self.monitor_thread.start()
        
        self.initialized = True
        logger.info("✅ MQTT Manager initialized")
    
    def setup_mqtt(self):
        """Setup MQTT client with improved connection handling"""
        try:
            # Use unique client ID
            unique_id = f"whac_manager_{STORE_ID}_{int(time.time())}"
            self.mqtt_client = mqtt.Client(client_id=unique_id, clean_session=True)
            
            # Set callbacks
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_log = self.on_mqtt_log
            
            # Set connection options for stability
            self.mqtt_client.keepalive = 60
            self.mqtt_client.connect_async(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            logger.info("✓ MQTT client setup complete")
            
        except Exception as e:
            logger.error(f"MQTT setup error: {e}")
            self.connected = False
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            self.connection_retries = 0
            self.last_heartbeat = time.time()
            logger.info("✅ MQTT Manager connected successfully")
            
            # Resubscribe to all topics
            for topic in self.subscribers.keys():
                client.subscribe(topic, qos=1)
                logger.info(f"✅ Resubscribed to: {topic}")
                
        else:
            logger.error(f"❌ MQTT Manager connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        if rc != 0:  # Only log unexpected disconnections
            logger.warning(f"MQTT Manager disconnected (code: {rc})")
            self.attempt_reconnection()
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Route message to appropriate subscriber
            if topic in self.subscribers:
                callback = self.subscribers[topic]
                callback(topic, payload)
            else:
                logger.warning(f"No subscriber for topic: {topic}")
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def on_mqtt_log(self, client, userdata, level, buf):
        """MQTT log callback"""
        if level == mqtt.MQTT_LOG_ERR:
            logger.error(f"MQTT Error: {buf}")
        elif level == mqtt.MQTT_LOG_WARNING:
            logger.warning(f"MQTT Warning: {buf}")
    
    def subscribe(self, topic, callback):
        """Subscribe to a topic with callback function"""
        try:
            self.subscribers[topic] = callback
            
            if self.connected:
                self.mqtt_client.subscribe(topic, qos=1)
                logger.info(f"✅ Subscribed to: {topic}")
            else:
                logger.warning(f"⚠️  Not connected, will subscribe when connected: {topic}")
                
        except Exception as e:
            logger.error(f"Error subscribing to {topic}: {e}")
    
    def unsubscribe(self, topic):
        """Unsubscribe from a topic"""
        try:
            if topic in self.subscribers:
                del self.subscribers[topic]
                
            if self.connected:
                self.mqtt_client.unsubscribe(topic)
                logger.info(f"✅ Unsubscribed from: {topic}")
                
        except Exception as e:
            logger.error(f"Error unsubscribing from {topic}: {e}")
    
    def publish(self, topic, payload, qos=1, retain=False):
        """Publish message to topic"""
        try:
            if self.connected:
                if isinstance(payload, dict):
                    payload = json.dumps(payload)
                
                result = self.mqtt_client.publish(topic, payload, qos=qos, retain=retain)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.debug(f"📤 Published to {topic}: {payload[:100]}...")
                    return True
                else:
                    logger.error(f"❌ Failed to publish to {topic}: {result.rc}")
                    return False
            else:
                logger.error(f"❌ Cannot publish - MQTT not connected: {topic}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")
            return False
    
    def attempt_reconnection(self):
        """Attempt to reconnect to MQTT broker"""
        if self.connection_retries < self.max_retries:
            self.connection_retries += 1
            logger.info(f"🔄 Attempting reconnection {self.connection_retries}/{self.max_retries}...")
            
            time.sleep(self.retry_delay)
            
            try:
                self.mqtt_client.reconnect()
            except Exception as e:
                logger.error(f"Reconnection attempt failed: {e}")
        else:
            logger.error(f"❌ Max reconnection attempts reached ({self.max_retries})")
    
    def connection_monitor(self):
        """Monitor connection health and attempt reconnection if needed"""
        while self.running:
            try:
                current_time = time.time()
                
                # Check if we need to send heartbeat
                if self.connected and (current_time - self.last_heartbeat) > self.heartbeat_interval:
                    self.send_heartbeat()
                
                # Check connection status
                if not self.connected and self.connection_retries < self.max_retries:
                    self.attempt_reconnection()
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                time.sleep(10)
    
    def send_heartbeat(self):
        """Send heartbeat to maintain connection"""
        try:
            heartbeat_data = {
                "type": "heartbeat",
                "store_id": STORE_ID,
                "timestamp": datetime.now().isoformat(),
                "status": "alive"
            }
            
            self.publish(f"WHAC/{STORE_ID}/heartbeat", heartbeat_data)
            self.last_heartbeat = time.time()
            
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
    
    def is_connected(self):
        """Check if MQTT is connected"""
        return self.connected
    
    def cleanup(self):
        """Clean up MQTT connection"""
        try:
            logger.info("Cleaning up MQTT Manager...")
            self.running = False
            
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("MQTT Manager disconnected")
            
            logger.info("✅ MQTT Manager cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up MQTT Manager: {e}")

# Global instance
mqtt_manager = MQTTManager()

def get_mqtt_manager():
    """Get the global MQTT manager instance"""
    return mqtt_manager
