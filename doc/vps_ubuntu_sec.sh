#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_sec.sh && chmod +x vps_ubuntu.sh && ./vps_ubuntu_sec.sh
# bash <(wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_sec.sh)
set -e  # Прерывать выполнение при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для проверки выполнения команд
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[✓] $1${NC}"
    else
        echo -e "${RED}[✗] $1${NC}"
        exit 1
    fi
}

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Этот скрипт должен запускаться с правами root${NC}" 
   exit 1
fi

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Установка безопасного рабочего пространства${NC}"
echo -e "${BLUE}================================${NC}\n"

# Обновление системы
echo -e "${YELLOW}[1/8] Обновление системы...${NC}"
apt-get update && apt-get upgrade -y
check_success "Система обновлена"

# Установка базовых пакетов безопасности
echo -e "\n${YELLOW}[2/8] Установка базовых пакетов безопасности...${NC}"
apt-get install -y \
    ufw \
    fail2ban \
    unattended-upgrades \
    apt-listchanges \
    rkhunter \
    chkrootkit \
    lynis \
    iptables \
    netfilter-persistent \
    curl \
    wget \
    vim \
    htop \
    tmux \
    git \
    build-essential \
    tor \
    torsocks \
    proxychains4 \
    openvpn \
    wireguard \
    macchanger

check_success "Пакеты безопасности установлены"

# Настройка автоматических обновлений безопасности
echo -e "\n${YELLOW}[3/8] Настройка автоматических обновлений безопасности...${NC}"
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESM:${distro_codename}";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";
EOF

cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

check_success "Автоматические обновления настроены"

# Настройка файрвола (UFW)
echo -e "\n${YELLOW}[4/8] Настройка файрвола...${NC}"
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh  # Разрешить SSH (будет изменено позже)

# Спрашиваем пользователя о порте SSH
read -p "Хотите изменить стандартный порт SSH (22)? (y/n): " change_ssh_port
if [[ $change_ssh_port == "y" || $change_ssh_port == "Y" ]]; then
    read -p "Введите новый порт для SSH (1024-65535): " new_ssh_port
    if [[ $new_ssh_port -ge 1024 && $new_ssh_port -le 65535 ]]; then
        # Изменение порта SSH
        sed -i "s/#Port 22/Port $new_ssh_port/" /etc/ssh/sshd_config
        ufw allow $new_ssh_port/tcp
        ufw delete allow ssh
        echo -e "${GREEN}SSH порт изменен на $new_ssh_port${NC}"
    else
        echo -e "${RED}Неверный порт. Используется стандартный порт 22${NC}"
    fi
fi

# Дополнительные настройки безопасности SSH
cat >> /etc/ssh/sshd_config << 'EOF'
# Усиление безопасности SSH
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
MaxSessions 2
ClientAliveInterval 300
ClientAliveCountMax 2
Protocol 2
EOF

ufw --force enable
check_success "Файрвол настроен и включен"

# Настройка Tor и Proxychains
echo -e "\n${YELLOW}[5/8] Настройка анонимизации (Tor, Proxychains)...${NC}"

# Настройка Tor
systemctl enable tor
systemctl start tor

# Настройка proxychains
cat > /etc/proxychains4.conf << 'EOF'
strict_chain
proxy_dns 
tcp_read_time_out 15000
tcp_connect_time_out 8000
[ProxyList]
socks4 127.0.0.1 9050
socks5 127.0.0.1 9050
EOF

check_success "Tor и Proxychains настроены"

# Настройка Fail2ban
echo -e "\n${YELLOW}[6/8] Настройка Fail2ban...${NC}"
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
ignoreip = 127.0.0.1/8

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

systemctl enable fail2ban
systemctl start fail2ban
check_success "Fail2ban настроен"

# Установка и настройка VPN клиентов
echo -e "\n${YELLOW}[7/8] Настройка VPN-клиентов...${NC}"

# Настройка WireGuard (если есть конфиг)
if [ -f "/root/wireguard.conf" ]; then
    cp /root/wireguard.conf /etc/wireguard/wg0.conf
    systemctl enable wg-quick@wg0
    echo -e "${GREEN}WireGuard конфигурация загружена${NC}"
fi

# Установка OpenVPN клиента
mkdir -p /etc/openvpn/client
echo -e "${YELLOW}Для настройки OpenVPN поместите конфигурацию в /etc/openvpn/client/ ${NC}"

# Настройка DNS через Tor (опционально)
echo -e "\n${YELLOW}[8/8] Настройка дополнительных мер безопасности...${NC}"

# Настройка DNS через Tor
cat >> /etc/tor/torrc << 'EOF'
DNSPort 5353
AutomapHostsOnResolve 1
AutomapHostsSuffixes .exit,.onion
EOF

systemctl restart tor

# Настройка системных параметров для усиления безопасности
cat >> /etc/sysctl.conf << 'EOF'
# Защита от IP-спуфинга
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Защита от SYN-флуда
net.ipv4.tcp_syncookies = 1

# Игнорирование ICMP-запросов
net.ipv4.icmp_echo_ignore_all = 1

# Защита от отслеживания
net.ipv4.tcp_timestamps = 0

# Отключение маршрутизации
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0
EOF

sysctl -p
check_success "Системные параметры безопасности применены"

# Создание скриптов для удобного использования
echo -e "\n${YELLOW}Создание полезных скриптов...${NC}"

# Скрипт для смены MAC-адреса
cat > /usr/local/bin/change-mac << 'EOF'
#!/bin/bash
# Скрипт для смены MAC-адреса

interface=${1:-eth0}
echo "Смена MAC-адреса для интерфейса $interface..."
ifconfig $interface down
macchanger -r $interface
ifconfig $interface up
echo "Новый MAC-адрес: $(ifconfig $interface | grep ether)"
EOF

chmod +x /usr/local/bin/change-mac

# Скрипт для безопасного серфинга через Tor
cat > /usr/local/bin/tor-browser << 'EOF'
#!/bin/bash
# Запуск браузера через Tor

if [ -z "$1" ]; then
    echo "Использование: tor-browser <URL>"
    exit 1
fi

torsocks firefox "$1"
EOF

chmod +x /usr/local/bin/tor-browser

# Скрипт для проверки безопасности
cat > /usr/local/bin/security-check << 'EOF'
#!/bin/bash
# Проверка безопасности системы

echo "=== Проверка безопасности системы ==="
echo "1. Проверка открытых портов:"
netstat -tulpn | grep LISTEN

echo -e "\n2. Проверка Fail2ban статуса:"
fail2ban-client status

echo -e "\n3. Проверка Tor статуса:"
systemctl status tor --no-pager

echo -e "\n4. Проверка UFW статуса:"
ufw status verbose

echo -e "\n5. Проверка наличия rootkit:"
rkhunter --check --skip-keypress --report-warnings-only
EOF

chmod +x /usr/local/bin/security-check

# Создание анонимного пользователя для работы
echo -e "\n${YELLOW}Создание анонимного пользователя...${NC}"
read -p "Создать отдельного пользователя для анонимной работы? (y/n): " create_user
if [[ $create_user == "y" || $create_user == "Y" ]]; then
    read -p "Введите имя пользователя: " username
    useradd -m -s /bin/bash $username
    usermod -aG sudo $username
    passwd $username
    
    # Настройка bashrc для пользователя
    cat >> /home/$username/.bashrc << 'EOF'
# Алиасы для анонимной работы
alias tor-curl='torsocks curl'
alias tor-wget='torsocks wget'
alias proxied='proxychains4'
alias security-check='sudo /usr/local/bin/security-check'
EOF
    
    echo -e "${GREEN}Пользователь $username создан${NC}"
fi

# Финальные проверки
echo -e "\n${BLUE}================================${NC}"
echo -e "${GREEN}Установка завершена!${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "\n${YELLOW}Важная информация:${NC}"
echo -e "1. SSH порт: ${GREEN}$(grep Port /etc/ssh/sshd_config | grep -v "#" | awk '{print $2}')${NC}"
echo -e "2. Tor SOCKS прокси: ${GREEN}127.0.0.1:9050${NC}"
echo -e "3. Proxychains настроен для использования с Tor"
echo -e "4. DNS через Tor доступен на порту ${GREEN}5353${NC}"

echo -e "\n${YELLOW}Полезные команды:${NC}"
echo -e "- ${GREEN}security-check${NC} - проверка безопасности системы"
echo -e "- ${GREEN}change-mac${NC} - смена MAC-адреса"
echo -e "- ${GREEN}tor-browser <URL>${NC} - открыть URL через Tor"
echo -e "- ${GREEN}torsocks curl ifconfig.me${NC} - проверить IP через Tor"
echo -e "- ${GREEN}proxychains4 curl ifconfig.me${NC} - проверить IP через proxychains"

echo -e "\n${RED}ВАЖНО:${NC}"
echo -e "1. Перезагрузите систему для применения всех настроек"
echo -e "2. Настройте VPN клиенты, если планируете их использовать"
echo -e "3. Регулярно обновляйте систему: apt update && apt upgrade"
echo -e "4. Следите за логами безопасности: /var/log/auth.log"

# Сохранение настроек
echo -e "\n${YELLOW}Сохраняем конфигурацию...${NC}"
iptables-save > /etc/iptables/rules.v4
check_success "Конфигурация сохранена"

echo -e "\n${GREEN}Готово! Рекомендуется перезагрузить систему.${NC}"