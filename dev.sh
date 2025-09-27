#!/bin/bash
# Quick development startup script

echo "🚀 Starting PixelParty Local Development"

# Activate virtual environment
source venv/bin/activate

# Setup debug environment
python debug_config.py

echo ""
echo "📍 Local development server will start on: http://localhost:5001"
echo "📍 Production continues running on: http://localhost"
echo ""
echo "💡 In another terminal, run: tail -f logs/debug.log"
echo ""

# Start Flask development server
python app.py