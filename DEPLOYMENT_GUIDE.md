# 📅 Daily Reminder System - Deployment Guide

## Overview
The daily reminder system automatically sends birthday and anniversary messages to contacts at user-specified times. It requires a scheduled task (cron job) to run every 15 minutes.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cron Job      │───▶│  FastAPI Backend │───▶│   DigitalSMS    │
│  (Every 15min)  │    │ /daily-reminders │    │   Brevo Email   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌──────────────────┐
                       │    MongoDB       │
                       │  (Logs/Stats)    │
                       └──────────────────┘
```

## 🚀 Quick Setup

### 1. Local Development / VPS
```bash
# Make script executable
chmod +x /app/setup_cron.sh

# Setup cron job (default: localhost:8001)
./setup_cron.sh

# Or specify custom backend URL
./setup_cron.sh "https://your-domain.com"
```

### 2. Docker Deployment
Add to your `Dockerfile`:
```dockerfile
# Install cron
RUN apt-get update && apt-get install -y cron

# Copy cron configuration
COPY reminder-cron /etc/cron.d/reminder-cron
RUN chmod 0644 /etc/cron.d/reminder-cron
RUN crontab /etc/cron.d/reminder-cron

# Create log file
RUN touch /var/log/reminder_cron.log

# Update CMD to start cron
CMD service cron start && python -m uvicorn server:app --host 0.0.0.0 --port 8001
```

Create `reminder-cron` file:
```
*/15 * * * * root curl -s -X POST http://localhost:8001/api/system/daily-reminders >> /var/log/reminder_cron.log 2>&1

```

## 🌐 Cloud Platform Deployment

### Heroku
```bash
# Install Heroku Scheduler addon
heroku addons:create scheduler:standard

# Add job in Heroku dashboard or CLI
heroku addons:open scheduler
# Add job: curl -X POST $API_URL/api/system/daily-reminders
# Frequency: Every 10 minutes
```

### Railway
Create `railway.json`:
```json
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "startCommand": "python -m uvicorn server:app --host 0.0.0.0 --port $PORT"
  },
  "cron": [
    {
      "command": "curl -X POST http://localhost:$PORT/api/system/daily-reminders",
      "schedule": "*/15 * * * *"
    }
  ]
}
```

### Vercel
Create `vercel.json`:
```json
{
  "functions": {
    "api/cron.py": {
      "maxDuration": 300
    }
  },
  "crons": [
    {
      "path": "/api/cron",
      "schedule": "*/15 * * * *"
    }
  ]
}
```

Create `api/cron.py`:
```python
import requests
import os
from vercel_cron import app

@app.route('/api/cron')
def cron_handler():
    backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8001')
    response = requests.post(f'{backend_url}/api/system/daily-reminders')
    return {'status': 'success', 'response': response.json()}
```

### AWS Lambda + EventBridge
```yaml
# serverless.yml
service: reminder-cron

provider:
  name: aws
  runtime: python3.9

functions:
  dailyReminders:
    handler: handler.daily_reminders
    events:
      - schedule: 
          rate: rate(15 minutes)
          enabled: true
    environment:
      BACKEND_URL: ${env:BACKEND_URL}

# handler.py
import requests
import os

def daily_reminders(event, context):
    backend_url = os.environ['BACKEND_URL']
    response = requests.post(f'{backend_url}/api/system/daily-reminders')
    return {
        'statusCode': 200,
        'body': response.json()
    }
```

### Google Cloud Scheduler
```bash
# Create scheduled job
gcloud scheduler jobs create http daily-reminders \
    --schedule="*/15 * * * *" \
    --uri="https://your-api.com/api/system/daily-reminders" \
    --http-method=POST \
    --location=us-central1
```

## 📊 Monitoring & Admin Dashboard

### Admin Endpoints
- `GET /api/admin/reminder-stats` - Daily execution statistics
- `GET /api/admin/reminder-logs` - Execution logs (last 7 days)

### Example Admin Dashboard Integration
```javascript
// Fetch daily stats
const fetchReminderStats = async (date) => {
  const response = await axios.get(`/api/admin/reminder-stats?date=${date}`);
  return response.data;
};

// Fetch execution logs
const fetchReminderLogs = async (days = 7) => {
  const response = await axios.get(`/api/admin/reminder-logs?days=${days}`);
  return response.data;
};
```

## 🔧 Configuration

### User Settings
Users can configure:
- **Daily Send Time**: When to send reminders (HH:MM format)
- **Timezone**: User's timezone for accurate timing
- **API Keys**: WhatsApp (DigitalSMS) and Email (Brevo) credentials

### System Configuration
- **Execution Frequency**: Every 15 minutes (recommended)
- **Time Window**: 15-minute tolerance for user send times
- **Credit Management**: Automatic deduction for non-unlimited users
- **Error Logging**: All errors logged for debugging

## 📝 Log Monitoring

### View Logs
```bash
# Real-time log monitoring
tail -f /var/log/reminder_cron.log

# View recent logs
tail -n 100 /var/log/reminder_cron.log

# Search for errors
grep -i error /var/log/reminder_cron.log
```

### Log Rotation (Recommended)
Create `/etc/logrotate.d/reminder-cron`:
```
/var/log/reminder_cron.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 644 root root
}
```

## 🚨 Troubleshooting

### Common Issues
1. **Cron not running**: `sudo systemctl start cron`
2. **Permission issues**: Check log file permissions
3. **Backend not responding**: Verify backend URL and port
4. **Timezone problems**: Ensure pytz is installed and configured

### Debug Commands
```bash
# Check cron status
sudo systemctl status cron

# List cron jobs
crontab -l

# Test manual execution
curl -X POST http://localhost:8001/api/system/daily-reminders

# Check backend health
curl http://localhost:8001/api/health
```

## 🔒 Security Considerations

### Internal Endpoint Protection
The `/system/daily-reminders` endpoint should be:
- Accessible only from localhost/internal network
- Protected by firewall rules
- Not exposed to public internet

### Example Nginx Configuration
```nginx
location /api/system/ {
    allow 127.0.0.1;
    allow ::1;
    deny all;
    proxy_pass http://localhost:8001;
}
```

## 📈 Scaling Considerations

### High Volume Deployments
- Use Redis for caching user settings
- Implement queue system (Celery/RQ) for message processing
- Database connection pooling
- Horizontal scaling with load balancers

### Example Celery Setup
```python
# celery_app.py
from celery import Celery

app = Celery('reminder_worker')
app.conf.broker_url = 'redis://localhost:6379/0'

@app.task
def process_reminders():
    # Call reminder processing logic
    pass

# Beat schedule
app.conf.beat_schedule = {
    'daily-reminders': {
        'task': 'celery_app.process_reminders',
        'schedule': 900.0,  # Every 15 minutes
    },
}
```

## ✅ Deployment Checklist

- [ ] Backend deployed and running
- [ ] Database connected and accessible
- [ ] Cron job configured (15-minute intervals)
- [ ] Log file created with proper permissions
- [ ] Timezone configuration verified
- [ ] Test execution completed successfully
- [ ] Admin monitoring dashboard configured
- [ ] Error alerting system setup (optional)
- [ ] Log rotation configured
- [ ] Security rules applied (internal endpoint protection)

## 📞 Support

For deployment issues:
1. Check logs: `/var/log/reminder_cron.log`
2. Verify cron status: `systemctl status cron`
3. Test manual execution: `curl -X POST /api/system/daily-reminders`
4. Check admin dashboard: `/api/admin/reminder-stats`

The daily reminder system is now ready for production deployment! 🎉