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

# Добавляем команды в файл .bashrc
echo "
alias mypy='source ~/environments/my_env/bin/activate'
alias ver='cat /etc/*-release'
alias mc='mc -S gotar'
alias hi='history | grep'
alias lsrt='ls --human-readable --size -1 -S --classify'

if [[ \$- == *i* ]]; then
    bind '\"\\e[5~\": history-search-backward'
    bind '\"\\e[6~\": history-search-forward'
fi

export HISTSIZE=10000
export HISTFILESIZE=10000
export HISTCONTROL=ignoreboth:erasedups
export PROMPT_COMMAND='history -a'
export HISTIGNORE='ls:ps:hi:pwd'
export HISTTIMEFORMAT='%d.%m.%Y %H:%M:%S: '
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
export EDITOR=mcedit

alias e=\"echo -e '\\e[8;50;150;t'\"
alias ee=\"echo -e '\\e[8;55;160;t'\"
alias eee=\"echo -e '\\e[8;60;190;t'\"\n" >> ~/.bashrc


# Установка 3proxy
# https://github.com/3proxy

# # Установка Nginx и сертификата Let's Encrypt
# sudo apt install -y nginx certbot python3-certbot-nginx
# sudo systemctl restart nginx
# sudo ufw allow 'Nginx Full'

# # Запуск сертификации через Certbot
# sudo certbot --nginx -d serpan.site

# Сообщение о завершении процесса
echo "Установка завершена! Перезагрузитесь, чтобы применить изменения."
