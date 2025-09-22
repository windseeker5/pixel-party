# PixelParty Docker Deployment Guide

Simple guide for deploying and managing your PixelParty application with Docker.

## 🚀 Initial Setup

### 1. Configure Environment
```bash
# Copy environment file
cp .env.example .env

# Edit with your details
nano .env
```

**Required settings in .env:**
```bash
DOMAIN=yourdomain.com
CERTBOT_EMAIL=your@email.com
SECRET_KEY=your-secret-key-here
```

### 2. Point Domain to Server
- Make sure your domain points to your server's IP
- Ports 80 and 443 must be open and accessible from internet

## 🏁 First Deployment

```bash
# Build and start all containers
docker-compose up -d

# Check if everything is running
docker-compose ps

# Watch logs (optional)
docker-compose logs -f
```

**What happens:**
1. PixelParty app container builds and starts
2. Nginx starts as reverse proxy
3. Certbot gets SSL certificate from Let's Encrypt
4. Your app is live at `https://yourdomain.com`

## 🔧 Making Changes & Redeploying

### Option 1: Quick Code Changes (Recommended)
```bash
# Stop containers
docker-compose down

# Rebuild only the app container
docker-compose build pixelparty-app

# Start everything again
docker-compose up -d
```

### Option 2: Full Rebuild (If needed)
```bash
# Stop and remove everything
docker-compose down

# Rebuild all images
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

## 📊 Testing & Monitoring

### Check if Everything is Working
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs pixelparty-app
docker-compose logs nginx
docker-compose logs certbot

# Test your app
curl -I https://yourdomain.com/health
```

### Test SSL Certificate
```bash
# Check certificate details
curl -I https://yourdomain.com

# Or use online tool
# https://www.ssllabs.com/ssltest/
```

## 🛠️ Common Commands

### View Logs
```bash
# All containers
docker-compose logs

# Specific container
docker-compose logs pixelparty-app
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f pixelparty-app
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific container
docker-compose restart pixelparty-app
docker-compose restart nginx
```

### Stop/Start
```bash
# Stop all containers
docker-compose stop

# Start all containers
docker-compose start

# Stop and remove containers
docker-compose down
```

## 🔄 New Version Deployment

When you have a new version of your PixelParty code:

```bash
# 1. Stop the app
docker-compose stop pixelparty-app

# 2. Rebuild the app container
docker-compose build pixelparty-app

# 3. Start the app
docker-compose start pixelparty-app

# Alternative: One command for steps 1-3
docker-compose up -d --build pixelparty-app
```

## 🚨 Troubleshooting

### SSL Certificate Issues
```bash
# Check certificate status
docker-compose exec certbot certbot certificates

# Force certificate renewal
docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot --email ${CERTBOT_EMAIL} --agree-tos --no-eff-email --force-renewal -d ${DOMAIN}

# Restart nginx after renewal
docker-compose restart nginx
```

### App Not Loading
```bash
# Check if containers are running
docker-compose ps

# Check app logs
docker-compose logs pixelparty-app

# Check nginx logs
docker-compose logs nginx

# Test internal connectivity
docker-compose exec nginx curl http://pixelparty-app:5000/health
```

### Container Build Issues
```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📁 File Structure

Your deployment directory:
```
PixelParty/
├── docker-compose.yml     # Container orchestration
├── Dockerfile             # App container definition
├── .env                   # Your configuration
├── nginx/
│   └── default.conf       # Nginx reverse proxy config
├── media/                 # Uploaded photos/videos (auto-created)
├── data/                  # Database files (auto-created)
└── export/                # Memory book exports (auto-created)
```

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| **Start** | `docker-compose up -d` |
| **Stop** | `docker-compose down` |
| **Rebuild** | `docker-compose build pixelparty-app` |
| **Update** | `docker-compose up -d --build pixelparty-app` |
| **Logs** | `docker-compose logs pixelparty-app` |
| **Status** | `docker-compose ps` |

## 🌐 Accessing Your App

- **Main App**: `https://yourdomain.com`
- **Health Check**: `https://yourdomain.com/health`
- **Admin Panel**: `https://yourdomain.com/admin` (if available)

That's it! Your PixelParty app should be running smoothly with automatic SSL certificates from Let's Encrypt.