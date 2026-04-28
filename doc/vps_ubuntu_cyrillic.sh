#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_cyrillic.sh && sudo chmod +x vps_ubuntu_cyrillic.sh && ./vps_ubuntu_cyrillic.sh
# bash <(wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_cyrillic.sh)

# Скрипт для установки кириллицы в Ubuntu 22.04
# Работает полностью через терминал

echo "=== Начинаем установку кириллицы ==="

# 1. Обновляем список пакетов
echo "1. Обновление списка пакетов..."
sudo apt update

# 2. Устанавливаем языковые пакеты
echo "2. Установка языковых пакетов..."
sudo apt install -y language-pack-ru

# 3. Устанавливаем русскую среду
echo "3. Установка русской среды..."
sudo apt install -y task-russian

# 4. Устанавливаем шрифты с кириллицей (на всякий случай)
echo "4. Установка шрифтов с поддержкой кириллицы..."
sudo apt install -y fonts-liberation fonts-dejavu-core

# 5. Настраиваем локали
echo "5. Настройка системных локалей..."
sudo locale-gen ru_RU.UTF-8

# 6. Устанавливаем русскую локаль по умолчанию
echo "6. Установка русской локали по умолчанию..."
sudo update-locale LANG=ru_RU.UTF-8 LC_ALL=ru_RU.UTF-8

# 7. Экспортируем переменные для текущей сессии
echo "7. Применяем настройки для текущей сессии..."
export LANG=ru_RU.UTF-8
export LC_ALL=ru_RU.UTF-8

# 8. Устанавливаем раскладку клавиатуры для текущего пользователя (GNOME)
echo "8. Настройка русской раскладки клавиатуры..."
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us'), ('xkb', 'ru')]"

# 9. Устанавливаем сочетание клавиш Win+Пробел для переключения
echo "9. Настройка переключения раскладки (Win+Пробел)..."
gsettings set org.gnome.desktop.wm.keybindings switch-input-source "['<Super>space', 'XF86Keyboard']"

# 10. [Опционально] Для консоли (TTY)
echo "10. Установка кириллицы для консоли (TTY)..."
sudo apt install -y console-cyrillic

echo ""
echo "=== Установка завершена! ==="
echo "Чтобы все изменения вступили в силу, выполните:"
echo "sudo reboot"
echo ""
echo "ИЛИ для применения без перезагрузки:"
echo "source ~/.bashrc"