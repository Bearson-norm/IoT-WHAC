#!/usr/bin/env python3
"""
AS608 Fingerprint Sensor Driver
Direct implementation of the AS608 protocol
"""

import serial
import time
import logging

logger = logging.getLogger(__name__)

class AS608Driver:
    """AS608 Fingerprint Sensor Driver"""
    
    # Command codes
    CMD_GET_IMAGE = 0x01
    CMD_IMAGE_2_TZ = 0x02
    CMD_REGMODEL = 0x05
    CMD_STORE = 0x06
    CMD_LOAD_CHAR = 0x07
    CMD_UP_CHAR = 0x08
    CMD_DOWN_CHAR = 0x09
    CMD_UP_IMAGE = 0x0A
    CMD_DOWN_IMAGE = 0x0B
    CMD_DELETE_CHAR = 0x0C
    CMD_EMPTY = 0x0D
    CMD_SET_SYS_PARA = 0x0E
    CMD_READ_SYS_PARA = 0x0F
    CMD_SET_PWD = 0x12
    CMD_VERIFY_PWD = 0x13
    CMD_GET_RANDOM_CODE = 0x14
    CMD_SET_CHIP_ADDR = 0x15
    CMD_READ_INFO_PAGE = 0x16
    CMD_PORT_CONTROL = 0x17
    CMD_WRITE_NOTEPAD = 0x18
    CMD_READ_NOTEPAD = 0x19
    CMD_TEMPLATE_COUNT = 0x1D
    CMD_TEMPLATE_READ = 0x1F
    CMD_ENTRY_MODULE = 0x21
    CMD_EXIT_MODULE = 0x22
    CMD_LED_CONTROL = 0x35
    CMD_FINGER_DETECT = 0x26
    CMD_SEARCH = 0x04
    CMD_COMPARE = 0x03
    CMD_HIGH_SPEED_SEARCH = 0x1B
    CMD_VFY_PWD = 0x13
    
    # Response codes
    ACK_SUCCESS = 0x00
    ACK_RECV_FAIL = 0x01
    ACK_NO_FINGER = 0x02
    ACK_ENROLL_FAIL = 0x03
    ACK_OVER_DISORDERED = 0x04
    ACK_OVER_SAME_FINGER = 0x05
    ACK_NO_ENTER = 0x06
    ACK_NOT_MATCH = 0x07
    ACK_NOT_SEARCHED = 0x08
    ACK_BAD_QUALITY = 0x09
    ACK_NO_SUCH_USER = 0x0A
    ACK_BAD_LIBRARY = 0x0B
    ACK_ENROLL_IN_DIFFERENT_FINGER = 0x0C
    ACK_BAD_FINGER = 0x0D
    ACK_BAD_TEMPLATE = 0x0E
    ACK_TIMEOUT = 0x0F
    ACK_GEN_COUNT_FAIL = 0x10
    ACK_BAD_BUFFER_ID = 0x11
    ACK_INVALID_TEMPLATE = 0x12
    ACK_BAD_PACKET = 0x13
    ACK_TEMPLATE_NOT_MATCH = 0x14
    ACK_PACKET_RESEND = 0x15
    ACK_PACKET_GET_FAIL = 0x16
    ACK_INVALID_REG = 0x17
    ACK_ADDR_CODE = 0x20
    ACK_PASS_NOT_MATCH = 0x21
    ACK_FINGER_IS_NOT_PRESSED = 0x22
    ACK_DB_IS_EMPTY = 0x23
    ACK_DB_IS_FULL = 0x24
    ACK_BAD_POSITION = 0x25
    ACK_DB_IS_EXIST = 0x26
    ACK_TIMEOUT_OR_CANCEL = 0x27
    ACK_UP_IMAGE_FAIL = 0x28
    ACK_CLEAR_LIB_FAIL = 0x29
    ACK_GET_IMAGE_FAIL = 0x2A
    ACK_FP_CANCEL = 0x2B
    ACK_INVALID_PARAM = 0x2C
    ACK_GET_ONE_IMG_FAIL = 0x2D
    ACK_LIGHT_ERR = 0x2E
    ACK_NO_FINGER_DETECTED = 0x2F
    ACK_FLASH_ERR = 0x30
    ACK_NO_VALID_IMG = 0x31
    ACK_BAD_IMG_QUALITY = 0x32
    ACK_MERGE_FAIL = 0x33
    ACK_DATABASE_NOT_EXIST = 0x34
    ACK_INVALID_DATABASE = 0x35
    ACK_BAD_IMG_FORMAT = 0x36
    ACK_BAD_PACKAGE_LEN = 0x37
    ACK_BAD_PACKAGE = 0x38
    ACK_NO_SUCH_USER_2 = 0x39
    ACK_BAD_QUALITY_2 = 0x3A
    ACK_TIMEOUT_2 = 0x3B
    ACK_NO_SUCH_USER_3 = 0x3C
    ACK_BAD_QUALITY_3 = 0x3D
    ACK_TIMEOUT_3 = 0x3E
    ACK_NO_SUCH_USER_4 = 0x3F
    ACK_BAD_QUALITY_4 = 0x40
    ACK_TIMEOUT_4 = 0x41
    ACK_NO_SUCH_USER_5 = 0x42
    ACK_BAD_QUALITY_5 = 0x43
    ACK_TIMEOUT_5 = 0x44
    ACK_NO_SUCH_USER_6 = 0x45
    ACK_BAD_QUALITY_6 = 0x46
    ACK_TIMEOUT_6 = 0x47
    ACK_NO_SUCH_USER_7 = 0x48
    ACK_BAD_QUALITY_7 = 0x49
    ACK_TIMEOUT_7 = 0x4A
    ACK_NO_SUCH_USER_8 = 0x4B
    ACK_BAD_QUALITY_8 = 0x4C
    ACK_TIMEOUT_8 = 0x4D
    ACK_NO_SUCH_USER_9 = 0x4E
    ACK_BAD_QUALITY_9 = 0x4F
    ACK_TIMEOUT_9 = 0x50
    ACK_NO_SUCH_USER_10 = 0x51
    ACK_BAD_QUALITY_10 = 0x52
    ACK_TIMEOUT_10 = 0x53
    ACK_NO_SUCH_USER_11 = 0x54
    ACK_BAD_QUALITY_11 = 0x55
    ACK_TIMEOUT_11 = 0x56
    ACK_NO_SUCH_USER_12 = 0x57
    ACK_BAD_QUALITY_12 = 0x58
    ACK_TIMEOUT_12 = 0x59
    ACK_NO_SUCH_USER_13 = 0x5A
    ACK_BAD_QUALITY_13 = 0x5B
    ACK_TIMEOUT_13 = 0x5C
    ACK_NO_SUCH_USER_14 = 0x5D
    ACK_BAD_QUALITY_14 = 0x5E
    ACK_TIMEOUT_14 = 0x5F
    ACK_NO_SUCH_USER_15 = 0x60
    ACK_BAD_QUALITY_15 = 0x61
    ACK_TIMEOUT_15 = 0x62
    ACK_NO_SUCH_USER_16 = 0x63
    ACK_BAD_QUALITY_16 = 0x64
    ACK_TIMEOUT_16 = 0x65
    ACK_NO_SUCH_USER_17 = 0x66
    ACK_BAD_QUALITY_17 = 0x67
    ACK_TIMEOUT_17 = 0x68
    ACK_NO_SUCH_USER_18 = 0x69
    ACK_BAD_QUALITY_18 = 0x6A
    ACK_TIMEOUT_18 = 0x6B
    ACK_NO_SUCH_USER_19 = 0x6C
    ACK_BAD_QUALITY_19 = 0x6D
    ACK_TIMEOUT_19 = 0x6E
    ACK_NO_SUCH_USER_20 = 0x6F
    ACK_BAD_QUALITY_20 = 0x70
    ACK_TIMEOUT_20 = 0x71
    ACK_NO_SUCH_USER_21 = 0x72
    ACK_BAD_QUALITY_21 = 0x73
    ACK_TIMEOUT_21 = 0x74
    ACK_NO_SUCH_USER_22 = 0x75
    ACK_BAD_QUALITY_22 = 0x76
    ACK_TIMEOUT_22 = 0x77
    ACK_NO_SUCH_USER_23 = 0x78
    ACK_BAD_QUALITY_23 = 0x79
    ACK_TIMEOUT_23 = 0x7A
    ACK_NO_SUCH_USER_24 = 0x7B
    ACK_BAD_QUALITY_24 = 0x7C
    ACK_TIMEOUT_24 = 0x7D
    ACK_NO_SUCH_USER_25 = 0x7E
    ACK_BAD_QUALITY_25 = 0x7F
    ACK_TIMEOUT_25 = 0x80
    ACK_NO_SUCH_USER_26 = 0x81
    ACK_BAD_QUALITY_26 = 0x82
    ACK_TIMEOUT_26 = 0x83
    ACK_NO_SUCH_USER_27 = 0x84
    ACK_BAD_QUALITY_27 = 0x85
    ACK_TIMEOUT_27 = 0x86
    ACK_NO_SUCH_USER_28 = 0x87
    ACK_BAD_QUALITY_28 = 0x88
    ACK_TIMEOUT_28 = 0x89
    ACK_NO_SUCH_USER_29 = 0x8A
    ACK_BAD_QUALITY_29 = 0x8B
    ACK_TIMEOUT_29 = 0x8C
    ACK_NO_SUCH_USER_30 = 0x8D
    ACK_BAD_QUALITY_30 = 0x8E
    ACK_TIMEOUT_30 = 0x8F
    ACK_NO_SUCH_USER_31 = 0x90
    ACK_BAD_QUALITY_31 = 0x91
    ACK_TIMEOUT_31 = 0x92
    ACK_NO_SUCH_USER_32 = 0x93
    ACK_BAD_QUALITY_32 = 0x94
    ACK_TIMEOUT_32 = 0x95
    ACK_NO_SUCH_USER_33 = 0x96
    ACK_BAD_QUALITY_33 = 0x97
    ACK_TIMEOUT_33 = 0x98
    ACK_NO_SUCH_USER_34 = 0x99
    ACK_BAD_QUALITY_34 = 0x9A
    ACK_TIMEOUT_34 = 0x9B
    ACK_NO_SUCH_USER_35 = 0x9C
    ACK_BAD_QUALITY_35 = 0x9D
    ACK_TIMEOUT_35 = 0x9E
    ACK_NO_SUCH_USER_36 = 0x9F
    ACK_BAD_QUALITY_36 = 0xA0
    ACK_TIMEOUT_36 = 0xA1
    ACK_NO_SUCH_USER_37 = 0xA2
    ACK_BAD_QUALITY_37 = 0xA3
    ACK_TIMEOUT_37 = 0xA4
    ACK_NO_SUCH_USER_38 = 0xA5
    ACK_BAD_QUALITY_38 = 0xA6
    ACK_TIMEOUT_38 = 0xA7
    ACK_NO_SUCH_USER_39 = 0xA8
    ACK_BAD_QUALITY_39 = 0xA9
    ACK_TIMEOUT_39 = 0xAA
    ACK_NO_SUCH_USER_40 = 0xAB
    ACK_BAD_QUALITY_40 = 0xAC
    ACK_TIMEOUT_40 = 0xAD
    ACK_NO_SUCH_USER_41 = 0xAE
    ACK_BAD_QUALITY_41 = 0xAF
    ACK_TIMEOUT_41 = 0xB0
    ACK_NO_SUCH_USER_42 = 0xB1
    ACK_BAD_QUALITY_42 = 0xB2
    ACK_TIMEOUT_42 = 0xB3
    ACK_NO_SUCH_USER_43 = 0xB4
    ACK_BAD_QUALITY_43 = 0xB5
    ACK_TIMEOUT_43 = 0xB6
    ACK_NO_SUCH_USER_44 = 0xB7
    ACK_BAD_QUALITY_44 = 0xB8
    ACK_TIMEOUT_44 = 0xB9
    ACK_NO_SUCH_USER_45 = 0xBA
    ACK_BAD_QUALITY_45 = 0xBB
    ACK_TIMEOUT_45 = 0xBC
    ACK_NO_SUCH_USER_46 = 0xBD
    ACK_BAD_QUALITY_46 = 0xBE
    ACK_TIMEOUT_46 = 0xBF
    ACK_NO_SUCH_USER_47 = 0xC0
    ACK_BAD_QUALITY_47 = 0xC1
    ACK_TIMEOUT_47 = 0xC2
    ACK_NO_SUCH_USER_48 = 0xC3
    ACK_BAD_QUALITY_48 = 0xC4
    ACK_TIMEOUT_48 = 0xC5
    ACK_NO_SUCH_USER_49 = 0xC6
    ACK_BAD_QUALITY_49 = 0xC7
    ACK_TIMEOUT_49 = 0xC8
    ACK_NO_SUCH_USER_50 = 0xC9
    ACK_BAD_QUALITY_50 = 0xCA
    ACK_TIMEOUT_50 = 0xCB
    ACK_NO_SUCH_USER_51 = 0xCC
    ACK_BAD_QUALITY_51 = 0xCD
    ACK_TIMEOUT_51 = 0xCE
    ACK_NO_SUCH_USER_52 = 0xCF
    ACK_BAD_QUALITY_52 = 0xD0
    ACK_TIMEOUT_52 = 0xD1
    ACK_NO_SUCH_USER_53 = 0xD2
    ACK_BAD_QUALITY_53 = 0xD3
    ACK_TIMEOUT_53 = 0xD4
    ACK_NO_SUCH_USER_54 = 0xD5
    ACK_BAD_QUALITY_54 = 0xD6
    ACK_TIMEOUT_54 = 0xD7
    ACK_NO_SUCH_USER_55 = 0xD8
    ACK_BAD_QUALITY_55 = 0xD9
    ACK_TIMEOUT_55 = 0xDA
    ACK_NO_SUCH_USER_56 = 0xDB
    ACK_BAD_QUALITY_56 = 0xDC
    ACK_TIMEOUT_56 = 0xDD
    ACK_NO_SUCH_USER_57 = 0xDE
    ACK_BAD_QUALITY_57 = 0xDF
    ACK_TIMEOUT_57 = 0xE0
    ACK_NO_SUCH_USER_58 = 0xE1
    ACK_BAD_QUALITY_58 = 0xE2
    ACK_TIMEOUT_58 = 0xE3
    ACK_NO_SUCH_USER_59 = 0xE4
    ACK_BAD_QUALITY_59 = 0xE5
    ACK_TIMEOUT_59 = 0xE6
    ACK_NO_SUCH_USER_60 = 0xE7
    ACK_BAD_QUALITY_60 = 0xE8
    ACK_TIMEOUT_60 = 0xE9
    ACK_NO_SUCH_USER_61 = 0xEA
    ACK_BAD_QUALITY_61 = 0xEB
    ACK_TIMEOUT_61 = 0xEC
    ACK_NO_SUCH_USER_62 = 0xED
    ACK_BAD_QUALITY_62 = 0xEE
    ACK_TIMEOUT_62 = 0xEF
    ACK_NO_SUCH_USER_63 = 0xF0
    ACK_BAD_QUALITY_63 = 0xF1
    ACK_TIMEOUT_63 = 0xF2
    ACK_NO_SUCH_USER_64 = 0xF3
    ACK_BAD_QUALITY_64 = 0xF4
    ACK_TIMEOUT_64 = 0xF5
    ACK_NO_SUCH_USER_65 = 0xF6
    ACK_BAD_QUALITY_65 = 0xF7
    ACK_TIMEOUT_65 = 0xF8
    ACK_NO_SUCH_USER_66 = 0xF9
    ACK_BAD_QUALITY_66 = 0xFA
    ACK_TIMEOUT_66 = 0xFB
    ACK_NO_SUCH_USER_67 = 0xFC
    ACK_BAD_QUALITY_67 = 0xFD
    ACK_TIMEOUT_67 = 0xFE
    ACK_NO_SUCH_USER_68 = 0xFF
    
    def __init__(self, port="/dev/ttyUSB0", baudrate=57600):
        """Initialize AS608 driver"""
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.finger_id = 0
        self.confidence = 0
        
    def connect(self):
        """Connect to the fingerprint sensor"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            logger.info(f"Connected to AS608 at {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to AS608: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the fingerprint sensor"""
        if self.serial_conn:
            self.serial_conn.close()
            logger.info("Disconnected from AS608")
    
    def send_packet(self, command, data=[]):
        """Send packet to fingerprint sensor"""
        packet = [0xEF, 0x01]  # Header
        packet.extend([0xFF, 0xFF, 0xFF, 0xFF])  # Address
        packet.append(command)  # Command
        packet.append((len(data) + 2) >> 8)  # Length high
        packet.append((len(data) + 2) & 0xFF)  # Length low
        packet.extend(data)  # Data
        
        # Calculate checksum
        checksum = (packet[6] + packet[7] + sum(data)) & 0xFFFF
        packet.append(checksum >> 8)
        packet.append(checksum & 0xFF)
        
        try:
            self.serial_conn.write(bytes(packet))
            return True
        except Exception as e:
            logger.error(f"Failed to send packet: {e}")
            return False
    
    def read_packet(self, timeout=2):
        """Read packet from fingerprint sensor"""
        try:
            start_time = time.time()
            packet = []
            
            while time.time() - start_time < timeout:
                if self.serial_conn.in_waiting > 0:
                    byte = self.serial_conn.read(1)
                    if byte:
                        packet.append(ord(byte))
                        
                        # Check if we have a complete packet
                        if len(packet) >= 12:  # Minimum packet length
                            if (packet[0] == 0xEF and packet[1] == 0x01 and 
                                packet[2:6] == [0xFF, 0xFF, 0xFF, 0xFF]):
                                length = (packet[7] << 8) | packet[8]
                                if len(packet) >= length + 9:
                                    return packet
                time.sleep(0.01)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to read packet: {e}")
            return None
    
    def get_image(self):
        """Get fingerprint image"""
        if not self.send_packet(self.CMD_GET_IMAGE):
            return False
        
        packet = self.read_packet()
        if packet and packet[9] == self.ACK_SUCCESS:
            logger.info("Fingerprint image captured")
            return True
        else:
            logger.warning("Failed to capture fingerprint image")
            return False
    
    def image_2_tz(self, buffer_id=1):
        """Convert image to template"""
        if not self.send_packet(self.CMD_IMAGE_2_TZ, [buffer_id]):
            return False
        
        packet = self.read_packet()
        if packet and packet[9] == self.ACK_SUCCESS:
            logger.info("Image converted to template")
            return True
        else:
            logger.warning("Failed to convert image to template")
            return False
    
    def search_fingerprint(self, buffer_id=1, start_page=0, page_num=127):
        """Search for fingerprint in database"""
        data = [buffer_id, (start_page >> 8) & 0xFF, start_page & 0xFF, 
                (page_num >> 8) & 0xFF, page_num & 0xFF]
        
        if not self.send_packet(self.CMD_SEARCH, data):
            return False
        
        packet = self.read_packet()
        if packet and packet[9] == self.ACK_SUCCESS:
            self.finger_id = (packet[10] << 8) | packet[11]
            self.confidence = (packet[12] << 8) | packet[13]
            logger.info(f"Fingerprint found: ID={self.finger_id}, Confidence={self.confidence}")
            return True
        else:
            logger.warning("Fingerprint not found in database")
            return False
    
    def get_fingerprint(self, confidence_threshold=50):
        """Get fingerprint and search for match"""
        # Get image
        if not self.get_image():
            return None
        
        # Convert to template
        if not self.image_2_tz(1):
            return None
        
        # Search for match
        if not self.search_fingerprint(1):
            return None
        
        # Check confidence
        if self.confidence >= confidence_threshold:
            return self.finger_id
        else:
            logger.warning(f"Low confidence match: {self.confidence}")
            return None
    
    def get_template_count(self):
        """Get number of stored templates"""
        if not self.send_packet(self.CMD_TEMPLATE_COUNT):
            return 0
        
        packet = self.read_packet()
        if packet and packet[9] == self.ACK_SUCCESS:
            count = (packet[10] << 8) | packet[11]
            logger.info(f"Template count: {count}")
            return count
        else:
            logger.warning("Failed to get template count")
            return 0
