# 📋 Migration Checklist - PebbleHost to Self-Hosted

## Pre-Migration Tasks

### ✅ Server Preparation
- [ ] **Server Requirements**
  - [ ] Minimum 4GB RAM, 2 CPU cores, 50GB storage
  - [ ] Ubuntu 20.04+ or CentOS 8+ installed
  - [ ] Stable internet connection
  - [ ] Static IP (optional but recommended)

- [ ] **Domain & SSL**
  - [ ] Domain name purchased/configured
  - [ ] DNS records pointing to server IP
  - [ ] SSL certificate ready (Let's Encrypt)

- [ ] **Server Setup**
  - [ ] System updated (`sudo apt update && sudo apt upgrade`)
  - [ ] Docker installed and configured
  - [ ] Docker Compose installed
  - [ ] Firewall configured (ports 80, 443, 25594)
  - [ ] SSH access secured

### ✅ Data Backup from PebbleHost
- [ ] **Database Export**
  - [ ] MySQL database exported
  - [ ] Database schema preserved
  - [ ] User data backed up
  - [ ] Configuration data exported

- [ ] **Application Files**
  - [ ] `.env` file downloaded
  - [ ] Log files backed up
  - [ ] Static assets downloaded
  - [ ] Custom configurations saved

- [ ] **Discord Bot**
  - [ ] Bot token noted
  - [ ] Guild IDs recorded
  - [ ] Custom commands documented
  - [ ] Webhook URLs saved

## Migration Tasks

### ✅ Self-Hosted Server Setup
- [ ] **Application Deployment**
  - [ ] Repository cloned to server
  - [ ] Environment variables configured
  - [ ] Docker containers built
  - [ ] Services started successfully

- [ ] **Database Migration**
  - [ ] MySQL database created
  - [ ] Data imported from backup
  - [ ] Database connections tested
  - [ ] User permissions configured

- [ ] **Web Server Configuration**
  - [ ] Nginx installed and configured
  - [ ] Reverse proxy setup
  - [ ] SSL certificate installed
  - [ ] Domain routing configured

### ✅ Service Verification
- [ ] **Bot Functionality**
  - [ ] Discord bot online
  - [ ] Commands responding correctly
  - [ ] API integrations working
  - [ ] Database operations successful

- [ ] **Web Interface**
  - [ ] Web dashboard accessible
  - [ ] Health check endpoint responding
  - [ ] Static assets loading
  - [ ] SSL certificate valid

- [ ] **Performance Testing**
  - [ ] Response times acceptable
  - [ ] Memory usage within limits
  - [ ] CPU usage normal
  - [ ] Database queries optimized

## Post-Migration Tasks

### ✅ Monitoring & Maintenance
- [ ] **Health Monitoring**
  - [ ] Health check script configured
  - [ ] Discord webhook alerts setup
  - [ ] Automated monitoring enabled
  - [ ] Log rotation configured

- [ ] **Backup Strategy**
  - [ ] Automated backup script created
  - [ ] Backup schedule configured
  - [ ] Backup retention policy set
  - [ ] Backup restoration tested

- [ ] **Security Hardening**
  - [ ] Firewall rules configured
  - [ ] SSH access secured
  - [ ] Database passwords changed
  - [ ] SSL certificates auto-renewal setup

### ✅ Documentation & Training
- [ ] **System Documentation**
  - [ ] Server configuration documented
  - [ ] Environment variables listed
  - [ ] Service management procedures written
  - [ ] Troubleshooting guide created

- [ ] **Team Training**
  - [ ] Admin procedures documented
  - [ ] Emergency contact procedures
  - [ ] Maintenance schedule created
  - [ ] Rollback procedures defined

## Testing Checklist

### ✅ Functional Testing
- [ ] **Discord Bot Commands**
  - [ ] `/bet` command working
  - [ ] `/balance` command working
  - [ ] `/leaderboard` command working
  - [ ] `/help` command working
  - [ ] All custom commands functional

- [ ] **Web Dashboard**
  - [ ] User authentication working
  - [ ] Dashboard loading correctly
  - [ ] Data displaying properly
  - [ ] Forms submitting successfully

- [ ] **API Integrations**
  - [ ] Sports data API working
  - [ ] Odds API working
  - [ ] Weather API working
  - [ ] All external services responding

### ✅ Performance Testing
- [ ] **Load Testing**
  - [ ] Multiple concurrent users
  - [ ] Database query performance
  - [ ] API response times
  - [ ] Memory usage under load

- [ ] **Stress Testing**
  - [ ] High traffic scenarios
  - [ ] Database connection limits
  - [ ] Error handling under stress
  - [ ] Recovery from failures

### ✅ Security Testing
- [ ] **Access Control**
  - [ ] Unauthorized access blocked
  - [ ] Admin functions protected
  - [ ] User permissions working
  - [ ] Session management secure

- [ ] **Data Protection**
  - [ ] Sensitive data encrypted
  - [ ] Database connections secure
  - [ ] API keys protected
  - [ ] Log files secured

## Rollback Plan

### ✅ Emergency Procedures
- [ ] **Quick Rollback**
  - [ ] PebbleHost backup ready
  - [ ] Rollback procedures documented
  - [ ] Emergency contacts listed
  - [ ] Communication plan ready

- [ ] **Data Recovery**
  - [ ] Database backup procedures
  - [ ] File backup procedures
  - [ ] Configuration backup procedures
  - [ ] Recovery testing completed

## Final Verification

### ✅ Go-Live Checklist
- [ ] **Pre-Launch**
  - [ ] All services running
  - [ ] Monitoring active
  - [ ] Backups configured
  - [ ] Team notified

- [ ] **Launch**
  - [ ] DNS updated
  - [ ] Traffic redirected
  - [ ] Services monitored
  - [ ] Performance tracked

- [ ] **Post-Launch**
  - [ ] 24-hour monitoring
  - [ ] Performance baseline established
  - [ ] Issues documented
  - [ ] Success metrics tracked

## Success Criteria

### ✅ Migration Success Metrics
- [ ] **Uptime**: 99.9%+ availability
- [ ] **Performance**: Response times < 2 seconds
- [ ] **Functionality**: All features working
- [ ] **Security**: No security vulnerabilities
- [ ] **Monitoring**: Full visibility into system health

### ✅ Business Continuity
- [ ] **Zero Downtime**: Seamless transition
- [ ] **Data Integrity**: All data preserved
- [ ] **User Experience**: No disruption to users
- [ ] **Cost Savings**: Reduced hosting costs
- [ ] **Control**: Full infrastructure control

## 🎉 Migration Complete!

Once all items are checked off, your migration from PebbleHost to self-hosted is complete!

### Next Steps
1. **Monitor performance** for the first week
2. **Document lessons learned**
3. **Plan future improvements**
4. **Set up additional monitoring**
5. **Consider scaling strategies**

---

**Migration Date**: ___________  
**Completed By**: ___________  
**Verified By**: ___________  
**Notes**: ___________ 