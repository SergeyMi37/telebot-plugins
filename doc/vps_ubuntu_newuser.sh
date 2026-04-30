#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_newuser.sh && sudo chmod +x vps_ubuntu_newuser.sh && ./vps_ubuntu_newuser.sh -u msw -p P@S5w0rd

# Минималистичный скрипт для создания пользователя с sudo
# Поддерживает интерактивный и CLI режимы

# Функция вывода помощи
show_help() {
    cat << EOF
Использование: $0 [ОПЦИИ]

Опции:
  -u, --username USERNAME    Имя пользователя
  -p, --password PASSWORD    Пароль пользователя
  -s, --ssh-key KEY          Публичный SSH ключ (опционально)
  -h, --help                 Показать эту помощь
  -q, --quiet                Тихий режим (без вывода)

Примеры:
  # Интерактивный режим
  $0

  # CLI режим с паролем
  $0 -u john -p mypassword

  # CLI режим с генерацией случайного пароля
  $0 -u john

  # CLI режим с SSH ключом
  $0 -u john -p pass123 -s "ssh-rsa AAAAB3..."

EOF
}

# Функция генерации случайного пароля
generate_password() {
    openssl rand -base64 12
}

# Инициализация переменных
USERNAME=""
PASSWORD=""
SSH_KEY=""
QUIET=false

# Парсинг аргументов командной строки
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--username)
            USERNAME="$2"
            shift 2
            ;;
        -p|--password)
            PASSWORD="$2"
            shift 2
            ;;
        -s|--ssh-key)
            SSH_KEY="$2"
            shift 2
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Неизвестная опция: $1"
            show_help
            exit 1
            ;;
    esac
done

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
    echo "Ошибка: Запустите с sudo" >&2
    exit 1
fi

# Интерактивный режим, если не указано имя пользователя
if [[ -z "$USERNAME" ]]; then
    read -p "Имя пользователя: " USERNAME
fi

# Проверка существования пользователя
if id "$USERNAME" &>/dev/null; then
    echo "Ошибка: Пользователь '$USERNAME' уже существует" >&2
    exit 1
fi

# Генерация или запрос пароля
if [[ -z "$PASSWORD" ]]; then
    if [[ -t 0 ]]; then
        # Интерактивный ввод пароля
        read -s -p "Пароль (оставьте пустым для генерации): " PASSWORD
        echo
        if [[ -z "$PASSWORD" ]]; then
            PASSWORD=$(generate_password)
            GENERATED_PASS=true
        else
            read -s -p "Повторите пароль: " PASSWORD_CONFIRM
            echo
            if [[ "$PASSWORD" != "$PASSWORD_CONFIRM" ]]; then
                echo "Ошибка: Пароли не совпадают" >&2
                exit 1
            fi
        fi
    else
        # Неинтерактивный режим - генерируем пароль
        PASSWORD=$(generate_password)
        GENERATED_PASS=true
    fi
fi

# Создание пользователя
useradd -m -s /bin/bash "$USERNAME" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo "Ошибка: Не удалось создать пользователя" >&2
    exit 1
fi

# Установка пароля
echo "$USERNAME:$PASSWORD" | chpasswd

# Добавление в группу sudo
usermod -aG sudo "$USERNAME"
usermod -aG docker "$USERNAME"

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
alias eee=\"echo -e '\\e[8;60;190;t'\"\n" >> /home/$USERNAME/.bashrc

# Настройка SSH ключа если указан
if [[ -n "$SSH_KEY" ]]; then
    mkdir -p "/home/$USERNAME/.ssh"
    echo "$SSH_KEY" >> "/home/$USERNAME/.ssh/authorized_keys"
    chmod 700 "/home/$USERNAME/.ssh"
    chmod 600 "/home/$USERNAME/.ssh/authorized_keys"
    chown -R "$USERNAME:$USERNAME" "/home/$USERNAME/.ssh"
    SSH_ADDED=true
fi

# Вывод результатов
if [[ "$QUIET" == false ]]; then
    echo "========================================"
    echo "✓ Пользователь '$USERNAME' создан"
    echo "✓ Добавлен в группу sudo"
    echo "✓ Домашняя директория: /home/$USERNAME"
    
    if [[ "$GENERATED_PASS" == true ]]; then
        echo ""
        echo "⚠️  Сгенерированный пароль: $PASSWORD"
        echo "   Сохраните его в надежном месте!"
    fi
    
    if [[ "$SSH_ADDED" == true ]]; then
        echo "✓ SSH ключ добавлен"
    fi
    
    echo "========================================"
    
    # Проверка
    if groups "$USERNAME" | grep -q sudo; then
        echo "✓ Права sudo подтверждены"
    fi
fi

# Вывод только пароля для неинтерактивного использования
if [[ "$QUIET" == true && "$GENERATED_PASS" == true ]]; then
    echo "$PASSWORD"
fi

exit 0