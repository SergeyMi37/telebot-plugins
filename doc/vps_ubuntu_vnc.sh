#!/bin/bash
# wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_vnc.sh && sudo chmod +x vps_ubuntu_vnc.sh && ./vps_ubuntu_vnc.sh
# bash <(wget https://raw.githubusercontent.com/SergeyMi37/telebot-plugins/master/doc/vps_ubuntu_vnc.sh)

# Минимальная установка VNC
sudo apt update
sudo apt install -y tigervnc-standalone-server tigervnc-common xfce4 xfce4-goodies

# Настройка пароля
vncpasswd

# Создание конфигурации
mkdir -p ~/.vnc
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec startxfce4
EOF

chmod +x ~/.vnc/xstartup

# Запуск сервера
vncserver -kill :1 2>/dev/null
vncserver :1 -geometry 1366x768 -depth 24 -localhost

echo "VNC установлен! Порт: 5901"
echo "Подключение: ssh -L 5901:localhost:5901 -N пользователь@IP_сервера"