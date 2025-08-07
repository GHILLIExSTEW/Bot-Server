# Self-Hosting Migration Guide

## 🚀 Transitioning from PebbleHost to Self-Hosted Server

This guide will help you migrate your DBSBM betting bot from PebbleHost to your own self-hosted server, giving you complete control over your infrastructure.

## 📋 Pre-Migration Checklist

### 1. Server Requirements
- **Minimum Specs**: 4GB RAM, 2 CPU cores, 50GB storage
- **Recommended**: 8GB RAM, 4 CPU cores, 100GB SSD
- **OS**: Ubuntu 20.04+ or CentOS 8+ (Ubuntu recommended)
- **Network**: Stable internet connection with static IP (optional but recommended)

### 2. Domain & SSL (Optional but Recommended)
- Domain name for your web interface
- SSL certificate (Let's Encrypt is free)
- DNS configuration

### 3. Required Services
- **MySQL 8.0+** or **PostgreSQL 13+**
- **Redis 6.0+** for caching
- **Nginx** for reverse proxy (optional but recommended)

## 🔧 Server Setup

### Step 1: Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install Python 3.11+
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Node.js (for asset optimization)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install MySQL
sudo apt install -y mysql-server mysql-client

# Install Redis
sudo apt install -y redis-server

# Install Nginx
sudo apt install -y nginx

# Install Docker (optional but recommended)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Step 2: Create Application User

```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash betting-bot
sudo usermod -aG docker betting-bot

# Set up application directory
sudo mkdir -p /opt/betting-bot
sudo chown betting-bot:betting-bot /opt/betting-bot
```

### Step 3: Database Setup

```bash
# Secure MySQL installation
sudo mysql_secure_installation

# Create database and user
sudo mysql -u root -p
```

```sql
-- Create database
CREATE DATABASE betting_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'betting_bot'@'localhost' IDENTIFIED BY 'your_secure_password_here';
GRANT ALL PRIVILEGES ON betting_bot.* TO 'betting_bot'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 4: Application Deployment

```bash
# Switch to application user
sudo su - betting-bot

# Clone your repository
cd /opt/betting-bot
git clone https://github.com/yourusername/bot-server.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip wheel setuptools
pip install -r DBSBM/requirements.txt
pip install -r DBSBMWEB/requirements.txt

# Create necessary directories
mkdir -p logs data/cache static/cache/optimized data/metrics
```

## 🔐 Environment Configuration

### Create Production Environment File

```bash
# Create .env file
nano /opt/betting-bot/.env
```

```env
# === APPLICATION SETTINGS ===
APP_NAME=DBSBM-Betting-Bot
APP_VERSION=2.0.0
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# === SECURITY ===
SECRET_KEY=your_cryptographically_secure_key_256_bits_long_here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# === DISCORD BOT ===
DISCORD_TOKEN=your_discord_bot_token_here
TEST_GUILD_ID=your_discord_guild_id_here

# === DATABASE ===
MYSQL_HOST=localhost
MYSQL_USER=betting_bot
MYSQL_PASSWORD=your_secure_password_here
MYSQL_DB=betting_bot
MYSQL_PORT=3306
MYSQL_POOL_MIN_SIZE=1
MYSQL_POOL_MAX_SIZE=10

# === REDIS CACHE ===
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600
REDIS_SESSION_TTL=86400

# === API KEYS ===
API_KEY=your_api_sports_key_here
API_SPORTS_KEY=your_api_sports_key_here
ODDS_API_KEY=your_odds_api_key_here

# === WEB SERVER ===
WEBAPP_PORT=25594
FLASK_ENV=production
FLASK_DEBUG=0
HOST=127.0.0.1
PORT=8000

# === PERFORMANCE ===
MAX_WORKERS=4
CACHE_TTL=3600
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RETRY_DELAY=5

# === MONITORING ===
HEALTH_CHECK_INTERVAL=30
LOG_FILE=/opt/betting-bot/logs/bot.log
```

## 🚀 Service Management

### Option 1: Systemd Service (Recommended)

```bash
# Create systemd service file
sudo nano /etc/systemd/system/betting-bot.service
```

```ini
[Unit]
Description=DBSBM Betting Bot
After=network.target mysql.service redis.service
Wants=mysql.service redis.service

[Service]
Type=simple
User=betting-bot
Group=betting-bot
WorkingDirectory=/opt/betting-bot
Environment=PATH=/opt/betting-bot/venv/bin
Environment=PYTHONPATH=/opt/betting-bot
ExecStart=/opt/betting-bot/venv/bin/python DBSBM/bot/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/betting-bot/logs /opt/betting-bot/data

[Install]
WantedBy=multi-user.target
```

### Option 2: Docker Compose (Alternative)

```bash
# Create docker-compose.yml
nano /opt/betting-bot/docker-compose.yml
```

```yaml
version: "3.8"

services:
  betting-bot:
    build: .
    container_name: betting-bot
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - API_KEY=${API_KEY}
      - MYSQL_HOST=mysql
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DB=${MYSQL_DB}
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped
    volumes:
      - ./logs:/opt/betting-bot/logs
      - ./data:/opt/betting-bot/data
    networks:
      - betting-network
    ports:
      - "25594:25594"

  mysql:
    image: mysql:8.0
    container_name: betting-mysql
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DB}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - betting-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  redis:
    image: redis:6-alpine
    container_name: betting-redis
    networks:
      - betting-network
    restart: unless-stopped

networks:
  betting-network:
    driver: bridge

volumes:
  mysql_data:
```

## 🌐 Web Server Configuration

### Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/betting-bot
```

```nginx
upstream betting_bot {
    server 127.0.0.1:25594;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Static assets
    location /static/ {
        alias /opt/betting-bot/DBSBM/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://betting_bot;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Health check
    location /health {
        proxy_pass http://betting_bot;
        access_log off;
    }

    # Main application
    location / {
        proxy_pass http://betting_bot;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/betting-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Set up auto-renewal
sudo crontab -e
# Add this line:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🚀 Start Services

### Systemd Method

```bash
# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable betting-bot
sudo systemctl start betting-bot

# Check status
sudo systemctl status betting-bot

# View logs
sudo journalctl -u betting-bot -f
```

### Docker Method

```bash
# Start services
cd /opt/betting-bot
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f betting-bot
```

## 📊 Monitoring & Maintenance

### Health Check Script

```bash
# Create health check script
nano /opt/betting-bot/health_check.sh
```

```bash
#!/bin/bash

# Health check script for betting bot
LOG_FILE="/opt/betting-bot/logs/health_check.log"
BOT_URL="http://localhost:25594/health"
DISCORD_WEBHOOK="your_discord_webhook_url_here"

# Check if bot is responding
if curl -f -s "$BOT_URL" > /dev/null; then
    echo "$(date): Bot is healthy" >> "$LOG_FILE"
    exit 0
else
    echo "$(date): Bot is not responding" >> "$LOG_FILE"
    
    # Send Discord notification
    curl -H "Content-Type: application/json" \
         -X POST \
         -d '{"content":"🚨 **Betting Bot Alert**: Bot is not responding! Check server immediately."}' \
         "$DISCORD_WEBHOOK"
    
    # Restart service
    sudo systemctl restart betting-bot
    exit 1
fi
```

```bash
# Make executable and add to crontab
chmod +x /opt/betting-bot/health_check.sh
crontab -e
# Add: */5 * * * * /opt/betting-bot/health_check.sh
```

### Backup Script

```bash
# Create backup script
nano /opt/betting-bot/backup.sh
```

```bash
#!/bin/bash

# Backup script for betting bot
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="betting_bot_backup_$DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
mysqldump -u betting_bot -p betting_bot > "$BACKUP_DIR/${BACKUP_NAME}.sql"

# Backup application data
tar -czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" \
    /opt/betting-bot/data \
    /opt/betting-bot/logs \
    /opt/betting-bot/.env

# Clean up old backups (keep last 7 days)
find "$BACKUP_DIR" -name "betting_bot_backup_*" -mtime +7 -delete

echo "Backup completed: $BACKUP_NAME"
```

```bash
# Make executable and add to crontab
chmod +x /opt/betting-bot/backup.sh
crontab -e
# Add: 0 2 * * * /opt/betting-bot/backup.sh
```

## 🔧 Migration Steps

### 1. Export Data from PebbleHost

```bash
# Export database (if you have access)
mysqldump -h your_pebblehost_db_host -u username -p database_name > backup.sql

# Download application files
# Use your hosting provider's file manager or FTP to download:
# - .env file
# - logs directory
# - data directory
# - static files
```

### 2. Import to Self-Hosted Server

```bash
# Import database
mysql -u betting_bot -p betting_bot < backup.sql

# Copy application files
scp -r /path/to/downloaded/files/* user@your-server:/opt/betting-bot/
```

### 3. Update Configuration

```bash
# Update environment variables for new server
nano /opt/betting-bot/.env

# Update Discord bot webhook URLs if needed
# Update any hardcoded URLs in your application
```

### 4. Test Migration

```bash
# Test the application
sudo systemctl restart betting-bot
sudo systemctl status betting-bot

# Check web interface
curl http://localhost:25594/health

# Test Discord bot commands
# Join your Discord server and test bot functionality
```

## 🛠️ Troubleshooting

### Common Issues

1. **Bot won't start**
   ```bash
   # Check logs
   sudo journalctl -u betting-bot -f
   
   # Check environment variables
   sudo -u betting-bot cat /opt/betting-bot/.env
   ```

2. **Database connection issues**
   ```bash
   # Test database connection
   mysql -u betting_bot -p betting_bot -e "SELECT 1;"
   
   # Check MySQL status
   sudo systemctl status mysql
   ```

3. **Web interface not accessible**
   ```bash
   # Check Nginx status
   sudo systemctl status nginx
   
   # Check firewall
   sudo ufw status
   
   # Test local access
   curl http://localhost:25594
   ```

4. **SSL certificate issues**
   ```bash
   # Check certificate status
   sudo certbot certificates
   
   # Renew manually if needed
   sudo certbot renew --dry-run
   ```

## 📈 Performance Optimization

### MySQL Optimization

```sql
-- Add to /etc/mysql/mysql.conf.d/mysqld.cnf
[mysqld]
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT
query_cache_size = 64M
query_cache_type = 1
max_connections = 200
```

### Redis Optimization

```bash
# Edit /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Application Optimization

```bash
# Enable gzip compression in Nginx
sudo nano /etc/nginx/nginx.conf
# Add to http block:
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
```

## 🎉 Migration Complete!

Your betting bot is now running on your own server with:
- ✅ Complete control over infrastructure
- ✅ Better performance and reliability
- ✅ Custom monitoring and backup solutions
- ✅ SSL security
- ✅ Professional domain setup

### Next Steps

1. **Monitor performance** for the first few days
2. **Set up additional monitoring** (Prometheus + Grafana)
3. **Configure automated backups** to external storage
4. **Set up alerting** for critical issues
5. **Document your setup** for future maintenance

### Support

If you encounter issues during migration:
1. Check the logs: `sudo journalctl -u betting-bot -f`
2. Verify environment variables are set correctly
3. Test database connectivity
4. Ensure all required services are running
5. Check firewall and network configuration

Happy self-hosting! 🚀 