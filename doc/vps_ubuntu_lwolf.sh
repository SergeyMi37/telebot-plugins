#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_lwolf.sh && sudo chmod +x vps_ubuntu_lwolf.sh && ./vps_ubuntu_lwolf.sh
# bash <(wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_lwolf.sh)

# Скрипт установки LibreWolf на Ubuntu 22.04
# Автоматически определяет лучший способ установки

set -e  # Прерывать выполнение при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   Установщик LibreWolf для Ubuntu 22.04${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Проверка прав
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        print_error "Не запускайте скрипт от имени root!"
        print_error "Запустите обычного пользователя с правами sudo"
        exit 1
    fi
    
    if ! sudo -n true 2>/dev/null; then
        print_error "Требуются права sudo. Запустите скрипт с пользователем, имеющим sudo доступ"
        exit 1
    fi
}

# Проверка наличия команды
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Установка через apt (extrepo)
install_via_apt() {
    print_message "Установка LibreWolf через официальный репозиторий (.deb)..."
    
    # Установка extrepo
    print_message "Установка extrepo..."
    sudo apt update
    sudo apt install -y extrepo
    
    # Включение репозитория LibreWolf
    print_message "Добавление репозитория LibreWolf..."
    sudo extrepo enable librewolf
    
    # Обновление списка пакетов
    print_message "Обновление списка пакетов..."
    sudo apt update
    
    # Установка LibreWolf
    print_message "Установка LibreWolf..."
    sudo apt install -y librewolf
    
    print_message "LibreWolf успешно установлен через apt!"
    return 0
}

# Установка через Flatpak
install_via_flatpak() {
    print_message "Установка LibreWolf через Flatpak..."
    
    # Установка Flatpak если не установлен
    if ! command_exists flatpak; then
        print_message "Установка Flatpak..."
        sudo apt update
        sudo apt install -y flatpak
    fi
    
    # Добавление репозитория Flathub если его нет
    if ! flatpak remote-list | grep -q flathub; then
        print_message "Добавление репозитория Flathub..."
        flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    fi
    
    # Установка LibreWolf
    print_message "Установка LibreWolf из Flathub..."
    flatpak install -y flathub io.gitlab.librewolf-community
    
    # Создание символической ссылки для запуска из терминала
    print_message "Создание символической ссылки..."
    sudo ln -sf /var/lib/flatpak/exports/bin/io.gitlab.librewolf-community /usr/local/bin/librewolf 2>/dev/null || true
    
    print_message "LibreWolf успешно установлен через Flatpak!"
    return 0
}

# Установка через snap (альтернативный вариант)
install_via_snap() {
    print_message "Установка LibreWolf через Snap..."
    
    if ! command_exists snap; then
        print_message "Установка Snap..."
        sudo apt update
        sudo apt install -y snapd
    fi
    
    print_message "Установка LibreWolf из Snap Store..."
    sudo snap install librewolf
    
    print_message "LibreWolf успешно установлен через Snap!"
    return 0
}

# Основное меню выбора
show_menu() {
    echo ""
    echo "Выберите способ установки:"
    echo "1) Установка через официальный репозиторий (.deb) - РЕКОМЕНДУЕТСЯ"
    echo "2) Установка через Flatpak"
    echo "3) Установка через Snap"
    echo "4) Автоматический выбор (попробует .deb, затем Flatpak)"
    echo "5) Выход"
    echo ""
    read -p "Ваш выбор [1-5]: " choice
    
    case $choice in
        1)
            install_via_apt
            ;;
        2)
            install_via_flatpak
            ;;
        3)
            install_via_snap
            ;;
        4)
            auto_install
            ;;
        5)
            print_message "Выход из установки."
            exit 0
            ;;
        *)
            print_error "Неверный выбор. Попробуйте снова."
            show_menu
            ;;
    esac
}

# Автоматическая установка
auto_install() {
    print_message "Автоматический выбор способа установки..."
    
    # Сначала пробуем apt
    if install_via_apt; then
        print_message "Установка завершена через apt!"
        return 0
    else
        print_warning "Установка через apt не удалась, пробуем Flatpak..."
        if install_via_flatpak; then
            print_message "Установка завершена через Flatpak!"
            return 0
        else
            print_error "Не удалось установить LibreWolf ни одним способом!"
            return 1
        fi
    fi
}

# Проверка успешности установки
verify_installation() {
    echo ""
    print_message "Проверка установки..."
    
    if command_exists librewolf; then
        print_message "LibreWolf установлен и доступен в системе!"
        print_message "Версия: $(librewolf --version 2>/dev/null || echo 'не определена')"
    elif flatpak list | grep -q io.gitlab.librewolf-community; then
        print_message "LibreWolf (Flatpak) установлен!"
    else
        print_warning "Не удалось проверить установку. Попробуйте запустить LibreWolf вручную."
    fi
}

# Показ информации после установки
show_post_install_info() {
    echo ""
    print_header
    echo ""
    print_message "LibreWolf успешно установлен!"
    echo ""
    echo "Запустить браузер можно:"
    echo "  • Из меню приложений (иконка LibreWolf)"
    echo "  • Из терминала командой: librewolf"
    echo "  • Если установлен через Flatpak: flatpak run io.gitlab.librewolf-community"
    echo ""
    echo "Обновление LibreWolf:"
    echo "  • Для .deb версии: sudo apt update && sudo apt upgrade"
    echo "  • Для Flatpak версии: flatpak update"
    echo "  • Для Snap версии: sudo snap refresh librewolf"
    echo ""
    echo "Удаление LibreWolf:"
    echo "  • Для .deb версии: sudo apt remove librewolf && sudo extrepo disable librewolf"
    echo "  • Для Flatpak версии: flatpak uninstall io.gitlab.librewolf-community"
    echo "  • Для Snap версии: sudo snap remove librewolf"
    echo ""
    print_message "Наслаждайтесь приватным браузингом с LibreWolf! 🐺"
}

# Основная функция
main() {
    clear
    print_header
    
    # Проверка ОС
    if ! grep -q "Ubuntu 22" /etc/os-release 2>/dev/null; then
        print_warning "Скрипт разработан для Ubuntu 22.04, но может работать и на других версиях."
        echo "Ваша версия: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
    
    check_permissions
    
    # Обновление системы
    print_message "Обновление списка пакетов..."
    sudo apt update
    
    show_menu
    verify_installation
    show_post_install_info
}

# Запуск скрипта
main