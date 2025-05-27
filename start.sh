#!/bin/bash

# Startup script for Restricted Message Bot

echo "🤖 Starting Restricted Message Bot..."

# Check if .env file exists
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env file..."
    source .env
else
    echo "⚠️  No .env file found. Please create one based on .env.example"
    echo "💡 Run: cp .env.example .env"
    exit 1
fi

# Check if required variables are set
if [ -z "$TELEGRAM_API_ID" ] || [ -z "$TELEGRAM_API_HASH" ]; then
    echo "❌ Missing required environment variables!"
    echo "Please set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env file"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📥 Installing/updating dependencies..."
pip install -r requirements.txt

echo "🚀 Starting bot..."
python3 main.py
