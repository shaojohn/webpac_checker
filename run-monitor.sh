#!/bin/bash
# Shell script to run the website monitor
# Make sure this script is executable: chmod +x run-monitor.sh

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Run the Node.js application
node index.js