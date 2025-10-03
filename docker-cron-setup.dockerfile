# Docker setup for Daily Reminder System
# Add this to your existing Dockerfile

# Install cron
RUN apt-get update && apt-get install -y cron && apt-get clean

# Create cron job file
COPY <<EOF /etc/cron.d/reminder-cron
*/15 * * * * root curl -s -X POST http://localhost:8001/api/system/daily-reminders >> /var/log/reminder_cron.log 2>&1
# Empty line required at end
EOF

# Set permissions for cron
RUN chmod 0644 /etc/cron.d/reminder-cron
RUN crontab /etc/cron.d/reminder-cron

# Create log file
RUN touch /var/log/reminder_cron.log

# Update the startup command to include cron
# Replace your existing CMD with:
CMD service cron start && python -m uvicorn server:app --host 0.0.0.0 --port 8001