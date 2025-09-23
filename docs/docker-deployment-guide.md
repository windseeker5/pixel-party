# PixelParty Docker Deployment Guide

## Deployment Status: READY ✅

Your Docker setup is mostly correct and ready for deployment with minor fixes needed.

## 🔴 Critical Issues to Fix Before Deployment

### 1. Missing `curl` in Dockerfile
The healthcheck requires `curl` but it's not installed in the container.

**Fix:** Update `Dockerfile` (line 11-15):
```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    curl \  # ADD THIS LINE
    && rm -rf /var/lib/apt/lists/*
```

### 2. Create `.env` File
Create a `.env` file in the project root with your configuration:

```bash
# Required environment variables
CERTBOT_EMAIL=your-email@example.com
DOMAIN=your-domain.com  # e.g., party.dresdell.com
SECRET_KEY=your-super-secret-key-here  # Generate a secure random key
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

**Generate a secure secret key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Update Nginx SSL Certificate Paths
The nginx config has hardcoded SSL paths. Update `nginx/default.conf` (lines 28-29):

**Current (hardcoded):**
```nginx
ssl_certificate /etc/letsencrypt/live/party.dresdell.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/party.dresdell.com/privkey.pem;
```

**Should be (using environment variable):**
```nginx
ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
```

## ✅ Already Configured Correctly

- **USB Music Library Mount**: ✅ Correctly mapped at `/mnt/pixelparty/Music`
- **Ollama Connectivity**: ✅ Using `host.docker.internal:11434`
- **Media Persistence**: ✅ All media folders mounted as volumes
- **Database Persistence**: ✅ SQLite database stored in `./data` volume
- **Static Files**: ✅ Served directly by nginx

## 📋 Pre-Deployment Checklist

- [ ] USB drive mounted at `/mnt/pixelparty` on host
- [ ] Ollama server running on host machine
- [ ] Domain name pointing to your server's IP
- [ ] Ports 80 and 443 open in firewall
- [ ] Docker and Docker Compose installed
- [ ] `.env` file created with all variables

## 🚀 Deployment Steps

### Step 1: Verify USB Mount
```bash
# Check if USB drive is mounted
ls /mnt/pixelparty/Music

# If not mounted, mount it:
sudo mkdir -p /mnt/pixelparty
sudo mount /dev/sdX1 /mnt/pixelparty  # Replace sdX1 with your USB device

# Make it permanent (add to /etc/fstab):
# UUID=your-usb-uuid /mnt/pixelparty ext4 defaults 0 2
```

### Step 2: Start Ollama on Host
```bash
# Make Ollama accessible from Docker containers
OLLAMA_HOST=0.0.0.0 ollama serve

# Or add to systemd service:
sudo systemctl edit ollama.service
# Add: Environment="OLLAMA_HOST=0.0.0.0"
```

### Step 3: Build Docker Image
```bash
# Build the application image
docker-compose build
```

### Step 4: Initial Deployment (HTTP only)
```bash
# Start without SSL first
docker-compose up -d pixelparty-app nginx

# Check logs
docker-compose logs -f pixelparty-app
```

### Step 5: Get SSL Certificate
```bash
# Run certbot to get SSL certificate
docker-compose run --rm certbot

# For renewal (add to cron):
docker-compose run --rm certbot renew
```

### Step 6: Enable HTTPS
```bash
# Restart nginx with SSL enabled
docker-compose restart nginx

# Verify HTTPS is working
curl https://your-domain.com/health
```

## 🔍 Verification Commands

### Check Container Status
```bash
docker-compose ps
```

### Test Application Health
```bash
# From host
curl http://localhost/health

# Check application logs
docker-compose logs -f pixelparty-app
```

### Verify Ollama Connectivity
```bash
# From container
docker exec pixelparty-app curl http://host.docker.internal:11434/api/tags

# Should return list of available models
```

### Check USB Music Access
```bash
# From container
docker exec pixelparty-app ls /mnt/pixelparty/Music
```

## 🛠️ Troubleshooting

### Issue: Ollama Not Accessible
```bash
# Ensure Ollama binds to all interfaces
OLLAMA_HOST=0.0.0.0 ollama serve

# Check firewall isn't blocking internal Docker network
sudo iptables -L
```

### Issue: Permission Denied on USB
```bash
# Fix permissions
sudo chmod -R 755 /mnt/pixelparty/Music

# Or run container as root (not recommended for production)
# Remove USER directive from Dockerfile
```

### Issue: SSL Certificate Failed
```bash
# Check DNS is properly configured
nslookup your-domain.com

# Manually test Let's Encrypt
docker-compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d your-domain.com
```

### Issue: Database Not Persisting
Already fixed! The `./data:/app/data` volume mount ensures persistence.

### Issue: Large Files Upload Failing
Already configured! Both Flask and nginx allow 50MB uploads.

## 🔄 Maintenance

### View Logs
```bash
# All containers
docker-compose logs -f

# Specific container
docker-compose logs -f pixelparty-app
```

### Restart Services
```bash
# Restart everything
docker-compose restart

# Restart specific service
docker-compose restart pixelparty-app
```

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d
```

### Backup Data
```bash
# Backup database and media
tar -czf backup-$(date +%Y%m%d).tar.gz data/ media/ export/
```

### SSL Certificate Renewal (Cron)
Add to crontab:
```bash
0 0 * * 0 cd /path/to/pixelparty && docker-compose run --rm certbot renew && docker-compose restart nginx
```

## 🎉 Post-Deployment

Once deployed, your PixelParty app will be accessible at:
- HTTP: `http://your-domain.com` (redirects to HTTPS)
- HTTPS: `https://your-domain.com`

### Access Points:
- **Guest Mobile**: `https://your-domain.com/mobile`
- **Big Screen**: `https://your-domain.com/`
- **Admin Panel**: `https://your-domain.com/admin`

### First-Time Setup:
1. Access admin panel
2. Configure party settings
3. Generate QR code for guests
4. Start the party!

## 📝 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `generate-secure-random-key` |
| `DATABASE_URL` | SQLite database path | `sqlite:////app/data/birthday_party.db` |
| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://host.docker.internal:11434` |
| `FLASK_CONFIG` | Flask configuration mode | `production` |
| `CERTBOT_EMAIL` | Email for SSL certificates | `your-email@example.com` |
| `DOMAIN` | Your domain name | `party.example.com` |

## 🚨 Important Security Notes

1. **Change the default SECRET_KEY** - Never use the default in production
2. **SSL is configured** - Always use HTTPS in production
3. **File uploads limited to 50MB** - Prevents abuse
4. **Read-only music mount** - USB drive is mounted read-only for safety
5. **Non-root container user** - Application runs as `appuser` for security

---

**Last Updated**: December 2024
**Deployment Ready**: YES (with minor fixes above)