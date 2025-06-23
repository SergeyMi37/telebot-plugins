#!/bin/bash
#  wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu.sh
# chmod +x vps_ubuntu.sh
# ./vps_ubuntu.sh
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    net-tools \
    mc

# Установка Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Добавление текущего пользователя в группу docker
sudo usermod -aG docker "$USER"

# Установка Docker Compose
DOCKER_COMPOSE_VERSION="$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d '"' -f 4)"
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Установка 3proxy
wget http://3proxy.ru/3proxy-latest.tgz
tar xzf 3proxy-latest.tgz
cd 3proxy*
make -f Makefile.Linux
sudo cp src/3proxy /usr/local/bin/
sudo mkdir /var/log/3proxy
sudo touch /var/log/3proxy/3proxy.log
sudo chown root:root /var/log/3proxy/3proxy.log
sudo chmod 755 /var/log/3proxy/3proxy.log
cat << EOF > /etc/systemd/system/3proxy.service
[Unit]
Description=3Proxy Service
After=network.target

[Service]
Type=simple
User=nobody
Group=nogroup
ExecStart=/usr/local/bin/3proxy /etc/3proxy.cfg
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable 3proxy
systemctl start 3proxy

# Настройка конфигурации 3proxy
mkdir -p /etc
touch /etc/3proxy.cfg
chmod 600 /etc/3proxy.cfg
chown nobody:nogroup /etc/3proxy.cfg
cat << EOF >> /etc/3proxy.cfg
nscache 65536
auth strong
users ${USER}:CL:${PASSWORD}
allow *:*:${IP}
proxy -n -a -u
flush
log /var/log/3proxy/3proxy.log D
rotate W6
daemon
pidfile /var/run/3proxy.pid
EOF

# Установка Nginx и сертификата Let's Encrypt
sudo apt install -y nginx certbot python3-certbot-nginx
sudo systemctl restart nginx
sudo ufw allow 'Nginx Full'

# Запуск сертификации через Certbot
sudo certbot --nginx -d serpan.site

# Сообщение о завершении процесса
echo "Установка завершена! Перезагрузитесь, чтобы применить изменения."
