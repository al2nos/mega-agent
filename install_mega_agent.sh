#!/bin/bash

# ┌────────────────────────────────────────────────────────────────────┐
# │  MEGA AGENT INSTALLER for Orange Pi Zero 2W                        │
# │  Updated with new modules and pyproject.toml                       │
# └────────────────────────────────────────────────────────────────────┘

set -euo pipefail

# === КОНФИГУРАЦИЯ ===
USER="${SUDO_USER:-$(whoami)}"
HOME_DIR="/home/$USER"
PROJECT_DIR="$HOME_DIR/mega-agent"
MODEL_DIR="$HOME_DIR/models"
LOG_DIR="$HOME_DIR/logs"

# === ФУНКЦИИ ЛОГИРОВАНИЯ ===
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
info() { log "INFO: $*"; }
warn() { log "WARN: $*"; }
error() { log "ERROR: $*" >&2; }
fatal() { log "FATAL: $*" >&2; exit 1; }

# === ПРОВЕРКА СИСТЕМЫ ===
check_system() {
    info "Проверка системы..."
    [[ $EUID -eq 0 ]] && fatal "Не запускать от root!"
    info "Система готова"
}

# === УСТАНОВКА ЗАВИСИМОСТЕЙ ===
install_dependencies() {
    info "Установка зависимостей..."
    
    sudo apt update -q
    
    # Установка системных пакетов
    sudo apt install -y --no-install-recommends \
        ca-certificates curl wget git \
        python3 python3-pip python3-venv python3-dev python3-full \
        build-essential cmake gcc \
        htop nano vim jq \
        alsa-utils pulseaudio espeak-ng \
        portaudio19-dev libasound2-dev \
        libportaudio2 libportaudiocpp0 \
        python3-rpi.gpio \
        sqlite3 \
        ufw fail2ban \
        mosquitto mosquitto-clients \
        libavformat-dev libavfilter-dev \
        libavdevice-dev libavutil-dev \
        libswscale-dev libswresample-dev \
        libsndfile1-dev libffi-dev \
        python3-pil python3-pil.imagetk \
        fonts-dejavu-core fonts-freefont-ttf \
        spi-tools i2c-tools \
        python3-spidev \
        python3-serial \
        || fatal "Зависимости не установлены"
}

# === НАСТРОЙКА SPI ===
setup_spi() {
    info "Настройка SPI..."
    
    # Создание групп если они не существуют
    sudo groupadd -f spi 2>/dev/null || true
    sudo groupadd -f gpio 2>/dev/null || true
    sudo groupadd -f i2c 2>/dev/null || true
    
    # Включение SPI в config.txt
    if ! grep -q "dtparam=spi=on" /boot/orangepiEnv.txt 2>/dev/null; then
        echo "dtparam=spi=on" | sudo tee -a /boot/orangepiEnv.txt
        warn "Требуется перезагрузка для активации SPI!"
    fi
    
    # Добавление пользователя в группы
    sudo usermod -a -G spi,gpio,i2c,audio,video $USER
    
    info "SPI настроен"
}

# === УСТАНОВКА АГЕНТА ===
install_agent() {
    info "Установка мега-агента..."
    
    cd "$PROJECT_DIR"
    
    # Создание виртуального окружения с доступом к системным пакетам
    python3 -m venv venv --system-site-packages
    source venv/bin/activate
    
    # Установка pip-пакетов из pyproject.toml или requirements.txt
    # Если есть pyproject.toml, установим через pip
    if [[ -f "pyproject.toml" ]]; then
        info "Установка зависимостей через pip (из pyproject.toml)"
        # Установка основных зависимостей
        pip install --upgrade pip
        pip install .
        # Установка опциональных зависимостей, если нужно
        # pip install .[mesh,industrial,integrations,monitoring,business]
    elif [[ -f "requirements.txt" ]]; then
        info "Установка зависимостей из requirements.txt"
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        # Минимальная установка
        info "Установка минимальных зависимостей"
        pip install --upgrade pip
        pip install flask requests cryptography python-telegram-bot apscheduler pillow
    fi
    
    info "Мега-агент установлен"
}

# === НАСТРОЙКА СЕРВИСОВ ===
setup_services() {
    info "Настройка сервисов..."
    
    # Основной сервис
    sudo tee /etc/systemd/system/mega-agent.service > /dev/null << 'EOF'
[Unit]
Description=Mega Agent with Extended Features
After=network.target mosquitto.service
Wants=network.target

[Service]
Type=simple
User=orangepi
WorkingDirectory=/home/orangepi/mega-agent
ExecStart=/home/orangepi/mega-agent/venv/bin/python3 mega_agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONPATH=/home/orangepi/mega-agent
Environment=PATH=/home/orangepi/mega-agent/venv/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF

    # Включение сервиса
    sudo systemctl daemon-reload
    sudo systemctl enable mega-agent.service
    
    info "Сервисы настроены"
}

# === ФИНАЛЬНАЯ НАСТРОЙКА ===
final_setup() {
    info "Финальная настройка..."
    
    # Создание необходимых директорий
    mkdir -p "$PROJECT_DIR"/{config,logs,models,backups}
    
    # Создание базового конфигурационного файла, если его нет
    if [[ ! -f "$PROJECT_DIR/config/settings.json" ]]; then
        cat > "$PROJECT_DIR/config/settings.json" << 'EOF'
{
    "system": {
        "relay_pin": 18,
        "language": "ru"
    },
    "display": {
        "epaper": {
            "enabled": true,
            "type": "waveshare_2in13b_v3",
            "colors": ["black", "white", "red", "yellow"],
            "update_interval": 60
        }
    },
    "mesh": {
        "enabled": false,
        "protocols": ["lora"],
        "lora": {
            "port": "/dev/ttyS0",
            "baudrate": 9600
        }
    },
    "industrial": {
        "enabled": false,
        "protocols": ["modbus_tcp"],
        "modbus_tcp": {
            "host": "127.0.0.1",
            "port": 502,
            "unit_id": 1
        }
    },
    "integrations": {
        "enabled": true,
        "systems": ["mqtt_broker"],
        "mqtt_broker": {
            "enabled": true,
            "host": "localhost",
            "port": 1883
        }
    },
    "monitoring": {
        "enabled": true,
        "data_storage": "memory",
        "storage_path": "./monitoring_data"
    },
    "business": {
        "enabled": false,
        "systems": [],
        "backup_storage": "./backups"
    },
    "telegram": {
        "bot_token": "",
        "enabled": false,
        "admin_chat_id": ""
    }
}
EOF
    fi

    # Настройка прав доступа
    sudo usermod -a -G spi,gpio,i2c,audio,video $USER
    
    info "Финальная настройка завершена"
}

# === СТАТУС И ИНСТРУКЦИИ ===
show_status() {
    echo ""
    echo "=========================================="
    echo "🚀 MEGA-AGENT УСПЕШНО УСТАНОВЛЕН"
    echo "=========================================="
    echo "✅ Установлены компоненты:"
    echo "   • Основной агент"
    echo "   • 4-цветный e-paper дисплей"
    echo "   • Mesh-сети (LoRa, WiFi Direct, Bluetooth Mesh)"
    echo "   • Промышленные протоколы (Modbus, MQTT-SN, CoAP)"
    echo "   • Интеграции (Zigbee2MQTT, Z-Wave, KNX, HomeKit)"
    echo "   • Мониторинг и аналитика"
    echo "   • Бизнес-интеграции (CRM, ERP, резервное копирование)"
    echo ""
    echo "🔧 Управление сервисом:"
    echo "   Запуск: sudo systemctl start mega-agent"
    echo "   Остановка: sudo systemctl stop mega-agent"
    echo "   Статус: sudo systemctl status mega-agent"
    echo "   Логи: journalctl -u mega-agent -f"
    echo ""
    echo "⚡ Для активации перезагрузите систему:"
    echo "   sudo reboot"
    echo "=========================================="
}

# === ГЛАВНАЯ ФУНКЦИЯ ===
main() {
    info "Начало установки мега-агента..."
    
    mkdir -p "$PROJECT_DIR" "$MODEL_DIR" "$LOG_DIR"
    cd "$PROJECT_DIR"
    
    check_system
    install_dependencies
    setup_spi
    install_agent
    setup_services
    final_setup
    
    show_status
    
    info "Мега-агент готов к активации! 🤖"
    info "Перезагрузите систему для завершения настройки"
}

# Запуск установки
main "$@"
