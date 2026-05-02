#!/bin/bash
# sudo wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_newssh.sh && sudo chmod +x vps_ubuntu_newssh.sh && sudo ./vps_ubuntu_newssh.sh --user msw3

# ==============================================
# Скрипт безопасной настройки SSH на Ubuntu
# Автор: Claude (исправлено для сохранения UTF-8)
# Описание: Создает sudo-пользователя, меняет порт SSH,
#           запрещает root-доступ и включает вход только по ключам
#
# Использование:
#   ./vps_ubuntu_newssh.sh [--user USERNAME] [--key "PUBLIC_KEY"]
#   
# Примеры:
#   ./vps_ubuntu_newssh.sh --user john --key "ssh-ed25519 AAAAC3... user@host"
#   ./vps_ubuntu_newssh.sh --user john  # ключ будет запрошен интерактивно
#   ./vps_ubuntu_newssh.sh               # полностью интерактивный режим
# ==============================================

set -e  # Прерывать выполнение при ошибке

# Сохраняем текущую локаль ДО любых действий
export SAVED_LANG="${LANG:-ru_RU.UTF-8}"
export SAVED_LC_ALL="${LC_ALL:-ru_RU.UTF-8}"
export SAVED_LANGUAGE="${LANGUAGE:-ru_RU:ru}"

# Цвета для красивого вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода сообщений
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция для отображения помощи
show_help() {
    echo "Использование: $0 [ОПЦИИ]"
    echo ""
    echo "Опции:"
    echo "  --user USERNAME      Имя нового пользователя для создания"
    echo "  --key PUBLIC_KEY     Публичный SSH-ключ для пользователя (в кавычках)"
    echo "  --help               Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 --user john --key \"ssh-ed25519 AAAAC3... john@local\""
    echo "  $0 --user john                    # ключ будет запрошен"
    echo "  $0                                 # полностью интерактивный режим"
    exit 0
}

# Функция безопасного создания пользователя с сохранением локали
create_user_with_locale() {
    local username="$1"
    local has_key="$2"
    
    print_info "Создание пользователя $username с сохранением UTF-8 локали..."
    
    # Создаем пользователя
    if [[ "$has_key" == "yes" ]]; then
        sudo adduser --gecos "" --disabled-password "$username"
        print_info "Пользователь создан. Пароль не установлен (вход только по ключу)."
    else
        sudo adduser --gecos "" "$username"
    fi
    
    # Добавляем в группу sudo
    sudo usermod -aG sudo "$username"
    sudo usermod -aG docker "$username"
    
    # Добавляем команды в файл .bashrc
    sudo -u "$USERNAME" bash -c "cat >> /home/$USERNAME/.bashrc << 'EOF'
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
alias eee=\"echo -e '\\e[8;60;190;t'\"
EOF"


    # Сохраняем русскую локаль для пользователя
    local user_home=$(eval echo ~$username)
    
    # Добавляем локаль в .bashrc
    sudo -u "$username" bash -c "cat >> ~/.bashrc << 'EOF'

# Настройки локали для корректного отображения кириллицы и псевдографики
export LANG=ru_RU.UTF-8
export LC_ALL=ru_RU.UTF-8
export LANGUAGE=ru_RU:ru
EOF"
    
    # Добавляем локаль в .profile для неинтерактивных сессий
    sudo -u "$username" bash -c "cat >> ~/.profile << 'EOF'

# Настройки локали для корректного отображения кириллицы и псевдографики
export LANG=ru_RU.UTF-8
export LC_ALL=ru_RU.UTF-8
export LANGUAGE=ru_RU:ru
EOF"
    
    # Явно устанавливаем локаль для пользователя через systemd (если используется)
    if command -v systemctl &> /dev/null; then
        sudo systemctl set-environment LANG=ru_RU.UTF-8 2>/dev/null || true
        sudo systemctl set-environment LC_ALL=ru_RU.UTF-8 2>/dev/null || true
    fi
    
    print_success "Пользователь $username создан с поддержкой UTF-8 и добавлен в группу sudo."
}

# Функция безопасного добавления SSH-ключа
add_ssh_key_safely() {
    local username="$1"
    local key="$2"
    local user_home=$(eval echo ~$username)
    local auth_keys="$user_home/.ssh/authorized_keys"
    
    # Создаем структуру .ssh от имени пользователя (не root!)
    sudo -u "$username" mkdir -p "$user_home/.ssh"
    
    # Добавляем ключ (если его там еще нет)
    if [[ -f "$auth_keys" ]] && grep -qF "$key" "$auth_keys"; then
        print_warning "Этот ключ уже существует в authorized_keys"
    else
        echo "$key" | sudo -u "$username" tee -a "$auth_keys" > /dev/null
        print_success "SSH-ключ добавлен."
    fi
    
    # Устанавливаем правильные права от имени пользователя
    sudo -u "$username" chmod 700 "$user_home/.ssh"
    sudo -u "$username" chmod 600 "$auth_keys"
    
    # Убеждаемся, что владелец правильный
    sudo chown -R "$username":"$username" "$user_home/.ssh"
}

# Парсинг аргументов командной строки
USERNAME=""
PUBLIC_KEY=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --user)
            USERNAME="$2"
            shift 2
            ;;
        --key)
            PUBLIC_KEY="$2"
            shift 2
            ;;
        --help)
            show_help
            ;;
        *)
            print_error "Неизвестный параметр: $1"
            show_help
            ;;
    esac
done

# Проверка, что скрипт запущен не от root
if [[ $EUID -eq 0 ]]; then
    print_error "Этот скрипт НЕ должен запускаться от root!"
    print_info "Запустите его от обычного пользователя с правами sudo."
    exit 1
fi

# Проверка наличия sudo
if ! command -v sudo &> /dev/null; then
    print_error "sudo не установлен. Установите sudo и добавьте пользователя в группу sudo."
    exit 1
fi

# Проверка, что пользователь может использовать sudo
if ! sudo -v &> /dev/null; then
    print_error "У вас нет прав sudo. Добавьте пользователя в группу sudo:"
    print_info "usermod -aG sudo $USER"
    exit 1
fi

# Приветствие
clear
echo "====================================================="
echo "     🔐 БЕЗОПАСНАЯ НАСТРОЙКА SSH НА UBUNTU 🔐"
echo "====================================================="
echo ""
print_info "Локаль сохранена: $SAVED_LANG (UTF-8 поддержка активна)"
echo ""

# Если переданы параметры, показываем их
if [[ -n "$USERNAME" ]]; then
    print_info "Режим командной строки:"
    print_info "  Пользователь: $USERNAME"
    if [[ -n "$PUBLIC_KEY" ]]; then
        print_info "  Ключ: ${PUBLIC_KEY:0:50}..." # Показываем только начало ключа
    else
        print_info "  Ключ: будет запрошен дополнительно"
    fi
    echo ""
fi

print_warning "Этот скрипт изменит критически важные настройки SSH."
print_warning "Убедитесь, что у вас есть ДРУГОЙ способ доступа к серверу (например, консоль VPS)."
print_warning "Неправильные настройки могут заблокировать вам доступ к серверу!"
echo ""

# Если параметры не переданы, спрашиваем подтверждение
if [[ -z "$USERNAME" ]]; then
    read -p "Вы уверены, что хотите продолжить? (yes/NO): " confirmation
    if [[ ! "$confirmation" =~ ^[Yy](es)?$ ]]; then
        print_info "Операция отменена."
        exit 0
    fi
else
    # Если параметры переданы, подтверждаем автоматически или спрашиваем?
    read -p "Продолжить с указанными параметрами? (YES/no): " confirmation
    if [[ "$confirmation" =~ ^[Nn]o?$ ]]; then
        print_info "Операция отменена."
        exit 0
    fi
fi

echo ""
print_info "Обновление списка пакетов..."
sudo apt update

# Проверяем и генерируем локали если нужно
print_info "Проверка поддержки UTF-8 локалей..."
if ! locale -a 2>/dev/null | grep -q "ru_RU.utf8\|ru_RU.UTF-8"; then
    print_warning "Русская локаль не найдена. Генерируем..."
    sudo locale-gen ru_RU.UTF-8 2>/dev/null || true
    sudo locale-gen en_US.UTF-8 2>/dev/null || true
fi

# ==============================================
# 0. СОЗДАНИЕ НОВОГО ПОЛЬЗОВАТЕЛЯ
# ==============================================
echo ""
print_info "--- ШАГ 0: СОЗДАНИЕ НОВОГО ПОЛЬЗОВАТЕЛЯ ---"

# Определяем имя пользователя
if [[ -n "$USERNAME" ]]; then
    # Используем переданный параметр
    TARGET_USER="$USERNAME"
    print_info "Используем пользователя: $TARGET_USER"

    # Проверяем, существует ли пользователь
    if id "$TARGET_USER" &>/dev/null; then
        print_warning "Пользователь $TARGET_USER уже существует."
        read -p "Использовать существующего пользователя? (yes/NO): " use_existing
        if [[ ! "$use_existing" =~ ^[Yy](es)?$ ]]; then
            print_error "Операция отменена."
            exit 1
        fi
        # Добавляем локаль существующему пользователю
        print_info "Добавление UTF-8 локали существующему пользователю..."
        sudo -u "$TARGET_USER" bash -c "grep -q 'LANG=ru_RU.UTF-8' ~/.bashrc || echo 'export LANG=ru_RU.UTF-8' >> ~/.bashrc"
        sudo -u "$TARGET_USER" bash -c "grep -q 'LC_ALL=ru_RU.UTF-8' ~/.bashrc || echo 'export LC_ALL=ru_RU.UTF-8' >> ~/.bashrc"
    else
        # Создаем пользователя с сохранением локали
        if [[ -n "$PUBLIC_KEY" ]]; then
            create_user_with_locale "$TARGET_USER" "yes"
        else
            create_user_with_locale "$TARGET_USER" "no"
        fi
    fi
else
    # Интерактивный режим
    read -p "Хотите создать нового пользователя с правами sudo? (yes/NO): " create_user

    if [[ "$create_user" =~ ^[Yy](es)?$ ]]; then
        read -p "Введите имя нового пользователя: " new_username

        if id "$new_username" &>/dev/null; then
            print_warning "Пользователь $new_username уже существует."
            read -p "Продолжить с существующим пользователем? (yes/NO): " continue_existing
            if [[ "$continue_existing" =~ ^[Yy](es)?$ ]]; then
                TARGET_USER="$new_username"
                # Добавляем локаль существующему пользователю
                sudo -u "$TARGET_USER" bash -c "grep -q 'LANG=ru_RU.UTF-8' ~/.bashrc || echo 'export LANG=ru_RU.UTF-8' >> ~/.bashrc"
                sudo -u "$TARGET_USER" bash -c "grep -q 'LC_ALL=ru_RU.UTF-8' ~/.bashrc || echo 'export LC_ALL=ru_RU.UTF-8' >> ~/.bashrc"
            else
                print_info "Пропускаем создание пользователя."
                read -p "Введите имя существующего пользователя для настройки: " existing_user
                if id "$existing_user" &>/dev/null; then
                    TARGET_USER="$existing_user"
                    # Добавляем локаль существующему пользователю
                    sudo -u "$TARGET_USER" bash -c "grep -q 'LANG=ru_RU.UTF-8' ~/.bashrc || echo 'export LANG=ru_RU.UTF-8' >> ~/.bashrc"
                    sudo -u "$TARGET_USER" bash -c "grep -q 'LC_ALL=ru_RU.UTF-8' ~/.bashrc || echo 'export LC_ALL=ru_RU.UTF-8' >> ~/.bashrc"
                else
                    print_error "Пользователь $existing_user не существует!"
                    exit 1
                fi
            fi
        else
            # Создаем пользователя с сохранением локали
            create_user_with_locale "$new_username" "no"
            TARGET_USER="$new_username"
        fi
    else
        read -p "Введите имя существующего пользователя для настройки: " existing_user
        if id "$existing_user" &>/dev/null; then
            TARGET_USER="$existing_user"
            # Добавляем локаль существующему пользователю
            sudo -u "$TARGET_USER" bash -c "grep -q 'LANG=ru_RU.UTF-8' ~/.bashrc || echo 'export LANG=ru_RU.UTF-8' >> ~/.bashrc"
            sudo -u "$TARGET_USER" bash -c "grep -q 'LC_ALL=ru_RU.UTF-8' ~/.bashrc || echo 'export LC_ALL=ru_RU.UTF-8' >> ~/.bashrc"
        else
            print_error "Пользователь $existing_user не существует!"
            exit 1
        fi
    fi
fi

# ==============================================
# 1. УСТАНОВКА SSH-КЛЮЧА
# ==============================================
echo ""
print_info "--- ШАГ 1: УСТАНОВКА SSH-КЛЮЧА ---"

USER_HOME=$(eval echo ~$TARGET_USER)
AUTH_KEYS_FILE="$USER_HOME/.ssh/authorized_keys"

# Если передан ключ через параметр
if [[ -n "$PUBLIC_KEY" ]]; then
    print_info "Добавление переданного SSH-ключа..."
    add_ssh_key_safely "$TARGET_USER" "$PUBLIC_KEY"
else
    # Интерактивный режим добавления ключа
    if [[ ! -f "$AUTH_KEYS_FILE" ]] || [[ ! -s "$AUTH_KEYS_FILE" ]]; then
        print_warning "У пользователя $TARGET_USER нет SSH-ключей в ~/.ssh/authorized_keys!"

        echo ""
        echo "Выберите способ добавления ключа:"
        echo "  1) Ввести публичный ключ вручную"
        echo "  2) Скопировать ключ текущего пользователя"
        echo "  3) Создать новый ключ"
        echo "  4) Пропустить (не рекомендуется)"
        read -p "Ваш выбор (1/2/3/4): " key_choice

        case $key_choice in
            1)
                echo "Вставьте ваш публичный SSH-ключ (начинается с 'ssh-rsa' или 'ssh-ed25519'):"
                read -r manual_key
                if [[ -n "$manual_key" ]]; then
                    add_ssh_key_safely "$TARGET_USER" "$manual_key"
                else
                    print_error "Ключ не может быть пустым!"
                    exit 1
                fi
                ;;
            2)
                if [[ -f ~/.ssh/authorized_keys ]] && [[ -s ~/.ssh/authorized_keys ]]; then
                    while IFS= read -r key; do
                        if [[ -n "$key" ]]; then
                            add_ssh_key_safely "$TARGET_USER" "$key"
                        fi
                    done < ~/.ssh/authorized_keys
                elif [[ -f ~/.ssh/id_rsa.pub ]]; then
                    add_ssh_key_safely "$TARGET_USER" "$(cat ~/.ssh/id_rsa.pub)"
                elif [[ -f ~/.ssh/id_ed25519.pub ]]; then
                    add_ssh_key_safely "$TARGET_USER" "$(cat ~/.ssh/id_ed25519.pub)"
                else
                    print_error "Не найдены ключи текущего пользователя."
                    exit 1
                fi
                ;;
            3)
                print_info "Создание нового SSH-ключа..."
                sudo -u "$TARGET_USER" mkdir -p "$USER_HOME/.ssh"
                sudo -u "$TARGET_USER" ssh-keygen -t ed25519 -f "$USER_HOME/.ssh/id_ed25519" -N "" -C "$TARGET_USER@$(hostname)"
                sudo -u "$TARGET_USER" cp "$USER_HOME/.ssh/id_ed25519.pub" "$USER_HOME/.ssh/authorized_keys"
                sudo -u "$TARGET_USER" chmod 700 "$USER_HOME/.ssh"
                sudo -u "$TARGET_USER" chmod 600 "$USER_HOME/.ssh/authorized_keys"
                sudo -u "$TARGET_USER" chmod 600 "$USER_HOME/.ssh/id_ed25519"
                print_success "SSH-ключ создан."
                print_warning "Приватный ключ: $USER_HOME/.ssh/id_ed25519"
                print_warning "СКОПИРУЙТЕ ЕГО СЕБЕ И УДАЛИТЕ С СЕРВЕРА!"
                echo ""
                echo "Содержимое ПРИВАТНОГО ключа (сохраните его):"
                echo "----------------------------------------"
                sudo cat "$USER_HOME/.ssh/id_ed25519"
                echo "----------------------------------------"
                ;;
            4)
                print_warning "ПРОДОЛЖЕНИЕ БЕЗ КЛЮЧА ОПАСНО! Вы рискуете потерять доступ."
                read -p "ВСЕ РАВНО ПРОДОЛЖИТЬ? (yes/NO): " dangerous_continue
                if [[ ! "$dangerous_continue" =~ ^[Yy](es)?$ ]]; then
                    print_info "Операция отменена."
                    exit 0
                fi
                ;;
            *)
                print_error "Неверный выбор."
                exit 1
                ;;
        esac
    else
        print_success "SSH-ключи для пользователя $TARGET_USER уже существуют."
    fi
fi

# ==============================================
# 2. НАСТРОЙКА SSH
# ==============================================
echo ""
print_info "--- ШАГ 2: КОНФИГУРАЦИЯ SSH ---"

# Создаем резервную копию конфига
SSHD_CONFIG="/etc/ssh/sshd_config"
BACKUP_FILE="/etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)"

print_info "Создание резервной копии $SSHD_CONFIG -> $BACKUP_FILE"
sudo cp "$SSHD_CONFIG" "$BACKUP_FILE"
print_success "Резервная копия создана."

# Запрос нового порта
echo ""
if [[ -n "$USERNAME" ]]; then
    read -p "Введите новый порт для SSH (по умолчанию 2222): " ssh_port
fi
ssh_port=${ssh_port:-2222}

# Проверка, что порт не занят
if sudo ss -tlnp 2>/dev/null | grep -q ":$ssh_port" || sudo netstat -tlnp 2>/dev/null | grep -q ":$ssh_port"; then
    print_warning "Порт $ssh_port уже используется!"
    read -p "Использовать другой порт? (введите номер): " new_port_choice
    if [[ "$new_port_choice" =~ ^[0-9]+$ ]]; then
        ssh_port=$new_port_choice
    else
        print_error "Операция отменена."
        exit 1
    fi
fi

# Создаем временный файл конфигурации через sudo
TEMP_CONFIG=$(sudo mktemp)
sudo cp "$SSHD_CONFIG" "$TEMP_CONFIG"
# Даем права на чтение текущему пользователю
sudo chmod 644 "$TEMP_CONFIG"

# Функция для безопасного обновления параметра
update_ssh_config() {
    local param="$1"
    local value="$2"
    local file="$3"

    # Удаляем все существующие вхождения параметра
    sudo sed -i "/^[#[:space:]]*$param/d" "$file"
    # Добавляем новый параметр через sudo tee
    echo "$param $value" | sudo tee -a "$file" > /dev/null
}

# Обновляем параметры
print_info "Обновление конфигурации SSH..."

# Порт
update_ssh_config "Port" "$ssh_port" "$TEMP_CONFIG"

# Запрет root
update_ssh_config "PermitRootLogin" "no" "$TEMP_CONFIG"

# Отключаем вход по паролю
update_ssh_config "PasswordAuthentication" "no" "$TEMP_CONFIG"
update_ssh_config "ChallengeResponseAuthentication" "no" "$TEMP_CONFIG"
update_ssh_config "KbdInteractiveAuthentication" "no" "$TEMP_CONFIG"
update_ssh_config "UsePAM" "no" "$TEMP_CONFIG"

# Включаем вход по ключам
update_ssh_config "PubkeyAuthentication" "yes" "$TEMP_CONFIG"

# Добавляем AcceptEnv для сохранения локали при SSH-подключениях
update_ssh_config "AcceptEnv" "LANG LC_*" "$TEMP_CONFIG"

# Ограничиваем вход конкретным пользователем (опционально)
if [[ -n "$USERNAME" ]]; then
    # Если передан параметр, спрашиваем
    read -p "Ограничить вход только пользователем $TARGET_USER? (YES/no): " restrict_user
    if [[ ! "$restrict_user" =~ ^[Nn]o?$ ]]; then
        update_ssh_config "AllowUsers" "$TARGET_USER" "$TEMP_CONFIG"
    fi
else
    # Интерактивный режим
    read -p "Ограничить вход только пользователем $TARGET_USER? (yes/NO): " restrict_user
    if [[ "$restrict_user" =~ ^[Yy](es)?$ ]]; then
        update_ssh_config "AllowUsers" "$TARGET_USER" "$TEMP_CONFIG"
    fi
fi

# Проверяем синтаксис с сохранением локали
print_info "Проверка синтаксиса конфигурации..."
if sudo sshd -t -f "$TEMP_CONFIG" &>/dev/null; then
    print_success "Синтаксис конфигурации верный."
    sudo cp "$TEMP_CONFIG" "$SSHD_CONFIG"
else
    print_error "Ошибка в синтаксисе конфигурации!"
    sudo sshd -t -f "$TEMP_CONFIG"
    sudo rm "$TEMP_CONFIG"
    exit 1
fi
sudo rm "$TEMP_CONFIG"

# ==============================================
# 3. ОТКЛЮЧЕНИЕ SSH.SOCKET
# ==============================================
echo ""
print_info "--- ШАГ 3: ОТКЛЮЧЕНИЕ SOCKET ACTIVATION ---"

if systemctl list-unit-files | grep -q ssh.socket; then
    if systemctl is-active ssh.socket &>/dev/null; then
        print_info "Обнаружен ssh.socket. Отключаем..."
        sudo systemctl disable --now ssh.socket
        print_success "ssh.socket отключен."
    else
        print_info "ssh.socket не активен, пропускаем."
    fi
fi

# Перезапускаем SSH с сохранением окружения
print_info "Перезапуск SSH-сервиса..."
sudo systemctl restart ssh

# Проверяем статус
if systemctl is-active ssh &>/dev/null; then
    print_success "SSH-сервис успешно перезапущен."
else
    print_error "SSH-сервис не запустился!"
    print_info "Восстанавливаем резервную копию..."
    sudo cp "$BACKUP_FILE" "$SSHD_CONFIG"
    sudo systemctl restart ssh
    exit 1
fi

# ==============================================
# 4. НАСТРОЙКА UFW
# ==============================================
echo ""
print_info "--- ШАГ 4: НАСТРОЙКА UFW ---"

if command -v ufw &>/dev/null; then
    if sudo ufw status | grep -q "Status: active"; then
        print_info "UFW активен. Настраиваем правила..."

        # Разрешаем новый порт
        sudo ufw allow "$ssh_port"/tcp comment 'SSH custom port'
        print_success "Порт $ssh_port разрешен."

        # Закрываем старый порт 22
        if sudo ufw status | grep -q "22/tcp"; then
            sudo ufw delete allow 22/tcp
            print_info "Старый порт 22 закрыт."
        fi

        # Перезагружаем UFW
        sudo ufw reload
        print_success "Правила UFW обновлены."
    else
        print_info "UFW не активен. Пропускаем настройку."
    fi
fi

# ==============================================
# 5. НАСТРОЙКА ЛОКАЛИ ДЛЯ SSH-СЕССИЙ
# ==============================================
echo ""
print_info "--- ШАГ 5: СОХРАНЕНИЕ ЛОКАЛИ ДЛЯ SSH ---"

# Убеждаемся что локаль глобально сконфигурирована
if [[ -f /etc/default/locale ]]; then
    sudo sed -i 's/^LANG=.*/LANG=ru_RU.UTF-8/' /etc/default/locale
    sudo sed -i 's/^LC_ALL=.*/LC_ALL=ru_RU.UTF-8/' /etc/default/locale
else
    echo "LANG=ru_RU.UTF-8" | sudo tee /etc/default/locale > /dev/null
    echo "LC_ALL=ru_RU.UTF-8" | sudo tee -a /etc/default/locale > /dev/null
fi

# Добавляем в /etc/environment если нужно
if ! grep -q "LANG=ru_RU.UTF-8" /etc/environment 2>/dev/null; then
    echo "LANG=ru_RU.UTF-8" | sudo tee -a /etc/environment > /dev/null
fi

print_success "Локаль настроена глобально."

# ==============================================
# 6. ФИНАЛЬНАЯ ПРОВЕРКА
# ==============================================
echo ""
print_info "--- ШАГ 6: ФИНАЛЬНАЯ ПРОВЕРКА ---"

# Получаем IP сервера
SERVER_IP=$(ip -4 route get 1 | awk '{print $NF;exit}' 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
print_success "✅ НАСТРОЙКА ЗАВЕРШЕНА!"
echo ""
print_info "НОВАЯ КОНФИГУРАЦИЯ SSH:"
echo "  • Порт: $ssh_port"
echo "  • Root доступ: ЗАПРЕЩЕН"
echo "  • Вход по паролю: ЗАПРЕЩЕН"
echo "  • Вход по ключам: РАЗРЕШЕН (для пользователя $TARGET_USER)"
echo "  • UTF-8 локаль: СОХРАНЕНА (ru_RU.UTF-8)"
if grep -q "^AllowUsers.*$TARGET_USER" "$SSHD_CONFIG"; then
    echo "  • Ограничение: Только пользователь $TARGET_USER"
fi
echo ""
print_warning "⚠️  ВАЖНЫЕ ИНСТРУКЦИИ:"
print_warning "1. НЕ ЗАКРЫВАЙТЕ ЭТУ СЕССИЮ до проверки!"
print_warning "2. Откройте НОВЫЙ терминал и проверьте подключение:"
echo ""
echo "   ssh -p $ssh_port $TARGET_USER@$SERVER_IP"
echo ""
print_warning "3. Если используете публичный ключ из параметра --key, убедитесь, что у вас есть соответствующий приватный ключ."
print_warning "4. ТОЛЬКО после успешного подключения в НОВОМ окне можно закрыть эту сессию."
print_warning "5. При подключении проверьте локаль командой: locale"
echo ""

# Сохраняем информацию
INFO_FILE="$HOME/ssh_setup_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "SSH НАСТРОЙКИ ОТ $(date)"
    echo "=========================="
    echo "Сервер: $SERVER_IP"
    echo "Пользователь: $TARGET_USER"
    echo "Порт: $ssh_port"
    echo "Команда подключения: ssh -p $ssh_port $TARGET_USER@$SERVER_IP"
    echo ""
    echo "UTF-8 локаль: СОХРАНЕНА"
    echo "Резервная копия конфига: $BACKUP_FILE"
    echo "Для восстановления:"
    echo "  sudo cp $BACKUP_FILE $SSHD_CONFIG"
    echo "  sudo systemctl restart ssh"
} > "$INFO_FILE"

print_info "Информация сохранена в: $INFO_FILE"
echo ""

exit 0