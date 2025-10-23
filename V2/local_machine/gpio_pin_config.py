#!/usr/bin/env python3
"""
GPIO Pin Configuration untuk Dual AS608 dengan Relay
Menghindari konflik dengan GPIO18 (Relay) dan GPIO19 (Exit Button)
"""

# GPIO Pin Mapping untuk Dual AS608
GPIO_PIN_MAPPING = {
    # Pin yang SUDAH DIGUNAKAN (JANGAN GUNAKAN!)
    "occupied_pins": {
        "relay": 18,        # GPIO18 - Relay Control
        "exit_button": 19,  # GPIO19 - Exit Button (jika digunakan)
        "led_status": 21    # GPIO21 - Status LED (jika digunakan)
    },
    
    # Pin untuk Sensor 1 (Hardware UART)
    "sensor_1": {
        "tx": 14,  # GPIO14 - Hardware UART TX
        "rx": 15,  # GPIO15 - Hardware UART RX
        "port": "/dev/serial0",
        "description": "Hardware UART - Primary Sensor"
    },
    
    # Pin untuk Sensor 2 (Software UART - HINDARI GPIO18!)
    "sensor_2": {
        "tx": 20,  # GPIO20 - Software UART TX (AMAN)
        "rx": 21,  # GPIO21 - Software UART RX (AMAN)
        "port": "/dev/serial1",
        "description": "Software UART - Secondary Sensor"
    },
    
    # Pin alternatif untuk Sensor 2 (jika GPIO20/21 tidak tersedia)
    "sensor_2_alternatives": {
        "option_1": {
            "tx": 22,  # GPIO22
            "rx": 23,  # GPIO23
            "description": "Alternative 1"
        },
        "option_2": {
            "tx": 24,  # GPIO24
            "rx": 25,  # GPIO25
            "description": "Alternative 2"
        },
        "option_3": {
            "tx": 26,  # GPIO26
            "rx": 27,  # GPIO27
            "description": "Alternative 3"
        }
    }
}

# Raspberry Pi 4 Physical Pin Layout
PHYSICAL_PIN_LAYOUT = {
    "power_pins": {
        "3v3_1": 1,   # Pin 1 - 3.3V
        "3v3_2": 17,  # Pin 17 - 3.3V
        "5v_1": 2,    # Pin 2 - 5V
        "5v_2": 4,    # Pin 4 - 5V
        "gnd_1": 6,   # Pin 6 - GND
        "gnd_2": 9,   # Pin 9 - GND
        "gnd_3": 14,  # Pin 14 - GND
        "gnd_4": 20,  # Pin 20 - GND
        "gnd_5": 25,  # Pin 25 - GND
        "gnd_6": 30,  # Pin 30 - GND
        "gnd_7": 34,  # Pin 34 - GND
        "gnd_8": 39,  # Pin 39 - GND
    },
    
    "gpio_pins": {
        # Sensor 1 (Hardware UART)
        8: 14,   # Pin 8 - GPIO14 (Sensor 1 TX)
        10: 15,  # Pin 10 - GPIO15 (Sensor 1 RX)
        
        # Sensor 2 (Software UART)
        38: 20,  # Pin 38 - GPIO20 (Sensor 2 TX)
        40: 21,  # Pin 40 - GPIO21 (Sensor 2 RX)
        
        # Pin yang sudah digunakan
        12: 18,  # Pin 12 - GPIO18 (RELAY - JANGAN GUNAKAN!)
        35: 19,  # Pin 35 - GPIO19 (Exit Button - JANGAN GUNAKAN!)
    }
}

# Konfigurasi UART
UART_CONFIG = {
    "hardware_uart": {
        "device": "/dev/serial0",
        "gpio_tx": 14,
        "gpio_rx": 15,
        "baudrate": 57600,
        "description": "Primary UART for Sensor 1"
    },
    
    "software_uart": {
        "device": "/dev/serial1",
        "gpio_tx": 20,
        "gpio_rx": 21,
        "baudrate": 57600,
        "description": "Secondary UART for Sensor 2"
    }
}

# Konfigurasi untuk dual sensor dengan relay
DUAL_SENSOR_GPIO_CONFIG = {
    "sensor_1": {
        "port": "/dev/serial0",
        "gpio_tx": 14,
        "gpio_rx": 15,
        "baudrate": 57600,
        "device_id": "AS608_001",
        "description": "Main Entry Sensor (Hardware UART)"
    },
    
    "sensor_2": {
        "port": "/dev/serial1",
        "gpio_tx": 20,
        "gpio_rx": 21,
        "baudrate": 57600,
        "device_id": "AS608_002",
        "description": "Secondary Entry Sensor (Software UART)"
    },
    
    "relay": {
        "gpio_pin": 18,
        "description": "Relay Control (JANGAN GUNAKAN untuk sensor!)"
    },
    
    "exit_button": {
        "gpio_pin": 19,
        "description": "Exit Button (JANGAN GUNAKAN untuk sensor!)"
    }
}

def get_safe_gpio_pins():
    """Mendapatkan pin GPIO yang aman untuk digunakan"""
    all_gpio_pins = list(range(2, 28))  # GPIO2 sampai GPIO27
    
    # Pin yang sudah digunakan
    occupied_pins = [
        GPIO_PIN_MAPPING["occupied_pins"]["relay"],
        GPIO_PIN_MAPPING["occupied_pins"]["exit_button"],
        GPIO_PIN_MAPPING["occupied_pins"]["led_status"],
        GPIO_PIN_MAPPING["sensor_1"]["tx"],
        GPIO_PIN_MAPPING["sensor_1"]["rx"],
        GPIO_PIN_MAPPING["sensor_2"]["tx"],
        GPIO_PIN_MAPPING["sensor_2"]["rx"]
    ]
    
    # Pin yang aman
    safe_pins = [pin for pin in all_gpio_pins if pin not in occupied_pins]
    
    return {
        "safe_pins": safe_pins,
        "occupied_pins": occupied_pins,
        "sensor_1_pins": [GPIO_PIN_MAPPING["sensor_1"]["tx"], GPIO_PIN_MAPPING["sensor_1"]["rx"]],
        "sensor_2_pins": [GPIO_PIN_MAPPING["sensor_2"]["tx"], GPIO_PIN_MAPPING["sensor_2"]["rx"]]
    }

def print_gpio_summary():
    """Mencetak ringkasan konfigurasi GPIO"""
    print("=" * 60)
    print("GPIO PIN CONFIGURATION SUMMARY")
    print("=" * 60)
    
    print("\n🔴 PIN YANG SUDAH DIGUNAKAN (JANGAN GUNAKAN!):")
    for name, pin in GPIO_PIN_MAPPING["occupied_pins"].items():
        print(f"  {name}: GPIO{pin}")
    
    print("\n🟢 PIN UNTUK SENSOR 1 (Hardware UART):")
    print(f"  TX: GPIO{GPIO_PIN_MAPPING['sensor_1']['tx']} (Pin 8)")
    print(f"  RX: GPIO{GPIO_PIN_MAPPING['sensor_1']['rx']} (Pin 10)")
    print(f"  Port: {GPIO_PIN_MAPPING['sensor_1']['port']}")
    
    print("\n🟢 PIN UNTUK SENSOR 2 (Software UART):")
    print(f"  TX: GPIO{GPIO_PIN_MAPPING['sensor_2']['tx']} (Pin 38)")
    print(f"  RX: GPIO{GPIO_PIN_MAPPING['sensor_2']['rx']} (Pin 40)")
    print(f"  Port: {GPIO_PIN_MAPPING['sensor_2']['port']}")
    
    print("\n🟡 PIN ALTERNATIF UNTUK SENSOR 2:")
    for option, pins in GPIO_PIN_MAPPING["sensor_2_alternatives"].items():
        print(f"  {option}: TX=GPIO{pins['tx']}, RX=GPIO{pins['rx']}")
    
    safe_pins = get_safe_gpio_pins()
    print(f"\n✅ PIN GPIO YANG AMAN: {safe_pins['safe_pins']}")
    
    print("\n⚠️  PERHATIKAN:")
    print("  - GPIO18 = RELAY CONTROL (JANGAN GUNAKAN!)")
    print("  - GPIO19 = Exit Button (JANGAN GUNAKAN!)")
    print("  - GPIO20/21 = Sensor 2 (AMAN)")
    print("  - GPIO14/15 = Sensor 1 (AMAN)")

if __name__ == "__main__":
    print_gpio_summary()
