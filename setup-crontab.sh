#!/bin/bash
# Script to help set up crontab for the website monitor

echo "🔧 Setting up crontab for Webpac Status Monitor"
echo "================================================"

# Get the absolute path of the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$PROJECT_DIR/run-monitor.sh"

echo "📍 Project Directory: $PROJECT_DIR"
echo "📄 Script Path: $SCRIPT_PATH"

# Make the run script executable
chmod +x "$SCRIPT_PATH"
echo "✅ Made run-monitor.sh executable"

echo ""
echo "📋 Available crontab options:"
echo "1. Every 5 minutes (for testing)"
echo "2. Every 15 minutes"
echo "3. Every 30 minutes (recommended)"
echo "4. Every hour"
echo "5. Custom interval"
echo "6. Just show the crontab lines (don't install)"

read -p "Choose an option (1-6): " choice

case $choice in
    1)
        CRON_LINE="*/5 * * * * cd $PROJECT_DIR && ./run-monitor.sh"
        DESCRIPTION="every 5 minutes"
        ;;
    2)
        CRON_LINE="*/15 * * * * cd $PROJECT_DIR && ./run-monitor.sh"
        DESCRIPTION="every 15 minutes"
        ;;
    3)
        CRON_LINE="*/30 * * * * cd $PROJECT_DIR && ./run-monitor.sh"
        DESCRIPTION="every 30 minutes"
        ;;
    4)
        CRON_LINE="0 * * * * cd $PROJECT_DIR && ./run-monitor.sh"
        DESCRIPTION="every hour"
        ;;
    5)
        read -p "Enter interval in minutes: " interval
        CRON_LINE="*/$interval * * * * cd $PROJECT_DIR && ./run-monitor.sh"
        DESCRIPTION="every $interval minutes"
        ;;
    6)
        echo ""
        echo "📋 Copy and paste these lines into your crontab (crontab -e):"
        echo ""
        echo "# Every 5 minutes (testing):"
        echo "*/5 * * * * cd $PROJECT_DIR && ./run-monitor.sh"
        echo ""
        echo "# Every 15 minutes:"
        echo "*/15 * * * * cd $PROJECT_DIR && ./run-monitor.sh"
        echo ""
        echo "# Every 30 minutes (recommended):"
        echo "*/30 * * * * cd $PROJECT_DIR && ./run-monitor.sh"
        echo ""
        echo "# Every hour:"
        echo "0 * * * * cd $PROJECT_DIR && ./run-monitor.sh"
        echo ""
        echo "# With logging:"
        echo "*/30 * * * * cd $PROJECT_DIR && ./run-monitor.sh >> /tmp/webpac-cron.log 2>&1"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🔄 Adding crontab entry to run $DESCRIPTION..."
echo "Cron line: $CRON_LINE"

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Crontab entry added successfully!"
    echo ""
    echo "📋 Current crontab:"
    crontab -l | grep -E "(webpac|run-monitor)"
    echo ""
    echo "🧪 To test manually: $SCRIPT_PATH"
    echo "📊 Check logs in: $PROJECT_DIR/logs/"
    echo "🗑️  To remove cron job: crontab -e"
else
    echo "❌ Failed to add crontab entry"
    exit 1
fi