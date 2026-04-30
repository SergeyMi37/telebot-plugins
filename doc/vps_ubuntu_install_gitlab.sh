#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_install_gitlab.sh && chmod +x vps_ubuntu_install_gitlab.sh && ./vps_ubuntu_install_gitlab.sh

# Скрипт установки GitLab CE на Ubuntu 22.04/24.04
# Требует прав root

set -e  # Остановить скрипт при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Этот скрипт должен запускаться с root правами${NC}"
   echo "Используйте: sudo ./install_gitlab.sh"
   exit 1
fi

echo -e "${GREEN}=== Установка GitLab CE на VPS ===${NC}"

# Запрос внешнего URL у пользователя
read -p "Введите домен или IP вашего VPS (например, gitlab.example.com или 123.123.123.123): " EXTERNAL_URL

if [[ -z "$EXTERNAL_URL" ]]; then
    echo -e "${RED}URL не может быть пустым. Использую localhost${NC}"
    EXTERNAL_URL="localhost"
fi

echo -e "${YELLOW}1. Обновление системы...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}2. Установка зависимостей...${NC}"
apt install -y curl openssh-server ca-certificates tzdata perl

# Установка Postfix для отправки почтовых уведомлений (опционально)
echo -e "${YELLOW}3. Установка и настройка Postfix...${NC}"
apt install -y postfix
# Postfix автоматически запросит тип конфигурации, выбираем 'Internet Site'

echo -e "${YELLOW}4. Добавление репозитория GitLab...${NC}"
curl -sS https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh | bash

echo -e "${YELLOW}5. Установка GitLab CE (это может занять несколько минут)...${NC}"
EXTERNAL_URL="http://$EXTERNAL_URL" apt install -y gitlab-ce

echo -e "${YELLOW}6. Первичная настройка и запуск GitLab...${NC}"
gitlab-ctl reconfigure

echo -e "${GREEN}=== Установка завершена! ===${NC}"

# Получение пароля root
if [[ -f /etc/gitlab/initial_root_password ]]; then
    ROOT_PASS=$(grep 'Password:' /etc/gitlab/initial_root_password | awk '{print $2}')
    echo -e "${GREEN}Временный пароль администратора (root): $ROOT_PASS${NC}"
    echo -e "${YELLOW}Этот пароль будет удалён через 24 часа или после первого входа. Сохраните его!${NC}"
else
    echo -e "${RED}Файл с паролем не найден. Возможно, GitLab уже был установлен ранее.${NC}"
    echo "Вы можете сбросить пароль командой: sudo gitlab-rake 'gitlab:password:reset[root]'"
fi

echo -e "${GREEN}GitLab доступен по адресу: http://$EXTERNAL_URL${NC}"
echo -e "${YELLOW}Для доступа через HTTPS настройте SSL отдельно (Let's Encrypt или свой сертификат).${NC}"
echo -e "${YELLOW}Для применения изменений конфигурации используйте: sudo gitlab-ctl reconfigure${NC}"
