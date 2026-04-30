#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_install_gitlab_https.sh && chmod +x vps_ubuntu_install_gitlab_https.sh && ./vps_ubuntu_install_gitlab_https.sh

# Установка GitLab CE на Ubuntu 22.04/24.04 с настройкой SSL
# https://chat.deepseek.com/share/ka6rvxex6zoffhtyxl
# Требует прав root

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Проверка root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Запустите с sudo: ./install_gitlab.sh${NC}"
   exit 1
fi

echo -e "${GREEN}=== Установка и настройка GitLab CE с SSL ===${NC}"

# ---------- Ввод данных ----------
read -p "Введите домен (например, gitlab.example.com): " EXTERNAL_URL
[[ -z "$EXTERNAL_URL" ]] && { echo -e "${RED}Домен обязателен${NC}"; exit 1; }

read -p "Email для Let's Encrypt (оставьте пустым, если HTTPS не нужен): " LETSENCRYPT_EMAIL

# Проверка доступности порта 80
echo -e "${YELLOW}Проверка порта 80...${NC}"
if ! ss -tlnp | grep -q ':80 '; then
    echo -e "${GREEN}Порт 80 свободен${NC}"
else
    echo -e "${RED}Порт 80 занят. Остановите nginx/apache и повторите.${NC}"
    exit 1
fi

# ---------- Установка GitLab ----------
echo -e "${YELLOW}1. Обновление системы...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}2. Установка зависимостей...${NC}"
apt install -y curl openssh-server ca-certificates tzdata perl postfix ufw

echo -e "${YELLOW}3. Добавление репозитория GitLab...${NC}"
curl -sS https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh | bash

echo -e "${YELLOW}4. Установка GitLab CE...${NC}"
EXTERNAL_URL="http://$EXTERNAL_URL" apt install -y gitlab-ce

# ---------- Настройка SSL ----------
if [[ -n "$LETSENCRYPT_EMAIL" ]]; then
    echo -e "${GREEN}Настройка HTTPS через Let's Encrypt...${NC}"
    cat >> /etc/gitlab/gitlab.rb <<EOF

# === SSL Let's Encrypt ===
external_url 'https://$EXTERNAL_URL'
letsencrypt['enable'] = true
letsencrypt['contact_emails'] = ['$LETSENCRYPT_EMAIL']
letsencrypt['auto_renew'] = true
letsencrypt['auto_renew_hour'] = 2
letsencrypt['auto_renew_day_of_month'] = "*/1"
EOF

else
    echo -e "${YELLOW}Пропускаем Let's Encrypt. Хотите добавить свой SSL-сертификат? (y/n)${NC}"
    read -p "> " ADD_MANUAL_SSL
    if [[ "$ADD_MANUAL_SSL" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Укажите пути к сертификатам:${NC}"
        read -p "Путь к .crt (fullchain): " SSL_CRT
        read -p "Путь к .key (privkey): " SSL_KEY
        if [[ -f "$SSL_CRT" && -f "$SSL_KEY" ]]; then
            mkdir -p /etc/gitlab/ssl
            cp "$SSL_CRT" "/etc/gitlab/ssl/$EXTERNAL_URL.crt"
            cp "$SSL_KEY" "/etc/gitlab/ssl/$EXTERNAL_URL.key"
            chmod 600 "/etc/gitlab/ssl/$EXTERNAL_URL.key"
            chmod 644 "/etc/gitlab/ssl/$EXTERNAL_URL.crt"
            cat >> /etc/gitlab/gitlab.rb <<EOF

# === SSL ручной сертификат ===
external_url 'https://$EXTERNAL_URL'
nginx['ssl_certificate'] = "/etc/gitlab/ssl/$EXTERNAL_URL.crt"
nginx['ssl_certificate_key'] = "/etc/gitlab/ssl/$EXTERNAL_URL.key"
EOF
        else
            echo -e "${RED}Файлы не найдены. HTTPS настраивать не будем.${NC}"
        fi
    else
        echo -e "${BLUE}Работаем через HTTP. Для HTTPS настройте позже.${NC}"
    fi
fi

# ---------- Настройка фаервола ----------
echo -e "${YELLOW}5. Настройка UFW...${NC}"
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
echo "y" | ufw enable

# ---------- Применение конфигурации ----------
echo -e "${YELLOW}6. Переконфигурация GitLab (это займёт несколько минут)...${NC}"
gitlab-ctl reconfigure

# ---------- Вывод пароля и информации ----------
echo -e "${GREEN}=== Установка завершена! ===${NC}"
if [[ -f /etc/gitlab/initial_root_password ]]; then
    ROOT_PASS=$(grep 'Password:' /etc/gitlab/initial_root_password | awk '{print $2}')
    echo -e "${GREEN}Временный пароль root: $ROOT_PASS${NC}"
    echo -e "${RED}Сохраните его! Файл удалится через 24 часа.${NC}"
fi

if [[ -n "$LETSENCRYPT_EMAIL" ]]; then
    echo -e "${GREEN}GitLab доступен по HTTPS: https://$EXTERNAL_URL${NC}"
else
    echo -e "${GREEN}GitLab доступен по HTTP: http://$EXTERNAL_URL${NC}"
fi

# ---------- Вывод справки по управлению ----------
show_help() {
    echo -e "\n${BLUE}=== ПОЛЕЗНЫЕ КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ GITLAB ===${NC}"
    cat <<EOF

${YELLOW}🔧 Общее управление:${NC}
  sudo gitlab-ctl status          - статус всех компонентов
  sudo gitlab-ctl start/stop/restart - запуск/остановка/перезапуск
  sudo gitlab-ctl reconfigure     - применить изменения из /etc/gitlab/gitlab.rb
  sudo gitlab-ctl tail            - просмотр логов в реальном времени
  sudo gitlab-ctl show-config     - показать текущую конфигурацию

${YELLOW}👤 Пользователи и пароли:${NC}
  sudo gitlab-rake "gitlab:password:reset[root]" - сброс пароля root
  sudo gitlab-rails console        - консоль Rails (для администрирования)
  sudo gitlab-ctl status postgresql - статус БД

${YELLOW}💾 Резервное копирование и восстановление:${NC}
  sudo gitlab-backup create        - создать резервную копию
  sudo gitlab-backup restore       - восстановить (указав BACKUP=timestamp)
  # Резервные копии хранятся в /var/opt/gitlab/backups/

${YELLOW}🔐 SSL и сертификаты:${NC}
  sudo letsencrypt renew           - ручное обновление (если используется LE)
  sudo gitlab-ctl renew-le-certs    - принудительное обновление сертификатов LE
  # Ручной сертификат: поместите файлы в /etc/gitlab/ssl/ и выполните reconfigure

${YELLOW}📊 Мониторинг и логи:${NC}
  sudo gitlab-ctl tail nginx       - логи nginx
  sudo gitlab-ctl tail postgresql  - логи PostgreSQL
  sudo gitlab-rake gitlab:check    - диагностика системы
  sudo gitlab-rake gitlab:env:info - информация об окружении

${YELLOW}🛠 Обновление GitLab:${NC}
  sudo apt update && sudo apt install gitlab-ce -y   - обновление до последней версии
  sudo gitlab-ctl reconfigure && sudo gitlab-ctl restart

${YELLOW}📁 Важные директории:${NC}
  /etc/gitlab/                     - конфигурация (gitlab.rb)
  /var/opt/gitlab/                 - данные, репозитории, БД
  /var/log/gitlab/                 - все логи
  /etc/gitlab/ssl/                 - SSL-сертификаты

${YELLOW}🌐 Доступ через браузер:${NC}
  ${GREEN}http${NC}://$EXTERNAL_URL  или  ${GREEN}https${NC}://$EXTERNAL_URL (если настроен)

${BLUE}Подробная документация: https://docs.gitlab.com/ee/administration/${NC}
EOF
}

# Сохраняем справку в файл и показываем
show_help > /root/gitlab_help.txt
show_help

echo -e "\n${GREEN}Справка сохранена в /root/gitlab_help.txt${NC}"
echo -e "${YELLOW}Для повторного просмотра выполните: cat /root/gitlab_help.txt${NC}"