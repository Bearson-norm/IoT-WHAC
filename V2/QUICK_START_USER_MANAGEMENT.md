# Quick Start Guide - Enhanced User Management Features

This guide will help you quickly get started with the new user management and enhanced logging features.

## 🚀 Quick Setup

### 1. Migrate Database (First Time Only)
If you have an existing database with the simple schema, you need to migrate it first:
```bash
cd local_machine
python3 migrate_database.py
```

### 2. Start the Enhanced User Controller
```bash
cd local_machine
python3 fingerprint_user_controller.py
```

### 3. Start the Web UI (if not already running)
```bash
cd web_ui
python3 app.py
```

### 3. Access the Enhanced Log Reports
Open your browser and navigate to:
```
http://localhost:5000/logs_report
```

## 🎯 Key Features Overview

### Enhanced User Management
- **Advanced user profiles** with department, access levels, and notes
- **MQTT-based commands** for remote user management
- **Comprehensive user statistics** and activity tracking
- **Bulk operations** and data export capabilities

### Advanced Logging & Reporting
- **Multi-parameter filtering** (user, date, store, action type)
- **Dynamic sorting** by any column
- **Real-time statistics** and analytics
- **Interactive charts** and visualizations
- **CSV export** with custom filtering

### Command Line Interface
- **Interactive menu system** for easy management
- **System diagnostics** and connection testing
- **MQTT command interface** for remote operations

## 📊 Using the Enhanced Log Reports

### 1. Access the Interface
- Navigate to `http://localhost:5000/logs_report`
- Login with your admin credentials

### 2. Apply Filters
- **Log Type**: Choose between Fingerprint Logs or Action Logs
- **User ID**: Filter by specific user
- **Date Range**: Set start and end dates
- **Sort Options**: Choose column and sort order
- **Records Per Page**: Adjust pagination size

### 3. View Analytics
- **Summary Statistics**: Total scans, unique users, success rates
- **Daily Activity Chart**: Visual representation of daily activity
- **Top Users Chart**: Most active users by scan count

### 4. Export Data
- Click the "Export" button to download filtered data as CSV
- Files are automatically named with timestamp

## 🖥️ Using the Command Line Interface

### 1. Start the CLI
```bash
cd local_machine
python3 user_management_cli.py
```

### 2. Available Commands
- **List Users**: View all users with optional filtering
- **Get User Info**: Retrieve detailed user information
- **Update User**: Modify user profiles and settings
- **Activate/Deactivate**: Change user status
- **Delete User**: Remove users from the system
- **Get Statistics**: View user and system statistics
- **Export Users**: Export user data to CSV/JSON
- **View Logs**: Browse verification logs
- **System Stats**: Get comprehensive system statistics
- **Test Connections**: Verify MQTT and sensor connectivity

### 3. Example Usage
```
Select option (1-12): 1
Show only active users? (y/N): y
Filter by department (optional): IT
```

## 📡 MQTT Commands

### Send Commands via MQTT Client
All commands are sent to topic: `WHAC/Store001/user_mgmt`

#### List All Users
```json
{
    "command": "list_users",
    "data": {
        "active_only": true,
        "department": "IT"
    }
}
```

#### Get User Information
```json
{
    "command": "get_user_info",
    "data": {
        "fingerprint_id": 1
    }
}
```

#### Update User Profile
```json
{
    "command": "update_user",
    "data": {
        "fingerprint_id": 1,
        "user_name": "John Doe",
        "department": "IT",
        "access_level": 2,
        "notes": "Updated profile"
    }
}
```

## 🔧 Configuration

### Environment Variables
The system uses the same configuration as `fingerprint_simple_client.py`:

```bash
# Store Configuration
STORE_ID=Store001

# MQTT Configuration
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883

# Fingerprint Sensor Configuration
FINGERPRINT_PORT=/dev/serial0
BAUD_RATE=57600
```

### Database Setup
- **Local Machine**: SQLite database (`fingerprints.db`)
- **Web UI**: PostgreSQL database (`whac_master`)

## 📈 Key Benefits

### For Administrators
- **Complete user lifecycle management**
- **Detailed activity monitoring**
- **Advanced reporting and analytics**
- **Easy data export and analysis**

### For System Monitoring
- **Real-time statistics dashboard**
- **Historical trend analysis**
- **Performance metrics tracking**
- **Automated reporting capabilities**

### For Data Analysis
- **Flexible filtering options**
- **Multiple export formats**
- **Statistical analysis tools**
- **Visual data representation**

## 🛠️ Troubleshooting

### Common Issues

#### MQTT Connection Failed
```bash
# Test MQTT connection using CLI
python3 user_management_cli.py
# Select option 10: Test MQTT connection
```

#### Fingerprint Sensor Not Found
```bash
# Test sensor connection using CLI
python3 user_management_cli.py
# Select option 11: Test fingerprint sensor
```

#### Web UI Not Loading
```bash
# Check if Flask app is running
cd web_ui
python3 app.py
```

#### Database Errors
- Verify database permissions
- Check database connectivity
- Ensure proper schema initialization

### Debug Commands
Use the CLI interface for system diagnostics:
- **Option 10**: Test MQTT connection
- **Option 11**: Test fingerprint sensor
- **Option 9**: Get system statistics

### Database Migration Issues
If you encounter database-related errors:

#### Error: "no such column: user_id"
This means your database still has the simple schema. Run the migration:
```bash
cd local_machine
python3 migrate_database.py
```

#### Test the Migration
Run the test suite to verify everything works:
```bash
cd local_machine
python3 test_user_management.py
```

#### Manual Database Check
Check your database schema:
```bash
cd local_machine
sqlite3 fingerprints.db ".schema users"
```

## 📝 Response Format

All MQTT responses are sent to topic: `WHAC/Store001/user_mgmt_response`

### Success Response Example
```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-15T10:30:00",
    "command": "list_users",
    "status": "success",
    "data": {
        "users": [
            {
                "fingerprint_id": 1,
                "user_name": "John Doe",
                "department": "IT",
                "access_level": 2,
                "is_active": true
            }
        ],
        "total_count": 1
    },
    "device_id": "AS608_001"
}
```

## 🎉 Next Steps

1. **Explore the Web Interface**: Try different filters and sorting options
2. **Test MQTT Commands**: Send commands via MQTT client
3. **Use the CLI**: Familiarize yourself with the command-line interface
4. **Export Data**: Generate reports for analysis
5. **Monitor Statistics**: Track system performance and user activity

## 📚 Additional Resources

- **Full Documentation**: `USER_MANAGEMENT_FEATURES.md`
- **Test Suite**: `tests/test_user_management.py`
- **Configuration**: `local_machine/config.py`
- **Database Schema**: `web_ui/database_setup.sql`

The enhanced user management system provides a complete solution for managing users and analyzing system activity, building upon the existing `fingerprint_simple_client.py` foundation while adding powerful new capabilities for monitoring and reporting.
