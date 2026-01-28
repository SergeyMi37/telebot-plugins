#!/bin/bash

# Скрипт автоматической установки GitLab CE на Ubuntu 22.04
# # Требует запуска от root или через sudo
#  Просмотр пароля root
# sudo cat /etc/gitlab/initial_root_password

# # Мониторинг состояния GitLab
# sudo gitlab-ctl status

# # Просмотр логов
# sudo gitlab-ctl tail
# 🔧 Дополнительные команды для управления
# bash
# # Остановка/запуск GitLab
# sudo gitlab-ctl stop
# sudo gitlab-ctl start
# sudo gitlab-ctl restart

# # Резервное копирование
# sudo gitlab-rake gitlab:backup:create

# # Восстановление из бекапа
# sudo gitlab-ctl stop unicorn puma sidekiq
# sudo gitlab-rake gitlab:backup:restore BACKUP=timestamp

# # Обновление GitLab
# sudo apt update
# sudo apt install gitlab-ce
# sudo gitlab-ctl reconfigure

set -e  # Прекратить выполнение при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ОШИБКА: $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ВНИМАНИЕ: $1${NC}"
}

# Проверка прав администратора
if [ "$EUID" -ne 0 ]; then 
    error "Для запуска требуются права администратора. Используйте: sudo bash $0"
fi

# Конфигурационные параметры (можно менять)
DOMAIN_OR_IP="localhost"  # Замените на ваш домен/IP
GITLAB_VERSION="latest"    # Версия GitLab (latest или конкретная, например: 17.0.0-ce.0)
LETSENCRYPT_EMAIL=""       # Email для Let's Encrypt (оставьте пустым для отключения SSL)
SWAP_SIZE="4G"            # Размер swap-файла (рекомендуется 4G для систем с 2-4GB RAM)

log "Начинаем установку GitLab CE на Ubuntu 22.04"

# Проверка системы
log "Проверка системы..."
RAM=$(free -g | awk '/^Mem:/ {print $2}')
if [ "$RAM" -lt 4 ]; then
    warn "Обнаружено только ${RAM}GB RAM. GitLab рекомендует минимум 4GB."
    warn "Будет создан swap-файл размером ${SWAP_SIZE}."
    
    # Создание swap-файла
    if [ ! -f /swapfile ]; then
        log "Создание swap-файла размером ${SWAP_SIZE}..."
        fallocate -l $SWAP_SIZE /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
        sysctl vm.swappiness=10
        echo 'vm.swappiness=10' >> /etc/sysctl.conf
        log "Swap-файл успешно создан"
    else
        log "Swap-файл уже существует"
    fi
fi

# Обновление системы
log "Обновление пакетов системы..."
apt-get update
apt-get upgrade -y

# Установка зависимостей
log "Установка необходимых зависимостей..."
apt-get install -y curl wget ca-certificates apt-transport-https \
    gnupg lsb-release ufw

# Настройка базового firewall (UFW)
log "Настройка firewall..."
ufw allow OpenSSH
ufw allow http
ufw allow https
ufw --force enable

# Установка и настройка Postfix для email
log "Настройка Postfix для отправки email..."
debconf-set-selections <<< "postfix postfix/mailname string $DOMAIN_OR_IP"
debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'"
apt-get install -y postfix
systemctl enable postfix

# Добавление репозитория GitLab
log "Добавление официального репозитория GitLab..."
curl -sS https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh | bash

# Установка GitLab CE
log "Установка GitLab CE (версия: $GITLAB_VERSION)..."
if [ "$GITLAB_VERSION" = "latest" ]; then
    apt-get install -y gitlab-ce
else
    apt-get install -y gitlab-ce=$GITLAB_VERSION
fi

# Настройка GitLab
log "Конфигурация GitLab..."

# Создание резервной копии конфига
cp /etc/gitlab/gitlab.rb /etc/gitlab/gitlab.rb.backup.$(date +%Y%m%d%H%M%S)

# Базовая конфигурация
cat > /etc/gitlab/gitlab.rb << EOF
external_url 'http://${DOMAIN_OR_IP}'
gitlab_rails['time_zone'] = 'UTC'

# Настройки почты (раскомментируйте и настройте при необходимости)
# gitlab_rails['smtp_enable'] = true
# gitlab_rails['smtp_address'] = "smtp.gmail.com"
# gitlab_rails['smtp_port'] = 587
# gitlab_rails['smtp_user_name'] = "your_email@gmail.com"
# gitlab_rails['smtp_password'] = "your_password"
# gitlab_rails['smtp_domain'] = "gmail.com"
# gitlab_rails['smtp_authentication'] = "login"
# gitlab_rails['smtp_enable_starttls_auto'] = true

# Настройка Let's Encrypt SSL
letsencrypt['enable'] = false
letsencrypt['contact_emails'] = ['${LETSENCRYPT_EMAIL}']
letsencrypt['group'] = 'root'
letsencrypt['key_size'] = 2048
letsencrypt['owner'] = 'root'
letsencrypt['wwwroot'] = '/var/opt/gitlab/nginx/www'

# Если используете HTTPS, раскомментируйте:
# external_url 'https://${DOMAIN_OR_IP}'
# nginx['redirect_http_to_https'] = true

# Оптимизация для сервера с 4GB RAM
puma['worker_processes'] = 2
sidekiq['max_concurrency'] = 10
postgresql['shared_buffers'] = "256MB"
postgresql['max_worker_processes'] = 4
EOF

# Если указан email для Let's Encrypt, включаем SSL
if [ -n "$LETSENCRYPT_EMAIL" ]; then
    log "Настройка Let's Encrypt SSL..."
    sed -i "s/external_url 'http:/external_url 'https:/" /etc/gitlab/gitlab.rb
    sed -i "s/letsencrypt\['enable'\] = false/letsencrypt['enable'] = true/" /etc/gitlab/gitlab.rb
    sed -i "s/# nginx\['redirect_http_to_https'\] = true/nginx['redirect_http_to_https'] = true/" /etc/gitlab/gitlab.rb
fi

# Применение конфигурации GitLab
log "Применение конфигурации GitLab (это может занять несколько минут)..."
gitlab-ctl reconfigure

# Включение автозапуска GitLab
systemctl enable gitlab-runsvdir

# Проверка состояния служб
log "Проверка состояния служб GitLab..."
gitlab-ctl status

# Вывод информации для доступа
log "================================================"
log "УСТАНОВКА УСПЕШНО ЗАВЕРШЕНА!"
log "================================================"
log "Доступ к GitLab: http://${DOMAIN_OR_IP}"
if [ -n "$LETSENCRYPT_EMAIL" ]; then
    log "Также по HTTPS: https://${DOMAIN_OR_IP}"
fi
log ""
log "Для первого входа используйте:"
log "Логин: root"
log "Пароль находится в файле: /etc/gitlab/initial_root_password"
log ""
log "Для просмотра пароля выполните:"
log "sudo cat /etc/gitlab/initial_root_password"
log ""
log "ВАЖНО: После первого входа немедленно смените пароль!"
log "================================================"

# Показ IP адресов для доступа
log "Сетевые интерфейсы сервера:"
ip -br addr show | grep -v lo