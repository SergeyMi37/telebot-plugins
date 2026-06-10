# 🔄 Настройка FRP для вебхуков Telegram через VPS

## 📋 Как работает схема

```
Telegram → VPS (FRP сервер + Caddy) → FRP туннель → Ваш локальный компьютер → Django бот
```

1. **Telegram** отправляет вебхук на `https://telega.example.com/webhook/`
2. **Caddy** на VPS принимает HTTPS и проксирует на FRP сервер (порт 8443)
3. **FRP сервер** передаёт запрос по туннелю на ваш локальный компьютер
4. **Django бот** обрабатывает запрос и отправляет ответ обратно

---

## 🚀 Быстрый старт

### Требования

- VPS с публичным IP-адресом
- Доменное имя, указывающее на VPS
- Локальный компьютер с Django ботом
- Токен Telegram бота

### Минимальные порты на VPS

| Порт | Протокол | Описание |
|------|----------|----------|
| 80   | HTTP     | Caddy (перенаправление на HTTPS) |
| 443  | HTTPS    | Caddy (основной вход) |
| 7000 | TCP      | FRP сервер (управление) |
| 8080 | HTTP     | FRP HTTP прокси |
| 8443 | HTTPS    | FRP HTTPS прокси |

---

## 📦 Установка и настройка

### Шаг 1: Установка FRP на VPS (сервер)

```bash
# Скачайте последнюю версию FRP
cd /opt
wget https://github.com/fatedier/frp/releases/download/v0.60.0/frp_0.60.0_linux_amd64.tar.gz
tar -xzf frp_0.60.0_linux_amd64.tar.gz
mv frp_0.60.0_linux_amd64 frp
cd frp
```

**Создайте конфигурационный файл `frps.toml`:**

```toml
# frps.toml - конфигурация FRP сервера
bindAddr = "0.0.0.0"
bindPort = 7000

# Для HTTP/HTTPS проксирования
vhostHTTPPort = 8080
vhostHTTPSPort = 8443

# Логирование
log.file = "/var/log/frps.log"
log.level = "info"
log.maxDays = 3

# Аутентификация (рекомендуется)
auth.method = "token"
auth.token = "your-secret-token-here"

# Детали транспорта
transport.tcpMux = true
transport.tcpMuxKeepaliveInterval = 30
```

**Создайте systemd сервис:**

```bash
sudo cat > /etc/systemd/system/frps.service << 'EOF'
[Unit]
Description=FRP Server
After=network.target

[Service]
Type=simple
ExecStart=/opt/frp/frps -c /opt/frp/frps.toml
Restart=always
RestartSec=5
User=nobody

[Install]
WantedBy=multi-user.target
EOF

# Запустите сервер
sudo systemctl daemon-reload
sudo systemctl start frps
sudo systemctl enable frps
sudo systemctl status frps
```

---

### Шаг 2: Установка FRP на локальный компьютер (клиент)

**Скачайте FRP для вашей ОС:**

| ОС | Ссылка |
|----|--------|
| Windows | [frp_0.60.0_windows_amd64.zip](https://github.com/fatedier/frp/releases/download/v0.60.0/frp_0.60.0_windows_amd64.zip) |
| macOS | [frp_0.60.0_darwin_amd64.tar.gz](https://github.com/fatedier/frp/releases/download/v0.60.0/frp_0.60.0_darwin_amd64.tar.gz) |
| Linux | [frp_0.60.0_linux_amd64.tar.gz](https://github.com/fatedier/frp/releases/download/v0.60.0/frp_0.60.0_linux_amd64.tar.gz) |

**Создайте конфигурационный файл `frpc.toml`:**

```toml
# frpc.toml - конфигурация FRP клиента
serverAddr = "IP_ВАШЕГО_VPS"  # Замените на реальный IP
serverPort = 7000

# Аутентификация (должна совпадать с сервером)
auth.method = "token"
auth.token = "your-secret-token-here"

# Настройки соединения
transport.tcpMux = true
transport.poolCount = 5
transport.heartbeatTimeout = 90
transport.heartbeatInterval = 30

# Прокси для вебхуков (HTTPS)
[[proxies]]
name = "telegram-webhook"
type = "https"
localIP = "127.0.0.1"
localPort = 8000
customDomains = ["telega.example.com"]  # Замените на ваш домен
transport.proxyProtocolVersion = "v2"

# Опционально: дополнительный порт для отладки (HTTP)
[[proxies]]
name = "telegram-webhook-http"
type = "http"
localIP = "127.0.0.1"
localPort = 8000
customDomains = ["telega.example.com"]
```

**Запустите клиент:**

```bash
# macOS/Linux
cd /opt/frp
./frpc -c frpc.toml

# Windows (cmd от имени администратора)
C:\frp\frpc.exe -c frpc.toml
```

---

### Шаг 3: Настройка Caddy на VPS (для HTTPS)

**Установите Caddy:**

```bash
# Debian/Ubuntu
sudo apt install -y caddy

# CentOS/RHEL
sudo yum install -y caddy
```

**Создайте конфигурацию `Caddyfile`:**

```caddy
telega.example.com {
    # Проксируем на FRP порт
    reverse_proxy localhost:8443 {
        # Передаем реальный IP клиента
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
    
    # Настройки логов
    log {
        output file /var/log/caddy/telega.log
    }
    
    # Таймауты для вебхуков
    timeouts {
        read 30s
        write 30s
    }
}
```

**Перезапустите Caddy:**

```bash
sudo systemctl reload caddy
sudo systemctl status caddy
```

---

### Шаг 4: Настройка Django бота (локально)

**`docker-compose.yml`:**

```yaml
version: "3.8"

services:
  web:
    build:
      context: .
      dockerfile: LocalDockerfile
    container_name: dtb_django
    command: gunicorn dtb.wsgi:application --bind 0.0.0.0:8000 --workers 4
    ports:
      - "8000:8000"
    env_file:
      - ./.env
```

**`.env` файл:**

```bash
# Режим работы
BOT_MODE=webhook
DOMAIN=telega.example.com
WEBHOOK_SECRET_PATH=<WEBHOOK_SECRET_PATH>/
TELEGRAM_TOKEN=<TELEGRAM_TOKEN>

# Django настройки
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
USE_X_FORWARDED_HOST=True
CSRF_TRUSTED_ORIGINS=https://telega.example.com
APPEND_SLASH=False
```

---

## 🎯 Запуск всей схемы

### 1. Запустите FRP сервер на VPS

```bash
sudo systemctl start frps
sudo systemctl status frps
```

### 2. Запустите FRP клиент на локальном компьютере

```bash
cd /opt/frp
./frpc -c frpc.toml
```

### 3. Запустите Django бота

```bash
docker-compose --profile webhook up -d
```

### 4. Зарегистрируйте вебхук

```bash
curl -F "url=https://telega.example.com/webhook/" \
  https://api.telegram.org/bot<TELEGRAM_TOKEN>/setWebhook
```

### 5. Проверьте статус

```bash
curl https://api.telegram.org/bot<TELEGRAM_TOKEN>/getWebhookInfo
```

---

## 📊 Мониторинг и отладка

### Проверка статуса FRP туннеля

```bash
# На VPS (логи сервера)
sudo journalctl -u frps -f

# На локальном компьютере (статус клиента)
./frpc status -c frpc.toml
```

### Проверка работы туннеля

```bash
# На VPS (должен вернуть ответ от бота)
curl -v http://localhost:8443/health/

# На локальном компьютере
curl -X POST http://localhost:8000/health/
```

### Проверка Caddy

```bash
# Логи Caddy
sudo tail -f /var/log/caddy/telega.log

# Статус Caddy
sudo systemctl status caddy
```

---

## 🐛 Частые проблемы и решения

| Проблема | Возможная причина | Решение |
|----------|-------------------|---------|
| `connection refused` | FRP клиент не запущен | Проверьте `./frpc status -c frpc.toml` |
| `502 Bad Gateway` | FRP сервер не видит клиента | Убедитесь, что порт 7000 открыт на VPS |
| Туннель не создаётся | Несовпадение доменов | Проверьте, что `customDomains` совпадает с `Caddyfile` |
| Telegram не принимает вебхук | Проблема с HTTPS | Проверьте логи Caddy и статус туннеля |
| Webhook не работает | Порт 8000 занят | Проверьте, что Django запущен на `0.0.0.0:8000` |
| Таймауты запросов | Блокировка файрволом | Откройте порты 7000, 8080, 8443 на VPS |

---

## 🔄 Автозапуск FRP клиента

### Linux (systemd)

```bash
# Создайте сервис для автозапуска
sudo cat > /etc/systemd/system/frpc.service << 'EOF'
[Unit]
Description=FRP Client
After=network.target

[Service]
Type=simple
ExecStart=/opt/frp/frpc -c /opt/frp/frpc.toml
Restart=always
RestartSec=5
User=ваш_пользователь

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start frpc
sudo systemctl enable frpc
```

### macOS (launchd)

```bash
# Создайте скрипт запуска
cat > ~/start-frpc.sh << 'EOF'
#!/bin/bash
cd /opt/frp
./frpc -c frpc.toml
EOF

chmod +x ~/start-frpc.sh

# Добавьте в launchd (для автозапуска при входе)
cat > ~/Library/LaunchAgents/com.frpc.start.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.frpc.start</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/ваш_пользователь/start-frpc.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.frpc.start.plist
```

### Windows (Task Scheduler)

```powershell
# Создайте .bat файл
echo C:\frp\frpc.exe -c C:\frp\frpc.toml > C:\frp\start-frpc.bat

# Добавьте в планировщик задач с запуском при старте системы
```

---

## 🔒 Безопасность

1. **Замените секретный токен** в конфигурационных файлах на уникальный
2. **Ограничьте доступ** к портам FRP через файрвол
3. **Используйте HTTPS** всегда (Caddy автоматически получает SSL-сертификат)
4. **Регулярно обновляйте** FRP до последней версии

---

## 📚 Дополнительные ресурсы

- [Официальная документация FRP](https://github.com/fatedier/frp)
- [Документация Caddy](https://caddyserver.com/docs/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

Теперь ваш локальный бот доступен через публичный HTTPS домен, даже если компьютер находится за NAT или файрволом.