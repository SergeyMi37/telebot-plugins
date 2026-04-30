#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_install_rustdesk.sh && chmod +x vps_ubuntu_install_rustdesk.sh && ./vps_ubuntu_install_rustdesk.sh

# RustDesk Server Auto-Installation Script with Let's Encrypt HTTPS
# Tested on Ubuntu 20.04 / 22.04 / 24.04
# Based on official RustDesk documentation [citation:9]
#  https://github.com/rustdesk/rustdesk 
#  https://chat.deepseek.com/share/n2j9jxe6ebjo89q199

set -e  # Exit on any error

# Цветной вывод для удобства чтения
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "\n${BLUE}==>${NC} ${GREEN}$1${NC}"; }

# Проверка запуска от root
if [[ $EUID -ne 0 ]]; then
   print_error "Этот скрипт должен запускаться от root (sudo)"
   exit 1
fi

# === ВВОД ДАННЫХ ===
clear
echo "========================================="
echo "   RustDesk Server Installation Script"
echo "========================================="
echo ""
echo "Данный скрипт установит:"
echo "  • Docker и Docker Compose"
echo "  • RustDesk Server (hbbs + hbbr) в контейнерах"
echo "  • Nginx с Let's Encrypt SSL сертификатом"
echo "  • Настроит файрвол и необходимые порты"
echo ""

read -p "Введите ваш домен (например, rustdesk.example.com): " DOMAIN
read -p "Введите ваш email для Let's Encrypt уведомлений: " EMAIL

# Проверка ввода
if [[ -z "$DOMAIN" ]] || [[ -z "$EMAIL" ]]; then
    print_error "Домен и email обязательны для заполнения!"
    exit 1
fi

print_info "Домен: $DOMAIN"
print_info "Email: $EMAIL"

# === 1. ОБНОВЛЕНИЕ СИСТЕМЫ ===
print_step "Шаг 1/7: Обновление системы..."
apt update && apt upgrade -y

# === 2. УСТАНОВКА DEPENDENCIES ===
print_step "Шаг 2/7: Установка зависимостей..."
apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    wget \
    software-properties-common \
    nginx \
    ufw \
    gnupg \
    lsb-release

# === 3. УСТАНОВКА DOCKER ===
print_step "Шаг 3/7: Установка Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    print_info "Docker установлен"
else
    print_info "Docker уже установлен"
fi

# Установка Docker Compose Plugin
if ! docker compose version &> /dev/null; then
    print_info "Установка Docker Compose Plugin..."
    apt install -y docker-compose-plugin
fi

print_info "Версия Docker: $(docker --version)"
print_info "Версия Docker Compose: $(docker compose version)"

# === 4. НАСТРОЙКА ФАЙРВОЛА ===
print_step "Шаг 4/7: Настройка файрвола..."
# Порты RustDesk [citation:7][citation:9]
# 21115: NAT type test
# 21116 TCP/UDP: ID registration, heartbeat, hole punching  
# 21117 TCP: Relay service
# 21118 TCP: Web client support (hbbs)
# 21119 TCP: Web client support (hbbr)
# 21114 TCP: Web console (Pro version)

ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP (Let\'s Encrypt)'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 21115/tcp comment 'RustDesk NAT test'
ufw allow 21116/tcp comment 'RustDesk TCP hole punching'
ufw allow 21116/udp comment 'RustDesk ID registration'
ufw allow 21117/tcp comment 'RustDesk Relay'
ufw allow 21118/tcp comment 'RustDesk Web client hbbs'
ufw allow 21119/tcp comment 'RustDesk Web client hbbr'

echo "y" | ufw enable
ufw status
print_info "Файрвол настроен"

# === 5. СОЗДАНИЕ ДИРЕКТОРИЙ И DOCKER COMPOSE ===
print_step "Шаг 5/7: Настройка RustDesk Server..."

# Создаем директории
mkdir -p /opt/rustdesk/data
cd /opt/rustdesk

# Создаем docker-compose.yml [citation:1]
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
    depends_on:
      - hbbr

  hbbr:
    image: rustdesk/rustdesk-server:latest
    container_name: rustdesk_hbbr
    command: hbbr
    restart: unless-stopped
    volumes:
      - /opt/rustdesk/data:/root
    network_mode: host
EOF

print_info "Docker Compose файл создан"

# Запускаем контейнеры
print_info "Запуск RustDesk контейнеров..."
docker compose up -d

# Проверяем статус
sleep 5
if docker ps | grep -q "rustdesk"; then
    print_info "Контейнеры успешно запущены"
    docker ps --filter "name=rustdesk" --format "table {{.Names}}\t{{.Status}}"
else
    print_error "Проблема с запуском контейнеров"
    docker compose logs
    exit 1
fi

# Получаем публичный ключ [citation:1][citation:8]
print_info "Получение ключа сервера..."
sleep 3
if [ -f /opt/rustdesk/data/id_ed25519.pub ]; then
    RUSTDESK_KEY=$(cat /opt/rustdesk/data/id_ed25519.pub)
    print_info "Ключ сервера: $RUSTDESK_KEY"
else
    print_warn "Ключ еще не сгенерирован, ожидаем..."
    sleep 10
    if [ -f /opt/rustdesk/data/id_ed25519.pub ]; then
        RUSTDESK_KEY=$(cat /opt/rustdesk/data/id_ed25519.pub)
        print_info "Ключ сервера: $RUSTDESK_KEY"
    else
        print_error "Не удалось получить ключ сервера"
        RUSTDESK_KEY="НЕ ДОСТУПЕН - проверьте позже в /opt/rustdesk/data/id_ed25519.pub"
    fi
fi

# === 6. НАСТРОЙКА NGINX И LET'S ENCRYPT ===
print_step "Шаг 6/7: Настройка Nginx и Let's Encrypt..."

# Создаем директорию для webroot
mkdir -p /var/www/html

# Создаем временную конфигурацию Nginx для получения сертификата
cat > /etc/nginx/sites-available/$DOMAIN <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        allow all;
    }
    
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

# Активируем конфигурацию
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default 2>/dev/null

# Проверяем конфигурацию
nginx -t && systemctl reload nginx

# Установка Certbot
print_info "Установка Certbot..."
apt install -y certbot python3-certbot-nginx

# Получение SSL сертификата [citation:1][citation:5]
print_info "Получение SSL сертификата от Let's Encrypt..."
systemctl stop nginx

certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"

if [ $? -eq 0 ]; then
    print_info "SSL сертификат успешно получен!"
    
    # Создаем полную конфигурацию Nginx [citation:1][citation:4]
    cat > /etc/nginx/sites-available/$DOMAIN <<'EOF'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name DOMAIN_PLACEHOLDER;

    ssl_certificate /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://127.0.0.1:21118;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    
    # Подставляем домен в конфигурацию
    sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /etc/nginx/sites-available/$DOMAIN
    
    # Запускаем Nginx
    systemctl start nginx
    nginx -t && systemctl reload nginx
    
    # Настраиваем автоматическое обновление сертификатов
    (crontab -l 2>/dev/null; echo "0 3 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
    print_info "Автоматическое обновление сертификатов настроено"
    
    SSL_STATUS="✅ SSL сертификат активен (Let's Encrypt)"
else
    print_warn "Не удалось получить Let's Encrypt сертификат"
    SSL_STATUS="❌ SSL не настроен - проверьте DNS записи"
    systemctl start nginx
fi

# === 7. СОЗДАНИЕ ИНФОРМАЦИОННОЙ СТРАНИЦЫ ===
print_step "Шаг 7/7: Создание информационной страницы..."

# Создаем HTML страницу с информацией о подключении
mkdir -p /var/www/rustdesk-info

cat > /var/www/rustdesk-info/index.html <<EOF
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RustDesk Server - готов к работе</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        .card { 
            background: white; 
            border-radius: 16px; 
            padding: 30px; 
            margin: 20px 0;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 { color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 15px; margin-bottom: 20px; }
        h2 { color: #764ba2; margin: 20px 0 15px 0; font-size: 1.4em; }
        .status { 
            display: inline-block; 
            background: #27ae60; 
            color: white; 
            padding: 8px 20px; 
            border-radius: 30px; 
            font-weight: bold;
            margin-bottom: 20px;
        }
        .code { 
            background: #1e1e1e; 
            color: #d4d4d4; 
            padding: 15px 20px; 
            border-radius: 10px; 
            font-family: 'Courier New', monospace; 
            overflow-x: auto; 
            font-size: 14px;
            margin: 15px 0;
        }
        .info-box {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px 20px;
            margin: 15px 0;
            border-radius: 8px;
        }
        .warning-box {
            background: #fff3e0;
            border-left: 4px solid #e67e22;
            padding: 15px 20px;
            margin: 15px 0;
            border-radius: 8px;
        }
        .success-box {
            background: #e8f8f0;
            border-left: 4px solid #27ae60;
            padding: 15px 20px;
            margin: 15px 0;
            border-radius: 8px;
        }
        hr { margin: 20px 0; border: none; border-top: 1px solid #e0e0e0; }
        .footer { text-align: center; color: rgba(255,255,255,0.8); margin-top: 30px; }
        .key { 
            background: #2c3e50; 
            color: #ecf0f1; 
            padding: 12px; 
            border-radius: 8px;
            font-family: monospace;
            word-break: break-all;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover { background: #5a67d8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🚀 RustDesk Server</h1>
            <p><span class="status">✅ Сервер работает</span></p>
            
            <div class="success-box">
                <strong>🎉 Установка завершена!</strong><br>
                Ваш персональный RustDesk сервер готов к использованию.
            </div>

            <h2>📡 Данные для подключения клиента</h2>
            <div class="info-box">
                <strong>ID сервера (Host):</strong><br>
                <code class="key">$DOMAIN</code> или <code>$(curl -s ifconfig.me)</code><br><br>
                <strong>Ключ (Key):</strong><br>
                <code class="key" id="serverKey">$RUSTDESK_KEY</code>
                <button onclick="copyKey()">📋 Копировать ключ</button>
            </div>

            <h2>🔧 Как настроить клиент RustDesk</h2>
            <div class="info-box">
                <ol style="margin-left: 20px;">
                    <li>Скачайте клиент с <a href="https://rustdesk.com/download" target="_blank">официального сайта</a></li>
                    <li>Откройте настройки (шестеренка в правом верхнем углу)</li>
                    <li>Перейдите в раздел <strong>Network</strong></li>
                    <li>В поле <strong>ID Server</strong> введите: <code>$DOMAIN</code> или IP сервера</li>
                    <li>В поле <strong>Key</strong> вставьте ключ, указанный выше</li>
                    <li>Нажмите <strong>Apply</strong> и перезапустите клиент</li>
                </ol>
            </div>

            <div class="warning-box">
                <strong>⚠️ Важно!</strong><br>
                • Убедитесь, что ключ скопирован полностью, включая все символы<br>
                • Настройки нужно применить на КАЖДОМ клиентском устройстве<br>
                • После настройки статус соединения должен стать зеленым ("Ready")
            </div>

            <h2>📊 Статус сервера</h2>
            <div class="code">
Контейнеры:
$(docker ps --filter "name=rustdesk" --format "  • {{.Names}}: {{.Status}}")

Порты:
  • 21115 (TCP) - NAT тестирование
  • 21116 (TCP+UDP) - Регистрация и подключение
  • 21117 (TCP) - Релейный сервер
  • 21118-21119 (TCP) - Веб-поддержка

SSL: $SSL_STATUS
            </div>

            <h2>🖥️ Просмотр логов</h2>
            <div class="code">
# Логи hbbs (сервер регистрации)
docker logs -f rustdesk_hbbs

# Логи hbbr (релейный сервер)
docker logs -f rustdesk_hbbr
            </div>

            <h2>🔄 Полезные команды</h2>
            <div class="code">
# Перезапуск сервера
cd /opt/rustdesk && docker compose restart

# Остановка сервера
cd /opt/rustdesk && docker compose down

# Обновление до последней версии
cd /opt/rustdesk && docker compose pull && docker compose up -d

# Просмотр ключа (если потеряли)
cat /opt/rustdesk/data/id_ed25519.pub

# Проверка статуса контейнеров
docker ps --filter "name=rustdesk"
            </div>

            <hr>
            <p style="font-size: 12px; color: #7f8c8d; text-align: center;">
                RustDesk Server установлен $(date '+%d.%m.%Y %H:%M:%S')<br>
                Документация: <a href="https://rustdesk.com/docs" target="_blank">https://rustdesk.com/docs</a>
            </p>
        </div>
        <div class="footer">
            <p>Ваш персональный RustDesk сервер | Полный контроль над удаленными подключениями</p>
        </div>
    </div>

    <script>
        function copyKey() {
            const key = document.getElementById('serverKey').innerText;
            navigator.clipboard.writeText(key).then(() => {
                alert('Ключ скопирован в буфер обмена!');
            });
        }
    </script>
</body>
</html>
EOF

# Настраиваем Nginx для отображения информационной страницы
cat > /etc/nginx/sites-available/info <<EOF
server {
    listen 8080;
    server_name _;
    root /var/www/rustdesk-info;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF

ln -sf /etc/nginx/sites-available/info /etc/nginx/sites-enabled/
systemctl reload nginx

# === ФИНАЛЬНАЯ ИНФОРМАЦИЯ ===
print_step "Установка завершена!"

clear
echo "========================================="
echo "  ✅ RustDesk Server успешно установлен!"
echo "========================================="
echo ""

echo "📋 ДАННЫЕ ДЛЯ ПОДКЛЮЧЕНИЯ:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 ID сервера (Host): $DOMAIN"
echo "🔑 Ключ (Key): $RUSTDESK_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 ИНСТРУКЦИЯ ПО НАСТРОЙКЕ КЛИЕНТА:"
echo "1. Скачайте RustDesk: https://rustdesk.com/download"
echo "2. Откройте Настройки → Network"
echo "3. Введите ID сервера и Key (поля выше)"
echo "4. Нажмите Apply и перезапустите клиент"
echo ""
echo "🌐 Информационная страница: http://$(curl -s ifconfig.me):8080"
echo "📁 Файлы сервера: /opt/rustdesk/"
echo "📝 Логи: docker logs -f rustdesk_hbbs / rustdesk_hbbr"
echo ""

# Вывод статуса контейнеров
echo "Статус контейнеров:"
docker ps --filter "name=rustdesk" --format "table {{.Names}}\t{{.Status}}"

echo ""
print_info "Скрипт успешно завершен!"