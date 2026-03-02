#!/bin/bash

# Configuration
PROJECT_DIR="/Users/jw/Desktop/japanese-restaurant"
LOG_DIR="$PROJECT_DIR/.tmp"
WEBHOOK_LOG="$LOG_DIR/webhook_receiver.log"
NGROK_DOMAIN="jayceon-superadditional-lochlan.ngrok-free.dev"

mkdir -p "$LOG_DIR"

cd "$PROJECT_DIR"

# 1. Check if webhook_receiver.py is running
if ! pgrep -f "webhook_receiver.py" > /dev/null; then
    echo "$(date): Restarting webhook_receiver.py..." >> "$WEBHOOK_LOG"
    /usr/bin/python3 execution/webhook_receiver.py >> "$WEBHOOK_LOG" 2>&1 &
fi

# 2. Check if ngrok is running
if ! pgrep -f "ngrok http" > /dev/null; then
    echo "$(date): Restarting ngrok..." >> "$WEBHOOK_LOG"
    # Starting ngrok with the specific domain
    ngrok http --domain="$NGROK_DOMAIN" 5001 >> "$WEBHOOK_LOG" 2>&1 &
fi

echo "$(date): Health check complete." >> "$WEBHOOK_LOG"
