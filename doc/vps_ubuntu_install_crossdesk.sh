#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_install_crossdesk.sh && chmod +x vps_ubuntu_install_crossdesk.sh && ./vps_ubuntu_install_crossdesk.sh

# CrossDesk Server Auto-Installation Script with Let's Encrypt HTTPS
# Tested on Ubuntu 22.04 / 24.04
# Author: Based on CrossDesk documentation

set -e  # Exit on any error

# Цветной вывод для удобства чтения
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка запуска от root
if [[ $EUID -ne 0 ]]; then
   print_error "Этот скрипт должен запускаться от root (sudo)"
   exit 1
fi

# === ВВОД ДАННЫХ ===
clear
echo "========================================="
echo "   CrossDesk Server Installation Script"
echo "========================================="
echo ""

read -p "Введите ваш домен (например, crossdesk.example.com): " DOMAIN
read -p "Введите ваш email для Let's Encrypt уведомлений: " EMAIL
read -p "Введите внешний IP-адрес сервера: " EXTERNAL_IP

# Получаем внутренний IP автоматически
INTERNAL_IP=$(ip route get 1 | awk '{print $NF;exit}')
print_info "Внутренний IP определен автоматически: $INTERNAL_IP"

# === 1. ОБНОВЛЕНИЕ СИСТЕМЫ И УСТАНОВКА ЗАВИСИМОСТЕЙ ===
print_info "Обновление системы и установка зависимостей..."
apt update && apt upgrade -y
apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw

# === 2. УСТАНОВКА DOCKER ===
if ! command -v docker &> /dev/null; then
    print_info "Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    print_info "Docker установлен"
else
    print_info "Docker уже установлен"
fi

# === 3. СОЗДАНИЕ ДИРЕКТОРИЙ И НАСТРОЙКА ПРАВ ===
print_info "Создание директорий для CrossDesk..."
mkdir -p /var/lib/crossdesk /var/log/crossdesk
# Устанавливаем правильные права (UID 1000 - стандартный пользователь в контейнере)
chown -R 1000:1000 /var/lib/crossdesk /var/log/crossdesk

# === 4. ОТКРЫТИЕ ПОРТОВ В ФАЙРВОЛЕ ===
print_info "Настройка файрвола..."
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP (Let\'s Encrypt)'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 9099/tcp comment 'CrossDesk Signaling'
ufw allow 3478/tcp comment 'COTURN TCP'
ufw allow 3478/udp comment 'COTURN UDP'
ufw allow 50000:60000/udp comment 'COTURN Media Ports'
ufw --force enable
print_info "Порты настроены"

# === 5. ЗАПУСК CROSSDESK SERVER ===
print_info "Запуск CrossDesk Server Docker контейнера..."
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
  crossdesk/crossdesk-server:v1.1.14

print_info "Контейнер CrossDesk Server запущен"

# Ожидание генерации сертификатов
print_info "Ожидание генерации SSL сертификатов (30 секунд)..."
sleep 30

# === 6. НАСТРОЙКА NGINX КАК ПРОКСИ ===
print_info "Настройка Nginx для домена $DOMAIN..."

# Копируем сертификаты CrossDesk в директорию Nginx (если они есть)
if [ -f /var/lib/crossdesk/certs/server.crt ]; then
    mkdir -p /etc/nginx/ssl/$DOMAIN
    cp /var/lib/crossdesk/certs/server.crt /etc/nginx/ssl/$DOMAIN/fullchain.pem
    cp /var/lib/crossdesk/certs/server.key /etc/nginx/ssl/$DOMAIN/privkey.pem
    print_info "Сертификаты CrossDesk скопированы"
fi

# Создаем конфигурацию Nginx для статической страницы-прокси
cat > /etc/nginx/sites-available/crossdesk <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL сертификаты будут добавлены Let's Encrypt
    # Пока используем временные самоподписанные
    ssl_certificate /etc/nginx/ssl/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/$DOMAIN/privkey.pem;

    location / {
        root /var/www/crossdesk;
        index index.html;
        try_files \$uri \$uri/ =404;
    }

    # Прокси для API (опционально, если нужно)
    location /api/ {
        proxy_pass http://127.0.0.1:9099;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Создаем директорию для веб-страницы
mkdir -p /var/www/crossdesk

# Создаем удобную HTML-страницу с информацией о подключении
cat > /var/www/crossdesk/index.html <<EOF
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CrossDesk Server - готов к работе</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; line-height: 1.6; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        .card { background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #3498db; }
        .code { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; font-family: monospace; overflow-x: auto; }
        .status { background: #27ae60; color: white; padding: 5px 15px; border-radius: 20px; display: inline-block; }
        .warning { background: #e74c3c; color: white; padding: 5px 15px; border-radius: 20px; display: inline-block; }
    </style>
</head>
<body>
    <h1>🚀 CrossDesk Server</h1>
    <p><span class="status">✅ Сервер работает</span></p>

    <div class="card">
        <h2>📡 Данные для подключения клиента</h2>
        <p><strong>Адрес сервера:</strong> <code>$EXTERNAL_IP</code></p>
        <p><strong>Порт сигналинга:</strong> <code>9099</code></p>
        <p><strong>Порт TURN сервера:</strong> <code>3478</code></p>
    </div>

    <div class="card">
        <h2>🌐 Web-клиент</h2>
        <p>Используйте официальный Web-клиент для подключения к удаленным устройствам:</p>
        <p>🔗 <a href="https://web.crossdesk.cn" target="_blank">https://web.crossdesk.cn</a></p>
        <p><em>В Web-клиенте укажите ваш сервер в настройках!</em></p>
    </div>

    <div class="card">
        <h2>📱 Настройка клиента CrossDesk</h2>
        <ol>
            <li>Скачайте клиент с <a href="https://www.crossdesk.cn" target="_blank">официального сайта</a></li>
            <li>В настройках (шестеренка) нажмите "Self-Hosted Server Configuration"</li>
            <li>Включите опцию "Self-hosted server configuration"</li>
            <li><strong>Server Address:</strong> <code>$EXTERNAL_IP</code></li>
            <li><strong>Signaling Service Port:</strong> <code>9099</code></li>
            <li><strong>Relay Service Port:</strong> <code>3478</code></li>
        </ol>
        <div class="warning" style="background:#e67e22;">⚠️ Важно!</div>
        <p>Вам нужно скачать и установить корневой сертификат сервера как доверенный:</p>
        <p><code>/var/lib/crossdesk/certs/ca.crt</code></p>
        <p>Скачайте его и установите в вашей ОС как доверенный корневой сертификат.</p>
    </div>

    <div class="card">
        <h2>📊 Статус сервера</h2>
        <p><strong>Контейнер Docker:</strong> $(docker ps --filter "name=crossdesk_server" --format "table {{.Status}}" | tail -1)</p>
        <p><strong>Время работы с начала установки:</strong> $(uptime -p)</p>
    </div>

    <hr>
    <p style="font-size: 12px; color: #7f8c8d;">CrossDesk Server установлен $(date)</p>
</body>
</html>
EOF

# Активируем конфигурацию Nginx
ln -sf /etc/nginx/sites-available/crossdesk /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default 2>/dev/null

# Проверяем конфигурацию и перезапускаем Nginx
nginx -t && systemctl restart nginx
print_info "Nginx настроен"

# === 7. ПОЛУЧЕНИЕ SSL СЕРТИФИКАТА LET'S ENCRYPT ===
print_info "Получение SSL сертификата от Let's Encrypt для $DOMAIN..."

# Останавливаем Nginx на время получения сертификата (если используем standalone)
systemctl stop nginx

certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"

if [ $? -eq 0 ]; then
    print_info "SSL сертификат успешно получен!"

    # Обновляем конфигурацию Nginx для использования Let's Encrypt сертификатов
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

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        root /var/www/crossdesk;
        index index.html;
        try_files \$uri \$uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:9099;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

    systemctl start nginx
    nginx -t && systemctl reload nginx

    # Добавляем автоматическое обновление сертификатов
    (crontab -l 2>/dev/null; echo "0 3 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
    print_info "Автоматическое обновление сертификатов настроено"
else
    print_warn "Не удалось получить Let's Encrypt сертификат. Проверьте, что домен $DOMAIN указывает на IP $EXTERNAL_IP"
    print_warn "Nginx будет использовать самоподписанный сертификат"
    systemctl start nginx
fi

# === 8. ФИНАЛЬНАЯ ПРОВЕРКА ===
print_info "Проверка статуса сервисов..."

echo ""
echo "========================================="
echo "  CrossDesk Server установлен!"
echo "========================================="
echo ""

echo "Статус Docker контейнера:"
docker ps --filter "name=crossdesk_server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "Статус Nginx:"
systemctl status nginx --no-pager -l | grep "Active:"
echo ""

echo "📋 ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ:"
echo "1. Скачайте клиент CrossDesk: https://www.crossdesk.cn"
echo "2. В настройках клиента включите Self-Hosted Server Configuration"
echo "3. Укажите параметры:"
echo "   - Server Address: $EXTERNAL_IP"
echo "   - Signaling Port: 9099"
echo "   - Relay Port: 3478"
echo "4. Установите доверенный корневой сертификат:"
echo "   Скачайте /var/lib/crossdesk/certs/ca.crt и установите в ОС"
echo ""
echo "✅ Web-интерфейс для просмотра статуса: https://$DOMAIN"
echo "   (если домен настроен и SSL получен)"
echo ""
echo "🌐 Web-клиент CrossDesk: https://web.crossdesk.cn"
echo ""
echo "📊 Полезные команды:"
echo "   - Посмотреть логи контейнера: docker logs crossdesk_server"
echo "   - Перезапустить контейнер: docker restart crossdesk_server"
echo "   - Просмотр статуса: docker ps | grep crossdesk"