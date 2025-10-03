#!/bin/bash

# Daily Reminder System Setup Script
# This script sets up the cron job for the birthday/anniversary reminder system

echo "🚀 Setting up Daily Reminder System..."

# Get the backend URL (default to localhost if not provided)
BACKEND_URL=${1:-"http://localhost:8001"}

echo "Backend URL: $BACKEND_URL"

# Create the cron job entry
CRON_JOB="*/15 * * * * curl -s -X POST $BACKEND_URL/api/system/daily-reminders >> /var/log/reminder_cron.log 2>&1"

# Create log file if it doesn't exist
sudo touch /var/log/reminder_cron.log
sudo chmod 666 /var/log/reminder_cron.log

# Add cron job to current user's crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job added successfully!"
echo "📋 Cron job: $CRON_JOB"
echo "📄 Logs will be written to: /var/log/reminder_cron.log"
echo ""
echo "📊 To view logs in real-time:"
echo "   tail -f /var/log/reminder_cron.log"
echo ""
echo "🔍 To check if cron is running:"
echo "   sudo systemctl status cron"
echo ""
echo "📝 To list current cron jobs:"
echo "   crontab -l"
echo ""
echo "❌ To remove the cron job later:"
echo "   crontab -e  # Then delete the reminder line"
echo ""
echo "🔄 The reminder system will now run every 15 minutes!"
echo "   - Checks all users' preferred send times"
echo "   - Sends birthday and anniversary reminders"
echo "   - Logs all activities for monitoring"