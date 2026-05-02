#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_install_crossdesk.sh && sudo chmod +x vps_ubuntu_install_crossdesk.sh && sudo ./vps_ubuntu_install_crossdesk.sh

# CrossDesk Server Auto-Installation Script with Let's Encrypt HTTPS
# Supports CLI parameters for automation
# 
# Usage:
#   ./install_crossdesk.sh [OPTIONS]
#
# Options:
#   -d, --domain DOMAIN           Domain name (required)
#   -e, --email EMAIL             Email for Let's Encrypt (required)
#   -i, --ip IP                   External IP address (auto-detected if not provided)
#   -s, --ssh-port PORT           SSH port (default: auto-detect from system)
#   -h, --help                    Show this help message
#
# Examples:
#   ./install_crossdesk.sh -d crossdesk.example.com -e admin@example.com -i 203.0.113.10
#   ./install_crossdesk.sh --domain crossdesk.example.com --email admin@example.com

set -e

# Цветной вывод
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "\n${BLUE}==>${NC} ${GREEN}$1${NC}"; }

show_help() {
    cat << EOF
CrossDesk Server Installation Script

Usage: $0 [OPTIONS]

Options:
  -d, --domain DOMAIN           Domain name (required)
  -e, --email EMAIL             Email for Let's Encrypt (required)
  -i, --ip IP                   External IP address (auto-detected if not provided)
  -s, --ssh-port PORT           SSH port (default: auto-detect from system)
  --no-ssl                      Skip SSL certificate setup (HTTP only)
  --skip-firewall               Skip firewall configuration
  --help, -h                    Show this help message

Examples:
  $0 -d crossdesk.example.com -e admin@example.com
  $0 -d crossdesk.example.com -e admin@example.com -i 203.0.113.10
  $0 -d crossdesk.example.com -e admin@example.com --no-ssl

EOF
    exit 0
}

# Парсинг аргументов командной строки
DOMAIN=""
EMAIL=""
EXTERNAL_IP=""
SSH_PORT=""
NO_SSL=false
SKIP_FIREWALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -i|--ip)
            EXTERNAL_IP="$2"
            shift 2
            ;;
        -s|--ssh-port)
            SSH_PORT="$2"
            shift 2
            ;;
        --no-ssl)
            NO_SSL=true
            shift
            ;;
        --skip-firewall)
            SKIP_FIREWALL=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            ;;
    esac
done

# Проверка обязательных параметров
if [[ -z "$DOMAIN" ]]; then
    print_error "Domain is required. Use -d or --domain"
    show_help
fi

if [[ -z "$EMAIL" ]]; then
    print_error "Email is required. Use -e or --email"
    show_help
fi

# Автоопределение внешнего IP если не указан
if [[ -z "$EXTERNAL_IP" ]]; then
    print_info "Auto-detecting external IP address..."
    EXTERNAL_IP=$(curl -s ifconfig.me)
    if [[ -z "$EXTERNAL_IP" ]]; then
        print_error "Could not auto-detect external IP. Please provide it with -i or --ip"
        exit 1
    fi
    print_info "Detected external IP: $EXTERNAL_IP"
fi

# Определение SSH порта
if [[ -z "$SSH_PORT" ]]; then
    if [ -f /etc/ssh/sshd_config ]; then
        SSH_PORT=$(grep -E "^Port " /etc/ssh/sshd_config | awk '{print $2}')
        if [ -z "$SSH_PORT" ]; then
            SSH_PORT=22
        fi
    else
        SSH_PORT=22
    fi
fi

print_info "Configuration:"
print_info "  Domain: $DOMAIN"
print_info "  Email: $EMAIL"
print_info "  External IP: $EXTERNAL_IP"
print_info "  SSH Port: $SSH_PORT"
print_info "  SSL: $([ "$NO_SSL" = false ] && echo "enabled" || echo "disabled")"
echo ""

# Проверка root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Получаем внутренний IP
INTERNAL_IP=$(ip route get 1 | awk '{print $NF;exit}')
print_info "Internal IP: $INTERNAL_IP"

# === 1. ОБНОВЛЕНИЕ ===
print_step "1/6: Updating system"
apt update && apt upgrade -y
apt install -y apt-transport-https ca-certificates curl software-properties-common nginx ufw

if [[ "$NO_SSL" = false ]]; then
    apt install -y certbot python3-certbot-nginx
fi

# === 2. DOCKER ===
print_step "2/6: Checking Docker"
if ! command -v docker &> /dev/null; then
    print_info "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    print_info "Docker already installed"
fi

# === 3. ДИРЕКТОРИИ ===
print_step "3/6: Creating directories"
mkdir -p /var/lib/crossdesk /var/log/crossdesk
chown -R 1000:1000 /var/lib/crossdesk /var/log/crossdesk

# === 4. ФАЙРВОЛ ===
if [[ "$SKIP_FIREWALL" = false ]]; then
    print_step "4/6: Configuring firewall"
    
    if ufw status | grep -q "inactive"; then
        echo "y" | ufw enable
    fi
    
    ufw allow "${SSH_PORT}/tcp" comment "SSH custom port"
    ufw allow 80/tcp comment "HTTP"
    ufw allow 443/tcp comment "HTTPS"
    ufw allow 9099/tcp comment "CrossDesk Signaling"
    ufw allow 3478/tcp comment "COTURN TCP"
    ufw allow 3478/udp comment "COTURN UDP"
    ufw allow 50000:60000/udp comment "COTURN Media"
    
    ufw --force enable
    print_info "Firewall configured"
else
    print_warn "Skipping firewall configuration"
fi

# === 5. CROSSDESK ===
print_step "5/6: Starting CrossDesk container"

docker stop crossdesk_server 2>/dev/null || true
docker rm crossdesk_server 2>/dev/null || true

docker run -d \
  --name crossdesk_server \
  --restart unless-stopped \
  --network host \
  -e EXTERNAL_IP="$EXTERNAL_IP" \
  -e INTERNAL_IP="$INTERNAL_IP" \
  -e CROSSDESK_SERVER_PORT=9099 \
  -e COTURN_PORT=3478 \
  -e MIN_PORT=50000 \
  -e MAX_PORT=60000 \
  -v /var/lib/crossdesk:/var/lib/crossdesk \
  -v /var/log/crossdesk:/var/log/crossdesk \
  crossdesk/crossdesk-server:latest

print_info "Container started"
sleep 10

# === 6. NGINX && SSL ===
print_step "6/6: Configuring Nginx"

mkdir -p /var/www/crossdesk

cat > /var/www/crossdesk/index.html <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CrossDesk Server</title>
    <style>
        body { font-family: monospace; margin: 40px; }
        .info { background: #f0f0f0; padding: 20px; border-radius: 8px; }
        code { background: #333; color: #fff; padding: 2px 6px; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>✓ CrossDesk Server Active</h1>
    <div class="info">
        <h2>Client Configuration</h2>
        <p><strong>Server Address:</strong> <code>$EXTERNAL_IP</code></p>
        <p><strong>Signaling Port:</strong> <code>9099</code></p>
        <p><strong>Relay Port:</strong> <code>3478</code></p>
        <hr>
        <p><strong>Important:</strong> Install the trusted root certificate:</p>
        <p><code>/var/lib/crossdesk/certs/ca.crt</code></p>
    </div>
</body>
</html>
EOF

if [[ "$NO_SSL" = false ]]; then
    systemctl stop nginx
    
    if certbot certonly --standalone --non-interactive --agree-tos --email "$EMAIL" -d "$DOMAIN" 2>/dev/null; then
        print_info "SSL certificate obtained"
        
        cat > /etc/nginx/sites-available/crossdesk <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    root /var/www/crossdesk;
    index index.html;
}
EOF
        
        ln -sf /etc/nginx/sites-available/crossdesk /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        systemctl start nginx
        systemctl reload nginx
        print_info "Nginx configured with HTTPS"
    else
        print_warn "Could not obtain SSL certificate"
        systemctl start nginx
    fi
else
    # HTTP only configuration
    cat > /etc/nginx/sites-available/crossdesk <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    root /var/www/crossdesk;
    index index.html;
}
EOF
    
    ln -sf /etc/nginx/sites-available/crossdesk /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    systemctl restart nginx
    print_info "Nginx configured with HTTP only"
fi

# === ФИНАЛ ===
clear
echo "========================================="
echo "  ✓ CrossDesk Server Successfully Installed"
echo "========================================="
echo ""
echo "CONNECTION DETAILS:"
echo "---------------------------------------------------"
echo "Server Address: $EXTERNAL_IP"
echo "Signaling Port: 9099"
echo "Relay Port: 3478"
echo "SSH Port: $SSH_PORT"
echo "Domain: $DOMAIN"
echo "---------------------------------------------------"
echo ""
echo "CLIENT SETUP:"
echo "1. Download client from: https://www.crossdesk.cn"
echo "2. Settings -> Self-Hosted Server Configuration"
echo "3. Server Address: $EXTERNAL_IP"
echo "4. Signaling Port: 9099"
echo ""
echo "Install trusted certificate:"
echo "  sudo cat /var/lib/crossdesk/certs/ca.crt"
echo ""
print_info "Installation complete"