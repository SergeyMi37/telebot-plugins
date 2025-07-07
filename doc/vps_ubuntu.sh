#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu.sh && chmod +x vps_ubuntu.sh && ./vps_ubuntu.sh
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git net-tools make mc

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
alias myip='wget -qO myip http://www.ipchicken.com/; grep -o "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" myip;  rm myip'
alias ver='cat /etc/*-release'
alias mc='mc -S gotar'
alias hi='history | grep'
alias lsrt='ls --human-readable --size -1 -S --classify'

# если интерактивный режим, то при введении начало команды из истории можно листать PgUp/PgDn
# https://qastack.ru/programming/4200800/in-bash-how-do-i-bind-a-function-key-to-a-command
# возможность по клавишам PgUp, PgDn переходить по командам истории находясь на контексте строки
if [[ \$- == *i* ]]; then
    bind '\"\\e[5~\": history-search-backward'
    bind '\"\\e[6~\": history-search-forward'
fi

# Настройки прокси сервера
# export http_proxy=http://proxyuser:pass@111.114.222.114:4999
# export https_proxy=${http_proxy}
# export ftp_proxy=${http_proxy}


# настройки истории
export HISTSIZE=10000
export HISTFILESIZE=10000
export HISTCONTROL=ignoreboth:erasedups
export PROMPT_COMMAND='history -a'
export HISTIGNORE='ls:ps:hi:pwd'
export HISTTIMEFORMAT='%d.%m.%Y %H:%M:%S: '

export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
export EDITOR=mcedit

alias dockersrm='docker stop $(docker ps -a -q) && docker rm $(docker ps -a -q) -f && docker system prune -f'
alias dockersrmi='docker rmi $(docker images -q) -f && docker system prune -f'
alias dcserv='docker compose ps --services'

alias e=\"echo -e '\\e[8;50;150;t'\"
alias ee=\"echo -e '\\e[8;55;160;t'\"
alias eee=\"echo -e '\\e[8;60;190;t'\"\n" >> ~/.bashrc

# # Переменная с командами, которые хотим добавить в историю
# echo 'docker compose up --build -d' >> ~/.bash_history
# history -s docker\\ ps

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
