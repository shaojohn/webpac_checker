const axios = require('axios');
const fs = require('fs-extra');
const path = require('path');
const moment = require('moment-timezone');

// Load environment variables from .env file if it exists
const dotenv = require('dotenv');
dotenv.config();

class WebsiteMonitor {
    constructor() {
        // Read target URL from environment variable, with default fallback
        this.targetUrl = process.env.TARGET_URL || 'https://webpac.library.gov.mo/client/zh_TW/webpac/search/results?qu=%E9%AC%BC%E6%BB%85&te=ILS';
        // Read Discord webhook URL from environment variable, with default fallback
        this.webhookUrl = process.env.DISCORD_WEBHOOK_URL || 'https://discord.com/api/webhooks/channelid/ttttoken';
        // Read timezone from environment variable, fallback to UTC
        this.timezone = process.env.TIMEZONE || 'UTC';
        this.logsDir = path.join(__dirname, 'logs');
        this.ensureLogsDirExists();
    }

    async ensureLogsDirExists() {
        try {
            await fs.ensureDir(this.logsDir);
        } catch (error) {
            console.error('Error creating logs directory:', error);
        }
    }

    getCurrentDateString() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    getCurrentTimeString() {
        // Use moment-timezone to format timestamp in the configured timezone
        let now = moment();
        let formatted;
        try {
            formatted = now.tz(this.timezone).format('YYYY-MM-DDTHH:mm:ss.SSSZ');
        } catch (e) {
            // fallback to UTC if timezone is invalid
            formatted = now.utc().format('YYYY-MM-DDTHH:mm:ss.SSS[Z]');
        }
        return formatted;
    }

    getLogFilePath() {
        const dateString = this.getCurrentDateString();
        return path.join(this.logsDir, `webpac-status-${dateString}.log`);
    }

    async sendDiscordAlert(result) {
        if (!this.webhookUrl) {
            console.log('🔕 No webhook URL configured, skipping Discord alert');
            return;
        }

        try {
            const isError = result.statusCode === 'ERROR' || (typeof result.statusCode === 'number' && result.statusCode >= 400);
            
            if (!isError) {
                return; // Only send alerts for errors
            }

            const embed = {
                title: "🚨 Website Status Alert",
                color: 0xff0000, // Red color
                fields: [
                    {
                        name: "Website",
                        value: this.targetUrl,
                        inline: false
                    },
                    {
                        name: "Status Code",
                        value: result.statusCode.toString(),
                        inline: true
                    },
                    {
                        name: "Response Time",
                        value: `${result.responseTime}ms`,
                        inline: true
                    },
                    {
                        name: "Timestamp",
                        value: result.timestamp,
                        inline: false
                    }
                ],
                footer: {
                    text: "Webpac Status Monitor"
                }
            };

            if (result.error) {
                embed.fields.push({
                    name: "Error Details",
                    value: result.error,
                    inline: false
                });
            }

            const webhookPayload = {
                content: "🚨 **Website Alert!** The monitored website is experiencing issues.",
                embeds: [embed]
            };

            const response = await axios.post(this.webhookUrl, webhookPayload, {
                headers: {
                    'Content-Type': 'application/json'
                },
                timeout: 10000
            });

            console.log('🔔 Discord alert sent successfully');
            
        } catch (error) {
            console.error('❌ Failed to send Discord alert:', error.message);
        }
    }

    async checkWebsiteStatus() {
        const startTime = Date.now();
        let statusCode = null;
        let responseTime = null;
        let error = null;

        try {
            console.log(`Checking website status: ${this.targetUrl}`);
            
            const response = await axios.get(this.targetUrl, {
                timeout: 30000, // 30 seconds timeout
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            });
            
            statusCode = response.status;
            responseTime = Date.now() - startTime;
            
            console.log(`✅ Status: ${statusCode}, Response Time: ${responseTime}ms`);
            
        } catch (err) {
            responseTime = Date.now() - startTime;
            statusCode = err.response ? err.response.status : 'ERROR';
            error = err.message;
            
            console.log(`❌ Status: ${statusCode}, Response Time: ${responseTime}ms, Error: ${error}`);
        }

        return {
            timestamp: this.getCurrentTimeString(),
            statusCode,
            responseTime,
            error
        };
    }

    async logResult(result) {
        const logFilePath = this.getLogFilePath();
        const logEntry = `${result.timestamp} | Status: ${result.statusCode} | Response Time: ${result.responseTime}ms${result.error ? ` | Error: ${result.error}` : ''}\n`;
        
        try {
            await fs.appendFile(logFilePath, logEntry);
            console.log(`📝 Logged to: ${logFilePath}`);
        } catch (error) {
            console.error('Error writing to log file:', error);
        }
    }

    async testDiscordAlert() {
        console.log('🧪 Testing Discord alert functionality...');
        
        // Simulate an error condition
        const testResult = {
            timestamp: this.getCurrentTimeString(),
            statusCode: 500,
            responseTime: 30000,
            error: 'Internal Server Error - Test Alert'
        };
        
        await this.sendDiscordAlert(testResult);
        console.log('✅ Test alert completed');
    }

    async run() {
        console.log('🚀 Website Monitor Started');
        console.log(`📍 Target URL: ${this.targetUrl}`);
        console.log(`📁 Logs Directory: ${this.logsDir}`);
        console.log(`🔔 Discord Webhook: ${this.webhookUrl ? 'Configured' : 'Not configured'}`);
        console.log('---');

        const result = await this.checkWebsiteStatus();
        await this.logResult(result);
        
        // Send Discord alert if there's an error
        await this.sendDiscordAlert(result);
        
        console.log('---');
        console.log('✅ Monitoring check completed');
    }

    async startScheduledMonitoring(intervalMinutes = 30) {
        console.log(`🔄 Starting scheduled monitoring every ${intervalMinutes} minutes`);
        
        // Run initial check
        await this.run();
        
        // Schedule recurring checks
        setInterval(async () => {
            await this.run();
        }, intervalMinutes * 60 * 1000);
    }
}

// Main execution
async function main() {
    const monitor = new WebsiteMonitor();
    
    // Check command line arguments
    const args = process.argv.slice(2);
    
    if (args.includes('--test-alert')) {
        await monitor.testDiscordAlert();
    } else if (args.includes('--schedule')) {
        const intervalIndex = args.indexOf('--interval');
        const interval = intervalIndex !== -1 && args[intervalIndex + 1] ? parseInt(args[intervalIndex + 1]) : 30;
        await monitor.startScheduledMonitoring(interval);
    } else {
        // For scheduled tasks (cron/Task Scheduler), just run once
        await monitor.run();
    }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n👋 Gracefully shutting down...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n👋 Gracefully shutting down...');
    process.exit(0);
});

// Start the application
if (require.main === module) {
    main().catch(console.error);
}

module.exports = WebsiteMonitor;