# 🚀 Quick Start Guide - Self-Hosting Migration

## Overview
This guide will help you quickly migrate from PebbleHost to your own self-hosted server.

## Prerequisites
- Ubuntu 20.04+ server with 4GB+ RAM
- Docker and Docker Compose installed
- Domain name (optional but recommended)

## Step 1: Server Setup (5 minutes)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for Docker group to take effect
exit
# SSH back into your server
```

## Step 2: Deploy Application (10 minutes)

```bash
# Clone your repository
git clone https://github.com/yourusername/bot-server.git
cd bot-server

# Copy environment template
cp env.example .env

# Edit environment variables
nano .env
```

**Fill in your actual values in `.env`:**
- `DISCORD_TOKEN` - Your Discord bot token
- `API_KEY` - Your API-Sports key
- `MYSQL_PASSWORD` - Secure database password
- `MYSQL_ROOT_PASSWORD` - Secure MySQL root password

## Step 3: Start Services (5 minutes)

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## Step 4: Verify Deployment (2 minutes)

```bash
# Check if services are running
docker-compose ps

# Test web interface
curl http://localhost:25594/health

# Check logs
docker-compose logs -f betting-bot
```

## Step 5: Configure Domain (Optional - 10 minutes)

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/betting-bot
```

**Add this configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:25594;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/betting-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Install SSL (optional)
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## ✅ Migration Complete!

Your betting bot is now running on your own server!

### Quick Commands

```bash
# View logs
docker-compose logs -f

# Restart bot
docker-compose restart betting-bot

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Backup database
./backup.sh

# Health check
./health_check.sh
```

### Access Points
- **Web Interface**: http://yourdomain.com or http://localhost:25594
- **Discord Bot**: Should be online and responding to commands
- **Logs**: `docker-compose logs -f betting-bot`

### Monitoring (Optional)
```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana: http://localhost:3000 (admin/admin)
# Access Prometheus: http://localhost:9090
```

## 🔧 Troubleshooting

### Bot not starting?
```bash
# Check environment variables
cat .env

# Check logs
docker-compose logs betting-bot

# Restart services
docker-compose down && docker-compose up -d
```

### Database connection issues?
```bash
# Check MySQL container
docker-compose logs mysql

# Test database connection
docker exec -it betting-mysql mysql -u betting_bot -p
```

### Web interface not accessible?
```bash
# Check if port is open
netstat -tlnp | grep 25594

# Test local access
curl http://localhost:25594/health
```

## 📊 Next Steps

1. **Set up automated backups**:
   ```bash
   crontab -e
   # Add: 0 2 * * * /opt/betting-bot/backup.sh
   ```

2. **Set up health monitoring**:
   ```bash
   crontab -e
   # Add: */5 * * * * /opt/betting-bot/health_check.sh
   ```

3. **Configure Discord webhook alerts**:
   - Add your Discord webhook URL to `.env`
   - Test with: `./health_check.sh`

4. **Monitor performance**:
   - Check resource usage: `docker stats`
   - Monitor logs: `docker-compose logs -f`

## 🎉 Congratulations!

You've successfully migrated from PebbleHost to your own self-hosted server with:
- ✅ Complete control over your infrastructure
- ✅ Better performance and reliability
- ✅ Custom monitoring and backup solutions
- ✅ Professional deployment setup

Your betting bot is now running independently! 🚀 