#!/bin/bash

# Script to restart PixelParty with video support fixes

echo "🎥 Restarting PixelParty with Video Support..."

# Stop the containers
echo "📦 Stopping containers..."
docker-compose down

# Run database migration
echo "🗄️ Migrating database..."
python migrate_db.py

# Check if media directories exist and create if needed
echo "📁 Ensuring media directories exist..."
mkdir -p media/photos
mkdir -p media/videos
mkdir -p media/music
mkdir -p export
mkdir -p data

# Set proper permissions
echo "🔧 Setting permissions..."
chmod 755 media/photos
chmod 755 media/videos
chmod 755 media/music
chmod 755 export
chmod 755 data

# Rebuild and start containers
echo "🚀 Building and starting containers..."
docker-compose up --build -d

# Wait a moment for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check container status
echo "📊 Container status:"
docker-compose ps

# Show logs for debugging
echo "📝 Recent logs:"
docker-compose logs --tail=20 pixelparty-app

echo ""
echo "✅ PixelParty video support deployment complete!"
echo ""
echo "🎯 Test checklist:"
echo "   1. Upload a video file (MP4, MOV, etc.)"
echo "   2. Check that video appears in photo queue with play icon"
echo "   3. Verify video plays on big screen with text overlay"
echo "   4. Check browser console for any video errors"
echo ""
echo "🐛 If videos still don't work:"
echo "   1. Check browser console (F12) for errors"
echo "   2. Try accessing video directly: http://your-domain/media/photos/video-filename.mp4"
echo "   3. Check nginx logs: docker-compose logs nginx"
echo "   4. Check app logs: docker-compose logs pixelparty-app"