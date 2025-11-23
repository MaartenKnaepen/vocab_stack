# 🎉 Deploying a Reflex App: From Local Docker to Self-Hosted HTTPS

A complete guide to deploying your Reflex (or any Docker-based) application from a local development environment to a publicly accessible HTTPS website with a clean URL.

---

## 📋 Prerequisites

- A server/computer running Linux (Ubuntu/Debian) that's on 24/7
- Docker and Docker Compose installed
- Your application working locally in Docker
- Router admin access (for port forwarding)
- Basic command line knowledge

---

## 🎯 What We'll Achieve

**Before:** `http://localhost:3000` (only accessible on your local network)

**After:** `https://yourapp.duckdns.org` (accessible from anywhere, with valid SSL)

- ✅ Clean URL (no port numbers)
- ✅ Free HTTPS certificate
- ✅ Free permanent domain
- ✅ Working WebSockets
- ✅ Auto-restart on reboot
- ✅ Auto-renewing SSL certificate

---

## 🚀 Step-by-Step Guide

### Step 1: Get a Free Domain Name

1. Go to [DuckDNS.org](https://www.duckdns.org/)
2. Sign in with GitHub, Google, or another provider
3. Create a subdomain (e.g., `yourapp` → `yourapp.duckdns.org`)
4. Copy your **token** (you'll need this)

---

### Step 2: Set Up DuckDNS Auto-Update

Your home IP address changes periodically. This script keeps DuckDNS updated with your current IP.

```bash
# Create directory for DuckDNS
mkdir -p ~/duckdns
cd ~/duckdns

# Create update script
nano duck.sh
```

Paste this (replace `YOUR-DOMAIN` and `YOUR-TOKEN`):

```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=YOUR-DOMAIN&token=YOUR-TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

Make it executable and test:

```bash
chmod +x duck.sh
./duck.sh
cat duck.log  # Should output: OK
```

Set up automatic updates every 5 minutes:

```bash
crontab -e
```

Add this line:

```
*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

---

### Step 3: Verify Your Local App Works

Make sure your Docker containers are running:

```bash
cd ~/path/to/your/app
docker-compose up -d

# Check containers are running
docker ps

# Test locally
curl http://localhost:3000  # Should return HTML
```

**Important:** Note which ports your app uses:
- Frontend port (usually 3000)
- Backend/API port (if separate, e.g., 8000)

---

### Step 4: Install and Configure Nginx

Nginx will act as a reverse proxy, handling SSL and routing traffic to your app.

```bash
# Install nginx
sudo apt update
sudo apt install nginx -y

# Create config for your app
sudo nano /etc/nginx/sites-available/yourapp
```

Paste this config (adjust domain and ports as needed):

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

# HTTP - Redirect to HTTPS
server {
    listen 80;
    server_name yourapp.duckdns.org;
    return 301 https://$server_name$request_uri;
}

# HTTPS
server {
    listen 443 ssl;
    server_name yourapp.duckdns.org;
    
    # SSL certificates (will be added by Certbot)
    ssl_certificate /etc/letsencrypt/live/yourapp.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourapp.duckdns.org/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # WebSocket endpoint (adjust if your app uses different path)
    location /_event/ {
        proxy_pass http://localhost:8000;  # Backend port
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_connect_timeout 86400;
    }

    # Main application
    location / {
        proxy_pass http://localhost:3000;  # Frontend port
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Note:** For Reflex apps, WebSocket endpoints (`/_event/`) typically run on the backend port (8000), while the frontend runs on port 3000. Adjust if your setup differs.

Enable the site:

```bash
# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Enable your site
sudo ln -s /etc/nginx/sites-available/yourapp /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

### Step 5: Configure Port Forwarding on Your Router

You need to forward ports 80 and 443 from the internet to your server.

1. Find your server's local IP:
   ```bash
   hostname -I | awk '{print $1}'
   # Example output: 192.168.0.3
   ```

2. Access your router admin page (common addresses):
   - `http://192.168.0.1`
   - `http://192.168.1.1`
   - `http://192.168.1.254`

3. Find "Port Forwarding" or "Virtual Server" section

4. Add **two rules**:

   **Rule 1 - HTTP (for SSL verification):**
   - Description: `YourApp-HTTP`
   - LAN IP: `192.168.0.X` (your server's IP)
   - Protocol: `TCP`
   - Public Port: `80`
   - Local Port: `80`

   **Rule 2 - HTTPS:**
   - Description: `YourApp-HTTPS`
   - LAN IP: `192.168.0.X` (your server's IP)
   - Protocol: `TCP`
   - Public Port: `443`
   - Local Port: `443`

5. Save and apply

6. Test external access:
   ```bash
   curl http://yourapp.duckdns.org
   # Should return HTML (but will show SSL error in browser - we'll fix this next)
   ```

---

### Step 6: Get Free SSL Certificate from Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate (Certbot will auto-configure nginx)
sudo certbot --nginx -d yourapp.duckdns.org
```

Follow the prompts:
- Enter your email
- Agree to Terms of Service (Y)
- Share email with EFF (optional - N is fine)

Certbot will automatically:
- Obtain a free SSL certificate
- Configure nginx to use it
- Set up auto-renewal (certificates renew every 90 days)

Test the renewal process:
```bash
sudo certbot renew --dry-run
```

---

### Step 7: Update Your Application Configuration

Your app needs to know its public URL for generating correct links and WebSocket connections.

**For Reflex apps:**

```bash
cd ~/path/to/your/app
nano .env
```

Update or add these variables:

```env
API_URL=https://yourapp.duckdns.org
DEPLOY_URL=https://yourapp.duckdns.org
```

**For other apps:** Check your app's documentation for URL configuration variables.

Restart your containers:

```bash
docker-compose down
docker-compose up -d
```

---

### Step 8: Final Testing

Wait 1-2 minutes for your app to fully start, then test:

1. **Access your app:**
   ```
   https://yourapp.duckdns.org
   ```

2. **Verify SSL certificate:**
   - Click the padlock icon in your browser
   - Should show "Connection is secure"

3. **Test from external network:**
   - Use your phone with mobile data (not WiFi)
   - Access the same URL
   - Should work from anywhere!

4. **Check WebSockets (if applicable):**
   - Open browser console (F12)
   - Look for WebSocket connection errors
   - Should see successful connections

---

## 🔧 Troubleshooting

### WebSocket Errors

If you see "WebSocket connection failed" errors:

1. **Check nginx config** - Make sure the `map $http_upgrade` block is at the top
2. **Verify backend routing** - WebSocket endpoints need correct port routing
3. **Check browser console** - Note the exact WebSocket URL being attempted
4. **View nginx logs:**
   ```bash
   sudo tail -f /var/log/nginx/access.log
   # Look for WebSocket upgrade requests (should show status 101 for success)
   ```

### Port 80/443 Blocked by ISP

Some ISPs block residential ports 80/443. Solutions:

1. **Contact your ISP** - Ask them to unblock the ports
2. **Use non-standard ports** - Use 8080 and 8443, update port forwarding accordingly
3. **Use Cloudflare Tunnel** - More complex but bypasses port restrictions

### DuckDNS Not Resolving

```bash
# Check if DuckDNS points to your public IP
nslookup yourapp.duckdns.org

# Check your actual public IP
curl ifconfig.me

# If they don't match, update DuckDNS
cd ~/duckdns
./duck.sh
cat duck.log  # Should output: OK
```

### SSL Certificate Fails to Generate

```bash
# Check certbot logs
sudo cat /var/log/letsencrypt/letsencrypt.log | tail -50

# Common issues:
# - Port 80 not accessible from internet (check port forwarding)
# - Nginx not running (sudo systemctl status nginx)
# - Domain not resolving (check DuckDNS)
```

### Containers Don't Auto-Restart

Ensure your `docker-compose.yml` has:

```yaml
services:
  app:
    restart: unless-stopped
    # ... rest of config
```

---

## 🛡️ Security Best Practices

### 1. **Only Expose Necessary Ports**

⚠️ **DO NOT** forward these ports unless you specifically want them public:
- 5432 (PostgreSQL)
- 3306 (MySQL)
- 6379 (Redis)
- Other internal services

✅ **Only forward:**
- 80 (HTTP - for SSL verification)
- 443 (HTTPS - your app)

### 2. **Implement Application-Level Authentication**

Your app should require login. Don't rely on "security by obscurity."

### 3. **Keep System Updated**

```bash
# Update regularly
sudo apt update && sudo apt upgrade -y

# Check for security updates
sudo unattended-upgrades
```

### 4. **Monitor SSL Certificate Renewal**

Certbot auto-renews, but check occasionally:

```bash
sudo certbot certificates
# Shows expiration dates
```

### 5. **Use Firewall (Optional but Recommended)**

```bash
# Install ufw
sudo apt install ufw

# Allow SSH (important - don't lock yourself out!)
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

---

## 📊 Monitoring and Maintenance

### Check Nginx Status

```bash
sudo systemctl status nginx
```

### View Nginx Logs

```bash
# Access log (successful requests)
sudo tail -f /var/log/nginx/access.log

# Error log (problems)
sudo tail -f /var/log/nginx/error.log
```

### Check Docker Containers

```bash
# List running containers
docker ps

# View container logs
docker logs -f container_name
```

### Restart Services

```bash
# Restart nginx
sudo systemctl restart nginx

# Restart your app
cd ~/path/to/your/app
docker-compose restart
```

---

## 🎓 Understanding the Architecture

```
Internet
    ↓
Your Home Router (Port Forwarding: 80→80, 443→443)
    ↓
Your Server (192.168.0.X)
    ↓
Nginx (Reverse Proxy on ports 80/443)
    ↓
    ├─→ Port 3000 (Frontend) - Regular HTTP requests
    └─→ Port 8000 (Backend) - WebSocket connections
    ↓
Docker Containers (Your App + Database)
```

**Why this setup?**

1. **DuckDNS** - Gives you a free domain name that updates with your changing home IP
2. **Nginx** - Handles SSL/HTTPS, routes traffic, manages WebSockets
3. **Let's Encrypt** - Provides free, auto-renewing SSL certificates
4. **Port Forwarding** - Makes your server accessible from the internet
5. **Docker** - Keeps your app isolated and easy to manage

---

## 🚀 Optional Enhancements

### Add a Custom Domain

If you buy a domain (e.g., `myapp.com` from Namecheap for ~$12/year):

1. Add an A record pointing to your IP
2. Update DuckDNS to track IP changes
3. Update nginx config with new domain
4. Get new SSL certificate: `sudo certbot --nginx -d myapp.com`

### Set Up Automatic Backups

```bash
# Backup script for database
nano ~/backup.sh
```

```bash
#!/bin/bash
docker exec postgres_container pg_dump -U username dbname > ~/backups/backup_$(date +%Y%m%d).sql
```

```bash
chmod +x ~/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * ~/backup.sh
```

### Add Monitoring

Use tools like:
- **Uptime Robot** (free) - Monitors if your site is up
- **Netdata** - System resource monitoring
- **Prometheus + Grafana** - Advanced metrics

---

## ✅ Final Checklist

- [ ] DuckDNS domain created and updating
- [ ] Docker containers running and accessible locally
- [ ] Nginx installed and configured
- [ ] Port forwarding set up on router (80 and 443)
- [ ] SSL certificate obtained from Let's Encrypt
- [ ] App environment variables updated with public URL
- [ ] Site accessible via HTTPS with clean URL
- [ ] WebSockets working (if applicable)
- [ ] Tested from external network (mobile data)
- [ ] SSL auto-renewal tested
- [ ] Docker containers set to auto-restart

---

## 🎉 Congratulations!

You now have a fully self-hosted application with:
- **Professional URL** (no ports, no IP addresses)
- **Secure HTTPS** with valid certificate
- **Free hosting** (just electricity costs)
- **Full control** over your data and infrastructure

Your app is accessible 24/7 from anywhere in the world! 🌍

---

## 📚 Additional Resources

- [DuckDNS Documentation](https://www.duckdns.org/spec.jsp)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Reflex Deployment Guide](https://reflex.dev/docs/hosting/self-hosting/)

---

*This guide was battle-tested on Ubuntu 22.04 with a Reflex application, but the principles apply to any Docker-based web application.*
