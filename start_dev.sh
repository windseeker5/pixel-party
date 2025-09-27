#!/bin/bash
# Quick development startup with correct production database

echo "🚀 Starting PixelParty Local Development with Production Data"
echo "=================================================="

# Activate virtual environment
source venv/bin/activate

# Set environment variables to use production data
export FLASK_CONFIG=development
export DATABASE_URL="sqlite:///$(pwd)/data/birthday_party.db"
export FLASK_ENV=development
export FLASK_DEBUG=1

# Verify database exists and has data
if [ -f "data/birthday_party.db" ]; then
    PHOTO_COUNT=$(sqlite3 data/birthday_party.db "SELECT COUNT(*) FROM photos;")
    GUEST_COUNT=$(sqlite3 data/birthday_party.db "SELECT COUNT(*) FROM guests;")
    MUSIC_COUNT=$(sqlite3 data/birthday_party.db "SELECT COUNT(*) FROM music_queue;")
    echo "✅ Using production database:"
    echo "   📸 Photos: $PHOTO_COUNT"
    echo "   👥 Guests: $GUEST_COUNT"
    echo "   🎵 Music queue: $MUSIC_COUNT"
else
    echo "❌ Production database not found at data/birthday_party.db"
    exit 1
fi

echo ""
echo "📍 Local development server starting on: http://localhost:5001"
echo "📍 Production continues running on: http://localhost"
echo "📍 Same database, same photos, same data!"
echo ""
echo "💡 To monitor logs: tail -f logs/debug.log"
echo "💡 To stop: Ctrl+C"
echo ""

# Start Flask development server
python app.py