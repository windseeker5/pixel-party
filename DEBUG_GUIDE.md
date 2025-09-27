# PixelParty Debugging Guide

## Overview

This guide helps you debug PixelParty while keeping the production Docker container running. The approach uses shared Docker volumes so your local debug environment uses the same database and media files as the live production app.

## Quick Start

```bash
# 1. Setup debug environment
python debug_start.py

# 2. Run local debug server (port 5001)
python app.py

# 3. Test YouTube functionality
python test_youtube.py

# 4. Monitor live container logs
docker logs -f pixelparty-app
```

## Architecture Understanding

### Docker Volume Mappings

Your production container uses these volume mappings:

```yaml
volumes:
  - ./media:/app/media           # Photos, videos, music
  - ./data:/app/data             # SQLite database
  - ./export:/app/export         # Memory book exports
  - ./import:/app/import         # Import directory
```

This means:
- **Database**: `./data/birthday_party.db` is shared between container and local
- **Media files**: `./media/` is shared between container and local
- **Changes in either environment are immediately visible to both**

### Port Configuration

- **Production container**: Internal port 5000 → Nginx → ports 80/443
- **Local debug server**: Port 5001 (configured in app.py line 31)
- **No port conflicts** - both can run simultaneously

## Debugging Workflow

### 1. Initial Setup

```bash
# Check prerequisites and setup environment
python debug_start.py
```

This script:
- ✅ Verifies Python version and project structure
- ✅ Checks production data availability
- ✅ Configures environment variables for production database
- ✅ Sets up enhanced logging
- ✅ Tests Docker container status

### 2. Local Development Server

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start debug server
python app.py
```

**Environment configured automatically:**
- `FLASK_CONFIG=development`
- `DATABASE_URL=sqlite:///./data/birthday_party.db` (production DB)
- `FLASK_DEBUG=1`
- Enhanced logging enabled

**Debug server features:**
- 🔥 Hot reload on code changes
- 📝 Detailed error messages
- 🎯 Same data as production
- 🚀 No need to stop production

### 3. Testing YouTube Issues

```bash
# Run comprehensive YouTube tests
python test_youtube.py
```

**Test coverage:**
- ✅ yt-dlp installation and version
- ✅ Basic YouTube search functionality
- ✅ YouTubeAudioService class functionality
- ✅ Directory permissions
- ✅ Ollama connection (for music suggestions)
- ✅ Actual download test (with cleanup)

### 4. Log Monitoring

#### Enhanced Local Logs
Enhanced logging is automatically configured:
```bash
# Watch debug log file
tail -f logs/debug.log
```

**Log features:**
- 🎵 YouTube search/download entry points
- ❌ Detailed error messages with full stack traces
- 🔍 Debug info (URLs, filenames, directory permissions)
- 📍 Function names and line numbers

#### Production Container Logs
```bash
# Watch live container logs
docker logs -f pixelparty-app

# Filter for specific errors
docker logs pixelparty-app 2>&1 | grep -E "ERROR|YouTube|music"

# Last 50 lines
docker logs --tail 50 pixelparty-app
```

## Common Debugging Scenarios

### YouTube "Error" Issues

**Symptoms:**
- Users see "error" when requesting YouTube music
- No specific error details

**Debug steps:**

1. **Check logs first:**
```bash
# Local debug logs
tail -f logs/debug.log | grep -E "YouTube|ERROR"

# Container logs
docker logs pixelparty-app 2>&1 | grep -E "YouTube|ERROR"
```

2. **Test YouTube functionality:**
```bash
python test_youtube.py
```

3. **Check specific issues:**

**yt-dlp version issues:**
```bash
pip list | grep yt-dlp
# If outdated: pip install --upgrade yt-dlp
```

**Network/firewall issues:**
```bash
# Test basic connectivity
curl -I https://www.youtube.com

# Test from container
docker exec -it pixelparty-app curl -I https://www.youtube.com
```

**Directory permissions:**
```bash
ls -la media/music/
# Should be writable by your user
```

**Ollama connection:**
```bash
curl http://127.0.0.1:11434/api/tags
```

### Database Issues

**Check database integrity:**
```bash
sqlite3 data/birthday_party.db ".tables"
sqlite3 data/birthday_party.db "SELECT COUNT(*) FROM photos;"
sqlite3 data/birthday_party.db "SELECT COUNT(*) FROM music_queue;"
```

**Backup database:**
```bash
cp data/birthday_party.db data/birthday_party_backup_$(date +%Y%m%d_%H%M%S).db
```

### File Upload Issues

**Check media directory:**
```bash
ls -la media/
ls -la media/photos/
ls -la media/videos/
```

**Check permissions:**
```bash
# Should be writable
touch media/photos/test_write && rm media/photos/test_write
```

## Advanced Debugging

### Container Shell Access

```bash
# Access running container
docker exec -it pixelparty-app /bin/bash

# Inside container, check:
cd /app
python -c "from app.services.youtube_service import get_youtube_service; print('OK')"
```

### Database Inspection

```bash
# Connect to production database
sqlite3 data/birthday_party.db

# Useful queries:
.tables
.schema photos
SELECT name, COUNT(*) FROM photos GROUP BY name;
SELECT * FROM music_queue ORDER BY submitted_at DESC LIMIT 5;
SELECT * FROM settings;
```

### Network Analysis

```bash
# Check which ports are in use
netstat -tlnp | grep -E ":80|:443|:5000|:5001"

# Test local debug server
curl http://localhost:5001/health

# Test production nginx
curl http://localhost/health
```

## Logging Configuration

### Enhanced YouTube Service Logging

The YouTube service now includes:
- 🎵 Entry point logging for all method calls
- ❌ Detailed error messages with full context
- 🔍 Debug information (versions, paths, permissions)
- 📍 Function names and line numbers in logs

### Log Files

```bash
logs/
├── debug.log          # All debug output
└── error.log          # Error-level only (future)
```

### Log Levels

- `DEBUG`: Detailed function entry/exit, variable values
- `INFO`: Important operations (search start, download start)
- `WARNING`: Recoverable issues
- `ERROR`: Failures with full context and debug info

## Troubleshooting Checklist

### Before Starting Debug Session

- [ ] Production container is running (`docker ps`)
- [ ] Database file exists (`ls -la data/birthday_party.db`)
- [ ] Media directory is accessible (`ls -la media/`)
- [ ] Virtual environment is active
- [ ] Dependencies are installed (`pip install -r requirements.txt`)

### When YouTube Errors Occur

- [ ] Run `python test_youtube.py` to isolate the issue
- [ ] Check `logs/debug.log` for detailed error info
- [ ] Verify yt-dlp version (`pip show yt-dlp`)
- [ ] Test network connectivity to YouTube
- [ ] Check media directory permissions
- [ ] Verify Ollama is running (if using music suggestions)

### When Making Code Changes

- [ ] Test locally first (`python app.py`)
- [ ] Check logs for any new errors
- [ ] Verify functionality with test script
- [ ] Only deploy to container when confident

## Key Files

| File | Purpose |
|------|---------|
| `debug_config.py` | Environment setup for debugging |
| `debug_start.py` | Complete debug environment setup |
| `test_youtube.py` | YouTube functionality testing |
| `logs/debug.log` | Enhanced debug logging output |
| `DEBUG_GUIDE.md` | This comprehensive guide |

## Best Practices

1. **Always use the debug environment** - Don't guess, use the tools
2. **Test changes locally first** - Verify before touching production
3. **Monitor both logs** - Local debug logs + container logs
4. **Keep backups** - Database and important config files
5. **Use version control** - Commit working states
6. **Document issues** - Note what worked/didn't work

## Emergency Procedures

### If Production Breaks

1. **Check container status:**
```bash
docker ps
docker logs pixelparty-app --tail 50
```

2. **Restart container if needed:**
```bash
docker-compose restart pixelparty-app
```

3. **Restore database if corrupted:**
```bash
# Stop container
docker-compose stop pixelparty-app

# Restore backup
cp data/birthday_party_backup_[timestamp].db data/birthday_party.db

# Start container
docker-compose start pixelparty-app
```

### If Debug Environment Breaks

1. **Reset environment:**
```bash
python debug_config.py
```

2. **Reinstall dependencies:**
```bash
pip install -r requirements.txt
```

3. **Clear logs:**
```bash
rm -f logs/debug.log
```

---

Remember: **The goal is to debug safely while keeping the party going!** 🎉