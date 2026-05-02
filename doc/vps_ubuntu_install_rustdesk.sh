#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_install_rustdesk.sh && chmod +x vps_ubuntu_install_rustdesk.sh && ./vps_ubuntu_install_rustdesk.sh

# RustDesk Server Auto-Installation Script with Let's Encrypt HTTPS
# Tested on Ubuntu 20.04 / 22.04 / 24.04
# Based on official RustDesk documentation [citation:9]
#  https://github.com/rustdesk/rustdesk 
#  https://chat.deepseek.com/share/n2j9jxe6ebjo89q199

# RustDesk Server Auto-Installation Script with Let's Encrypt HTTPS
# Supports CLI parameters for automation
#
# Usage:
#   ./install_rustdesk.sh [OPTIONS]
#
# Options:
#   -d, --domain DOMAIN           Domain name (required)
#   -e, --email EMAIL             Email for Let's Encrypt (required)
#   -s, --ssh-port PORT           SSH port (default: auto-detect from system)
#   -k, --key-file FILE           Save key to file
#   --no-ssl                      Skip SSL certificate setup (HTTP only)
#   --skip-firewall               Skip firewall configuration
#   -h, --help                    Show this help message
#
# Examples:
#   ./install_rustdesk.sh -d rustdesk.example.com -e admin@example.com
#   ./install_rustdesk.sh -d rustdesk.example.com -e admin@example.com --no-ssl

set -e

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
RustDesk Server Installation Script

Usage: $0 [OPTIONS]

Options:
  -d, --domain DOMAIN           Domain name (required)
  -e, --email EMAIL             Email for Let's Encrypt (required)
  -s, --ssh-port PORT           SSH port (default: auto-detect from system)
  -k, --key-file FILE           Save server key to file
  --no-ssl                      Skip SSL certificate setup (HTTP only)
  --skip-firewall               Skip firewall configuration
  --help, -h                    Show this help message

Examples:
  $0 -d rustdesk.example.com -e admin@example.com
  $0 -d rustdesk.example.com -e admin@example.com --no-ssl
  $0 -d rustdesk.example.com -e admin@example.com -k ./rustdesk.key

EOF
    exit 0
}

# Парсинг аргументов
DOMAIN=""
EMAIL=""
SSH_PORT=""
KEY_FILE=""
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
        -s|--ssh-port)
            SSH_PORT="$2"
            shift 2
            ;;
        -k|--key-file)
            KEY_FILE="$2"
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
print_info "  SSH Port: $SSH_PORT"
print_info "  SSL: $([ "$NO_SSL" = false ] && echo "enabled" || echo "disabled")"
echo ""

if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# === 1. ОБНОВЛЕНИЕ ===
print_step "1/7: Updating system"
apt update && apt upgrade -y

# === 2. ЗАВИСИМОСТИ ===
print_step "2/7: Installing dependencies"
apt install -y apt-transport-https ca-certificates curl wget software-properties-common nginx ufw gnupg lsb-release

if [[ "$NO_SSL" = false ]]; then
    apt install -y certbot python3-certbot-nginx
fi

# === 3. DOCKER ===
print_step "3/7: Installing Docker"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

if ! docker compose version &> /dev/null; then
    apt install -y docker-compose-plugin
fi

# === 4. ФАЙРВОЛ ===
if [[ "$SKIP_FIREWALL" = false ]]; then
    print_step "4/7: Configuring firewall"
    
    if ufw status | grep -q "inactive"; then
        echo "y" | ufw enable
    fi
    
    ufw allow "${SSH_PORT}/tcp" comment "SSH custom port"
    ufw allow 80/tcp comment "HTTP"
    ufw allow 443/tcp comment "HTTPS"
    ufw allow 21115/tcp comment "RustDesk NAT"
    ufw allow 21116/tcp comment "RustDesk TCP"
    ufw allow 21116/udp comment "RustDesk UDP"
    ufw allow 21117/tcp comment "RustDesk Relay"
    ufw allow 21118/tcp comment "RustDesk Web1"
    ufw allow 21119/tcp comment "RustDesk Web2"
    
    ufw --force enable
    print_info "Firewall configured"
else
    print_warn "Skipping firewall configuration"
fi

# === 5. RUSTDESK ===
print_step "5/7: Installing RustDesk"
mkdir -p /opt/rustdesk/data
cd /opt/rustdesk

cat > /opt/rustdesk/docker-compose.yml <<EOF
services:
  hbbs:
    image: rustdesk/rustdesk-server:latest
    container_name: rustdesk_hbbs
    command: hbbs
    restart: unless-stopped
    volumes:
      - /opt/rustdesk/data:/root
    network_mode: host

  hbbr:
    image: rustdesk/rustdesk-server:latest
    container_name: rustdesk_hbbr
    command: hbbr
    restart: unless-stopped
    volumes:
      - /opt/rustdesk/data:/root
    network_mode: host
EOF

docker compose up -d
sleep 5

if docker ps | grep -q "rustdesk"; then
    print_info "RustDesk containers started"
else
    print_error "Failed to start containers"
    docker compose logs
    exit 1
fi

# Получаем ключ
sleep 5
if [ -f /opt/rustdesk/data/id_ed25519.pub ]; then
    RUSTDESK_KEY=$(cat /opt/rustdesk/data/id_ed25519.pub)
    print_info "Server key obtained"
    
    # Сохраняем ключ в файл если указан параметр
    if [[ -n "$KEY_FILE" ]]; then
        echo "$RUSTDESK_KEY" > "$KEY_FILE"
        print_info "Key saved to: $KEY_FILE"
    fi
else
    RUSTDESK_KEY="NOT AVAILABLE - check later"
    print_warn "Key not yet generated"
fi

# === 6. NGINX && SSL ===
print_step "6/7: Configuring Nginx"

mkdir -p /var/www/rustdesk-info

cat > /var/www/rustdesk-info/index.html <<EOF
<!DOCTYPE html>
<html>
<head><title>RustDesk Server</title></head>
<body style="font-family: monospace; margin: 40px;">
<h1>✓ RustDesk Server Active</h1>
<p><strong>ID Server:</strong> $DOMAIN</p>
<p><strong>Key:</strong> <code>$RUSTDESK_KEY</code></p>
<p><strong>SSH Port:</strong> $SSH_PORT</p>
<hr>
<p><strong>Client Configuration:</strong></p>
<p>Settings → Network → ID Server: $DOMAIN → Key: above → Apply</p>
</body>
</html>
EOF

if [[ "$NO_SSL" = false ]]; then
    systemctl stop nginx
    
    if certbot certonly --standalone --non-interactive --agree-tos --email "$EMAIL" -d "$DOMAIN" 2>/dev/null; then
        print_info "SSL certificate obtained"
        
        cat > /etc/nginx/sites-available/rustdesk <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    root /var/www/rustdesk-info;
    index index.html;
}
EOF
        
        ln -sf /etc/nginx/sites-available/rustdesk /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        systemctl start nginx
        systemctl reload nginx
        print_info "Nginx configured with HTTPS"
    else
        print_warn "Could not obtain SSL certificate"
        systemctl start nginx
    fi
else
    cat > /etc/nginx/sites-available/rustdesk <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    root /var/www/rustdesk-info;
    index index.html;
}
EOF
    
    ln -sf /etc/nginx/sites-available/rustdesk /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    systemctl restart nginx
    print_info "Nginx configured with HTTP only"
fi

# === 7. HELPER СКРИПТЫ ===
print_step "7/7: Creating helper scripts"

cat > /usr/local/bin/rustdesk-status <<'EOF'
#!/bin/bash
echo "=== RustDesk Server Status ==="
echo ""
docker ps --filter "name=rustdesk" --format "table {{.Names}}\t{{.Status}}"
echo ""
echo "Key: $(cat /opt/rustdesk/data/id_ed25519.pub 2>/dev/null || echo 'Not found')"
echo ""
echo "Commands:"
echo "  docker logs -f rustdesk_hbbs"
echo "  cd /opt/rustdesk && docker compose restart"
EOF

chmod +x /usr/local/bin/rustdesk-status

cat > /usr/local/bin/rustdesk-key <<EOF
#!/bin/bash
cat /opt/rustdesk/data/id_ed25519.pub 2>/dev/null || echo "Key not found"
EOF

chmod +x /usr/local/bin/rustdesk-key

# === ФИНАЛ ===
clear
echo "========================================="
echo "  ✓ RustDesk Server Successfully Installed"
echo "========================================="
echo ""
echo "CONNECTION DETAILS:"
echo "---------------------------------------------------"
echo "ID Server (Host): $DOMAIN"
echo "Key: $RUSTDESK_KEY"
echo "SSH Port: $SSH_PORT"
echo "---------------------------------------------------"
echo ""
echo "CLIENT SETUP:"
echo "1. Download RustDesk: https://rustdesk.com/download"
echo "2. Settings → Network"
echo "3. ID Server: $DOMAIN"
echo "4. Key: paste the key above"
echo "5. Click Apply"
echo ""
echo "USEFUL COMMANDS:"
echo "  rustdesk-status - Check server status"
echo "  rustdesk-key    - Display server key"
echo "  docker logs -f rustdesk_hbbs - View logs"
echo ""
print_info "Installation complete"