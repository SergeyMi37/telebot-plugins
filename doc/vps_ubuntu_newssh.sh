#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_newssh.sh && chmod +x vps_ubuntu_newssh.sh && ./vps_ubuntu_newssh.sh --user msw
# bash <(wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_newssh.sh)
#!/bin/bash

# ==============================================
# Скрипт безопасной настройки SSH на Ubuntu
# Автор: Claude
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
    else
        # Создаем пользователя
        print_info "Создание пользователя $TARGET_USER..."
        
        # Если передан ключ, создаем пользователя без запроса пароля
        if [[ -n "$PUBLIC_KEY" ]]; then
            sudo useradd -m -s /bin/bash "$TARGET_USER"
            print_info "Пользователь создан. Пароль не установлен (вход только по ключу)."
        else
            sudo adduser "$TARGET_USER" --gecos ""
        fi
        
        # Добавляем в группу sudo
        sudo usermod -aG sudo "$TARGET_USER"
        print_success "Пользователь $TARGET_USER создан и добавлен в группу sudo."
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
            else
                print_info "Пропускаем создание пользователя."
                read -p "Введите имя существующего пользователя для настройки: " existing_user
                if id "$existing_user" &>/dev/null; then
                    TARGET_USER="$existing_user"
                else
                    print_error "Пользователь $existing_user не существует!"
                    exit 1
                fi
            fi
        else
            # Создаем пользователя
            sudo adduser "$new_username" --gecos ""
            sudo usermod -aG sudo "$new_username"
            TARGET_USER="$new_username"
            print_success "Пользователь $TARGET_USER успешно создан."
        fi
    else
        read -p "Введите имя существующего пользователя для настройки: " existing_user
        if id "$existing_user" &>/dev/null; then
            TARGET_USER="$existing_user"
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

# Функция для добавления ключа
add_ssh_key() {
    local key="$1"
    
    sudo mkdir -p "$USER_HOME/.ssh"
    
    # Добавляем ключ (если его там еще нет)
    if [[ -f "$AUTH_KEYS_FILE" ]] && grep -q "$key" "$AUTH_KEYS_FILE"; then
        print_warning "Этот ключ уже существует в authorized_keys"
    else
        echo "$key" | sudo tee -a "$AUTH_KEYS_FILE" > /dev/null
        print_success "SSH-ключ добавлен."
    fi
    
    sudo chown -R "$TARGET_USER":"$TARGET_USER" "$USER_HOME/.ssh"
    sudo chmod 700 "$USER_HOME/.ssh"
    sudo chmod 600 "$AUTH_KEYS_FILE"
}

# Если передан ключ через параметр
if [[ -n "$PUBLIC_KEY" ]]; then
    print_info "Добавление переданного SSH-ключа..."
    add_ssh_key "$PUBLIC_KEY"
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
                    add_ssh_key "$manual_key"
                else
                    print_error "Ключ не может быть пустым!"
                    exit 1
                fi
                ;;
            2)
                if [[ -f ~/.ssh/authorized_keys ]] && [[ -s ~/.ssh/authorized_keys ]]; then
                    cat ~/.ssh/authorized_keys | while read key; do
                        if [[ -n "$key" ]]; then
                            add_ssh_key "$key"
                        fi
                    done
                elif [[ -f ~/.ssh/id_rsa.pub ]]; then
                    add_ssh_key "$(cat ~/.ssh/id_rsa.pub)"
                elif [[ -f ~/.ssh/id_ed25519.pub ]]; then
                    add_ssh_key "$(cat ~/.ssh/id_ed25519.pub)"
                else
                    print_error "Не найдены ключи текущего пользователя."
                    exit 1
                fi
                ;;
            3)
                print_info "Создание нового SSH-ключа..."
                sudo mkdir -p "$USER_HOME/.ssh"
                sudo ssh-keygen -t ed25519 -f "$USER_HOME/.ssh/id_ed25519" -N "" -C "$TARGET_USER@$(hostname)"
                sudo cp "$USER_HOME/.ssh/id_ed25519.pub" "$USER_HOME/.ssh/authorized_keys"
                sudo chown -R "$TARGET_USER":"$TARGET_USER" "$USER_HOME/.ssh"
                sudo chmod 700 "$USER_HOME/.ssh"
                sudo chmod 600 "$USER_HOME/.ssh/authorized_keys"
                sudo chmod 600 "$USER_HOME/.ssh/id_ed25519"
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

# Создаем временный файл конфигурации
TEMP_CONFIG=$(mktemp)
sudo cp "$SSHD_CONFIG" "$TEMP_CONFIG"

# Функция для безопасного обновления параметра
update_ssh_config() {
    local param="$1"
    local value="$2"
    local file="$3"
    
    # Удаляем все существующие вхождения параметра
    sudo sed -i "/^[#[:space:]]*$param/d" "$file"
    # Добавляем новый параметр
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

# Проверяем синтаксис
print_info "Проверка синтаксиса конфигурации..."
if sudo sshd -t -f "$TEMP_CONFIG" &>/dev/null; then
    print_success "Синтаксис конфигурации верный."
    sudo cp "$TEMP_CONFIG" "$SSHD_CONFIG"
else
    print_error "Ошибка в синтаксисе конфигурации!"
    sudo sshd -t -f "$TEMP_CONFIG"
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

# Перезапускаем SSH
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
# 5. ФИНАЛЬНАЯ ПРОВЕРКА
# ==============================================
echo ""
print_info "--- ШАГ 5: ФИНАЛЬНАЯ ПРОВЕРКА ---"

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
    echo "Резервная копия конфига: $BACKUP_FILE"
    echo "Для восстановления:"
    echo "  sudo cp $BACKUP_FILE $SSHD_CONFIG"
    echo "  sudo systemctl restart ssh"
} > "$INFO_FILE"

print_info "Информация сохранена в: $INFO_FILE"
echo ""

exit 0