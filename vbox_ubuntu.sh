#!/bin/bash
# 
# chmod +x setup.sh
# ./setup.sh

# Обновляем систему перед началом установки пакетов
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
sudo apt install -y \
    docker.io \
    docker-compose-plugin \
    git \
    net-tools \
    curl \
    mc \
    dnsutils \
    openssh-server

# Настройка Docker (разрешаем автозапуск)
sudo systemctl enable docker.service
sudo usermod -aG docker "$USER"

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

alias e=\"echo -e '\\e[8;50;150;t'\"
alias ee=\"echo -e '\\e[8;55;160;t'\"
alias eee=\"echo -e '\\e[8;60;190;t'\"\n" >> ~/.bashrc

# Настраиваем Git для доступа к вашему репозиторию на GitHub
git config --global user.name \"somepro\"
git config --global user.email \"your_email@example.com\"
git config --global credential.helper store # Хранение пароля в файле

# Информация для входа в ваш аккаунт github
echo "Введите пароль от аккаунта somepro:"
read -s password
echo "https://$password@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Перезагружаем оболочку bash, чтобы применить изменения
exec bash
