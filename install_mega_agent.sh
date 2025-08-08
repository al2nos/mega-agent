
#### **install_mega_agent.sh:**
```bash
#!/bin/bash

# ┌────────────────────────────────────────────────────────────────────┐
# │  MEGA AGENT INSTALLER for Orange Pi Zero 2W                        │
# │  Fixed version with proper error handling                          │
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
        python3-spidev || fatal "Зависимости не установлены"
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
    
    # Установка pip-пакетов
    pip install --upgrade pip
    pip install flask requests cryptography python-telegram-bot apscheduler pillow
    
    info "Мега-агент установлен"
}

# === ОСНОВНАЯ ФУНКЦИЯ ===
main() {
    info "Начало установки мега-агента..."
    
    mkdir -p "$PROJECT_DIR" "$MODEL_DIR" "$LOG_DIR" "$PROJECT_DIR/config" "$PROJECT_DIR/waveshare_epd"
    cd "$PROJECT_DIR"
    
    check_system
    install_dependencies
    setup_spi
    install_agent
    
    info "Установка завершена успешно!"
    info "Перезагрузите систему: sudo reboot"
}

# Запуск установки
main "$@"