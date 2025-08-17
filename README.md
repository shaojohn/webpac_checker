# Webpac Status Monitor

A Node.js bot that monitors the status of the Webpac library website and records response data to daily log files.

## Features

- ✅ Monitors website status and response time
- 📝 Records data to daily log files
- 🔄 Supports scheduled monitoring
- ⚡ Configurable check intervals
- 🛡️ Error handling and graceful shutdown
- 🔔 Discord webhook alerts for errors (4xx/5xx status codes or connection errors)
- 🧪 Test alert functionality

## Installation

1. Make sure you have Node.js 16+ installed
2. Install dependencies:
   ```bash
   npm install
   ```
3. **Optional**: Configure website URL and Discord webhook via environment variables:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and customize the values:
   # TARGET_URL=https://your-website-to-monitor.com
   # DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
   ```

## Usage

### Single Check
Run a single status check:
```bash
npm start
```

### Manual Scheduled Monitoring (Internal Scheduler)
Start continuous monitoring (default: every 30 minutes):
```bash
node index.js --schedule
```

Start monitoring with custom interval (e.g., every 15 minutes):
```bash
node index.js --schedule --interval 15
```

### Test Discord Alerts
Test the Discord webhook functionality:
```bash
npm run test-alert
```

### Crontab Scheduling (Linux/Ubuntu - Recommended for Production)

#### Quick Setup
1. Make the script executable:
```bash
chmod +x run-monitor.sh
```

2. Edit your crontab:
```bash
crontab -e
```

3. Add one of these lines for different intervals:

**Every 30 minutes:**
```bash
*/30 * * * * cd /path/to/webpac_checker && ./run-monitor.sh
```

**Every 15 minutes:**
```bash
*/15 * * * * cd /path/to/webpac_checker && ./run-monitor.sh
```

**Every hour at minute 0:**
```bash
0 * * * * cd /path/to/webpac_checker && ./run-monitor.sh
```

**Every 5 minutes (for testing):**
```bash
*/5 * * * * cd /path/to/webpac_checker && ./run-monitor.sh
```

#### Managing Cron Jobs
```bash
# View current cron jobs
crontab -l

# Edit cron jobs
crontab -e

# Remove all cron jobs
crontab -r

# Test the script manually
./run-monitor.sh
```

#### Cron Job with Logging
Add output redirection to track cron execution:
```bash
*/30 * * * * cd /path/to/webpac_checker && ./run-monitor.sh >> /tmp/webpac-cron.log 2>&1
```

## Log Files

Log files are created in the `logs/` directory with the format:
- Filename: `webpac-status-YYYY-MM-DD.log`
- Format: `TIMESTAMP | Status: CODE | Response Time: XXXms | Error: MESSAGE (if any)`

Example log entry:
```
2025-08-16T10:30:00.000Z | Status: 200 | Response Time: 1250ms
2025-08-16T11:00:00.000Z | Status: ERROR | Response Time: 30000ms | Error: timeout of 30000ms exceeded
```

## Configuration

The bot monitors the following URL by default:
```
https://webpac.library.gov.mo/client/zh_TW/webpac/search/results?qu=%E9%AC%BC%E6%BB%85&te=ILS
```

You can modify the target URL by setting the `TARGET_URL` environment variable in your `.env` file or by editing the default value in the `WebsiteMonitor` class constructor.

## Discord Webhook Configuration

The bot can send Discord alerts when the website returns error codes (4xx, 5xx) or experiences connection issues.

### Setup Discord Webhook:
1. Go to your Discord server
2. Right-click on a channel → Edit Channel → Integrations → Webhooks
3. Create New Webhook
4. Copy the Webhook URL
5. Set environment variables:
   ```bash
   export TARGET_URL="https://your-website-to-monitor.com"
   export DISCORD_WEBHOOK_URL="your_webhook_url_here"
   ```
   
   Or create a `.env` file:
   ```bash
   TARGET_URL=https://your-website-to-monitor.com
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
   ```

### Alert Conditions:
- HTTP status codes 400-599 (client/server errors)
- Network timeouts or connection failures
- DNS resolution errors

### Test Alerts:
```bash
npm run test-alert
```

## Scripts

- `npm start` - Run a single status check
- `npm run dev` - Run with Node.js watch mode for development
- `npm run test-alert` - Test Discord webhook alert functionality
- `npm run setup-cron` - Interactive crontab setup (Linux)
- `npm run test-monitor` - Test the monitoring script (Linux)

## Dependencies

- **axios**: HTTP client for making requests and webhook calls
- **fs-extra**: Enhanced file system operations
- **dotenv**: Environment variable loading from .env files

## License

MIT