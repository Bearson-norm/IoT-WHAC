# WHAC Fingerprint System - Web UI

A modern web interface for displaying and managing fingerprint data from PostgreSQL database.

## 🎯 Features

- ✅ **Real-time Dashboard** - Live statistics and charts
- ✅ **Fingerprint Logs** - View all scan records
- ✅ **Action Logs** - Track access granted/denied
- ✅ **User Management** - Add/delete users
- ✅ **Responsive Design** - Works on desktop and mobile
- ✅ **Auto-refresh** - Updates every 30 seconds

## 📊 Database Schema

### Tables Used:
- **`log_data`** - Fingerprint scan records
- **`log_action`** - Access granted/denied actions
- **`store_001`** - User information

### Database Configuration:
- **Database**: `whac_master`
- **Username**: `postgres`
- **Password**: `Admin123`
- **Host**: `localhost`
- **Port**: `5432`

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
cd web_ui/
pip install -r requirements.txt
```

### 2. Setup PostgreSQL Database
```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create database
CREATE DATABASE whac_master;

# Connect to the database
\c whac_master

# Run the setup script
\i database_setup.sql
```

### 3. Run the Web Application
```bash
python app.py
```

### 4. Access the Web Interface
Open your browser and go to: `http://localhost:5000`

## 📱 Web Interface Features

### Dashboard
- **Total Users** - Number of registered users
- **Scans Today** - Daily scan count
- **Access Granted** - Successful access today
- **Access Denied** - Failed access today

### Charts
- **Daily Scans Chart** - Line chart showing scans over time
- **Access Status Chart** - Pie chart showing granted vs denied

### Fingerprint Logs
- View all fingerprint scan records
- Pagination support
- Real-time updates
- Shows user_id, username, timestamp, template_id

### Action Logs
- Track all access attempts
- Shows granted/denied status
- Color-coded status badges
- Timestamp information

### User Management
- Add new users
- Delete existing users
- View user statistics
- Template ID management

## 🔧 API Endpoints

### Dashboard
- `GET /api/dashboard_stats` - Get dashboard statistics

### Logs
- `GET /api/logs?page=1&per_page=20` - Get fingerprint logs
- `GET /api/action_logs?page=1&per_page=20` - Get action logs

### Users
- `GET /api/users` - Get all users
- `POST /api/add_user` - Add new user
- `DELETE /api/delete_user/<id>` - Delete user

### Charts
- `GET /api/charts/daily_stats?days=7` - Get daily statistics

## 📊 Data Flow

```
Fingerprint Sensor → MQTT → Server → PostgreSQL → Web UI
```

1. **Fingerprint sensor** scans and sends data via MQTT
2. **Server** receives data and stores in PostgreSQL
3. **Web UI** displays data from PostgreSQL database
4. **Real-time updates** every 30 seconds

## 🎨 UI Components

### Bootstrap 5
- Modern, responsive design
- Mobile-friendly interface
- Professional styling

### Chart.js
- Interactive charts
- Real-time data visualization
- Responsive charts

### Font Awesome
- Professional icons
- Consistent iconography
- Enhanced user experience

## 🔒 Security Considerations

- Database credentials in code (move to environment variables for production)
- No authentication implemented (add for production use)
- CORS not configured (add if needed for cross-origin requests)

## 🚀 Production Deployment

### Environment Variables
Create a `.env` file:
```
DB_HOST=localhost
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
DB_PORT=5432
```

### WSGI Server
For production, use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Nginx Reverse Proxy
Configure Nginx to serve the application:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📝 Notes

- The web UI is designed for **Store 001** only as specified
- `user_id` can be null for unmatched fingerprints
- All timestamps are stored in UTC
- Charts show data for the last 7 days by default
- Pagination is set to 20 items per page

This web interface provides a complete solution for monitoring and managing your fingerprint system!

