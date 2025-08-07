#!/bin/bash

# DBSBM Self-Hosting Deployment Script
# This script automates the deployment of your betting bot to a self-hosted server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="DBSBM-Betting-Bot"
APP_DIR="/opt/betting-bot"
SERVICE_NAME="betting-bot"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        exit 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Please create a .env file with your configuration."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to create application directory
create_app_directory() {
    print_status "Creating application directory..."
    
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR
    
    print_success "Application directory created: $APP_DIR"
}

# Function to copy application files
copy_application_files() {
    print_status "Copying application files..."
    
    # Copy all files to application directory
    cp -r . $APP_DIR/
    
    # Set proper permissions
    sudo chown -R $USER:$USER $APP_DIR
    
    print_success "Application files copied to $APP_DIR"
}

# Function to create systemd service
create_systemd_service() {
    print_status "Creating systemd service..."
    
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=$APP_NAME
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    print_success "Systemd service created and enabled"
}

# Function to start services
start_services() {
    print_status "Starting services..."
    
    cd $APP_DIR
    
    # Pull latest images
    docker-compose pull
    
    # Start services
    docker-compose up -d
    
    print_success "Services started successfully"
}

# Function to check service health
check_service_health() {
    print_status "Checking service health..."
    
    # Wait for services to start
    sleep 30
    
    # Check if bot is responding
    if curl -f -s "http://localhost:25594/health" > /dev/null; then
        print_success "Bot is healthy and responding"
    else
        print_warning "Bot health check failed. Check logs with: docker-compose logs betting-bot"
    fi
    
    # Check container status
    if docker-compose ps | grep -q "Up"; then
        print_success "All containers are running"
    else
        print_error "Some containers failed to start. Check with: docker-compose ps"
    fi
}

# Function to setup monitoring (optional)
setup_monitoring() {
    print_status "Setting up monitoring..."
    
    # Create monitoring directory
    mkdir -p $APP_DIR/monitoring
    
    # Create Prometheus configuration
    cat > $APP_DIR/monitoring/prometheus.yml <<EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'betting-bot'
    static_configs:
      - targets: ['betting-bot:25594']
    metrics_path: '/metrics'
EOF

    # Create Grafana datasource
    mkdir -p $APP_DIR/monitoring/grafana/datasources
    cat > $APP_DIR/monitoring/grafana/datasources/prometheus.yml <<EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    print_success "Monitoring setup completed"
}

# Function to create backup script
create_backup_script() {
    print_status "Creating backup script..."
    
    cat > $APP_DIR/backup.sh <<'EOF'
#!/bin/bash

# Backup script for betting bot
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="betting_bot_backup_$DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
docker exec betting-mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD betting_bot > "$BACKUP_DIR/${BACKUP_NAME}.sql"

# Backup application data
tar -czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" \
    /opt/betting-bot/data \
    /opt/betting-bot/logs \
    /opt/betting-bot/.env

# Clean up old backups (keep last 7 days)
find "$BACKUP_DIR" -name "betting_bot_backup_*" -mtime +7 -delete

echo "Backup completed: $BACKUP_NAME"
EOF

    chmod +x $APP_DIR/backup.sh
    
    print_success "Backup script created: $APP_DIR/backup.sh"
}

# Function to create health check script
create_health_check_script() {
    print_status "Creating health check script..."
    
    cat > $APP_DIR/health_check.sh <<'EOF'
#!/bin/bash

# Health check script for betting bot
LOG_FILE="/opt/betting-bot/logs/health_check.log"
BOT_URL="http://localhost:25594/health"
DISCORD_WEBHOOK="${DISCORD_WEBHOOK_URL}"

# Check if bot is responding
if curl -f -s "$BOT_URL" > /dev/null; then
    echo "$(date): Bot is healthy" >> "$LOG_FILE"
    exit 0
else
    echo "$(date): Bot is not responding" >> "$LOG_FILE"
    
    # Send Discord notification if webhook is configured
    if [ ! -z "$DISCORD_WEBHOOK" ]; then
        curl -H "Content-Type: application/json" \
             -X POST \
             -d '{"content":"🚨 **Betting Bot Alert**: Bot is not responding! Check server immediately."}' \
             "$DISCORD_WEBHOOK"
    fi
    
    # Restart service
    cd /opt/betting-bot && docker-compose restart betting-bot
    exit 1
fi
EOF

    chmod +x $APP_DIR/health_check.sh
    
    print_success "Health check script created: $APP_DIR/health_check.sh"
}

# Function to display deployment information
show_deployment_info() {
    print_success "Deployment completed successfully!"
    echo
    echo "=== Deployment Information ==="
    echo "Application Directory: $APP_DIR"
    echo "Service Name: $SERVICE_NAME"
    echo "Web Interface: http://localhost:25594"
    echo "Docker Compose: cd $APP_DIR && docker-compose up -d"
    echo "View Logs: cd $APP_DIR && docker-compose logs -f"
    echo "Stop Services: cd $APP_DIR && docker-compose down"
    echo "Systemd Service: sudo systemctl start/stop/restart $SERVICE_NAME"
    echo
    echo "=== Optional Monitoring ==="
    echo "Prometheus: http://localhost:9090"
    echo "Grafana: http://localhost:3000 (admin/admin)"
    echo
    echo "=== Backup & Maintenance ==="
    echo "Manual Backup: $APP_DIR/backup.sh"
    echo "Health Check: $APP_DIR/health_check.sh"
    echo "Add to crontab for automated monitoring:"
    echo "*/5 * * * * $APP_DIR/health_check.sh"
    echo "0 2 * * * $APP_DIR/backup.sh"
    echo
}

# Main deployment function
main() {
    echo "=== $APP_NAME Self-Hosting Deployment ==="
    echo
    
    check_root
    check_prerequisites
    create_app_directory
    copy_application_files
    create_systemd_service
    start_services
    check_service_health
    
    # Optional: Setup monitoring
    read -p "Do you want to set up monitoring (Prometheus/Grafana)? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_monitoring
        print_status "To start monitoring: cd $APP_DIR && docker-compose --profile monitoring up -d"
    fi
    
    create_backup_script
    create_health_check_script
    show_deployment_info
}

# Run main function
main "$@" 