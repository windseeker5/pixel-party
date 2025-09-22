# PixelParty Docker Deployment Guide

This guide explains how to deploy your PixelParty application using Docker with HTTPS SSL encryption.

## Overview

The Docker setup includes:
- **Flask Application Container**: Your PixelParty app running with Gunicorn
- **Nginx Container**: Reverse proxy with SSL termination
- **Certbot Container**: Automatic SSL certificate management

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- A domain name pointing to your server
- Ports 80 and 443 open on your server

### 2. Configuration

1. Copy the environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```bash
DOMAIN=your-domain.com
CERTBOT_EMAIL=your-email@example.com
SECRET_KEY=your-super-secret-key-here
SSL_PRODUCTION=false  # Set to true for production certificates
```

3. Update nginx configuration:
```bash
# Replace DOMAIN_PLACEHOLDER in nginx/default.conf
sed -i 's/DOMAIN_PLACEHOLDER/your-domain.com/g' nginx/default.conf
```

### 3. Development Deployment

For testing with staging SSL certificates:

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Production Deployment

For production with real SSL certificates:

```bash
# Set production environment
echo "SSL_PRODUCTION=true" >> .env

# Deploy with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check certificate status
docker-compose exec certbot certbot certificates
```

## Docker Compose Files

### docker-compose.yml (Base Configuration)
- Basic service definitions
- Development-friendly settings
- Staging SSL certificates

### docker-compose.prod.yml (Production Overrides)
- Production SSL certificates
- Enhanced logging
- Security optimizations
- Auto-renewal setup

## Service Details

### PixelParty App Container
- **Image**: Built from local Dockerfile
- **Port**: Internal 5000 (not exposed)
- **Volumes**:
  - `./media` - Uploaded photos/videos
  - `./data` - SQLite database
  - `./export` - Memory book exports

### Nginx Container
- **Image**: nginx:alpine
- **Ports**: 80 (HTTP) and 443 (HTTPS)
- **Features**:
  - HTTP to HTTPS redirect
  - Static file serving
  - SSL termination
  - Security headers

### Certbot Container
- **Image**: certbot/certbot
- **Purpose**: SSL certificate management
- **Features**:
  - Automatic certificate issuance
  - Auto-renewal (production setup)

## SSL Certificate Management

### Initial Certificate Setup

The first time you deploy, certificates are automatically requested from Let's Encrypt.

### Certificate Renewal

In production, certificates auto-renew. To manually renew:

```bash
docker-compose exec certbot certbot renew
docker-compose restart nginx
```

### Switching from Staging to Production

1. Update your `.env`:
```bash
SSL_PRODUCTION=true
```

2. Remove staging certificates:
```bash
docker-compose down
docker volume rm pixelparty_certbot-etc pixelparty_certbot-var
```

3. Restart with production config:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

1. **Certificate Request Failed**
   - Ensure domain points to your server
   - Check ports 80/443 are accessible
   - Verify email address is valid

2. **App Not Accessible**
   - Check if containers are running: `docker-compose ps`
   - View logs: `docker-compose logs pixelparty-app`
   - Test health endpoint: `curl http://localhost/health`

3. **SSL Issues**
   - Check certificate status: `docker-compose exec certbot certbot certificates`
   - Verify nginx config: `docker-compose exec nginx nginx -t`

### Useful Commands

```bash
# View all container logs
docker-compose logs

# Restart specific service
docker-compose restart nginx

# Check SSL certificate details
docker-compose exec certbot certbot certificates

# Access app container shell
docker-compose exec pixelparty-app bash

# View nginx access logs
docker-compose logs nginx | grep "GET\|POST"

# Test SSL configuration
curl -I https://your-domain.com
```

## File Structure

After deployment, your directory structure will be:

```
PixelParty/
├── docker-compose.yml          # Base configuration
├── docker-compose.prod.yml     # Production overrides
├── Dockerfile                  # App container definition
├── .env                       # Environment variables
├── nginx/
│   └── default.conf           # Nginx configuration
├── media/                     # Uploaded content (created)
├── data/                      # Database files (created)
└── export/                    # Memory book exports (created)
```

## Security Notes

- Change the default `SECRET_KEY` in your `.env` file
- SSL certificates are automatically managed
- All HTTP traffic redirects to HTTPS
- Security headers are configured in Nginx
- Containers run with non-root users where possible

## Accessing Your Application

Once deployed, your application will be available at:
- **Main Site**: https://your-domain.com
- **Mobile Interface**: https://your-domain.com/mobile
- **Admin Panel**: https://your-domain.com/admin
- **Health Check**: https://your-domain.com/health

Guests can access the party interface by visiting your domain or scanning the QR code generated by the application.

## Backup and Restore

### Backup
```bash
# Create backup directory
mkdir backup-$(date +%Y%m%d)

# Backup media files
cp -r media/ backup-$(date +%Y%m%d)/

# Backup database
cp data/birthday_party.db backup-$(date +%Y%m%d)/

# Backup SSL certificates
docker run --rm -v pixelparty_certbot-etc:/certs -v $(pwd):/backup alpine tar czf /backup/backup-$(date +%Y%m%d)/ssl-certs.tar.gz /certs
```

### Restore
```bash
# Restore media files
cp -r backup-20240315/media/ ./

# Restore database
cp backup-20240315/birthday_party.db data/

# Restart containers
docker-compose restart
```

This setup provides a robust, secure, and scalable deployment for your PixelParty application with automatic HTTPS encryption.