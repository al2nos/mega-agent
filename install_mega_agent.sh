#!/bin/bash

set -euo pipefail

USER="${SUDO_USER:-$(whoami)}"
HOME_DIR="/home/$USER"
PROJECT_DIR="$HOME_DIR/mega-agent"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
info() { log "INFO: $*"; }
warn() { log "WARN: $*"; }
error() { log "ERROR: $*" >&2; }
fatal() { log "FATAL: $*" >&2; exit 1; }

check_system() {
    info "Проверка системы..."
    [[ $EUID -eq 0 ]] && fatal "Не запускать от root!"
    info "Система готова"
}

install_dependencies() {
    info "Установка системных зависимостей..."
    sudo apt update -q
    sudo apt install -y --no-install-recommends \
        python3 python3-pip python3-venv python3-dev python3-full \
        build-essential cmake gcc \
        python3-rpi.gpio python3-spidev \
        || fatal "Критические зависимости не установлены"

    sudo apt install -y --no-install-recommends \
        ca-certificates curl wget git \
        htop nano vim jq \
        alsa-utils pulseaudio espeak-ng \
        portaudio19-dev libasound2-dev \
        libportaudio2 libportaudiocpp0 \
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
        python3-serial \
        || warn "Некоторые дополнительные зависимости не установлены"
}

setup_spi() {
    info "Настройка SPI..."
    sudo groupadd -f spi 2>/dev/null || true
    sudo groupadd -f gpio 2>/dev/null || true
    sudo groupadd -f i2c 2>/dev/null || true
    sudo usermod -a -G spi,gpio,i2c,audio,video $USER
    info "SPI настроен"
}

install_agent() {
    info "Установка мега-агента и его модулей..."
    cd "$PROJECT_DIR"
    python3 -m venv venv --system-site-packages
    source venv/bin/activate
    pip install --upgrade pip
    if [[ -f "requirements.txt" ]]; then
        info "Установка зависимостей из requirements.txt"
        pip install -r requirements.txt
    else
        warn "Файл requirements.txt не найден"
    fi
    info "Мега-агент установлен"
}

setup_services() {
    info "Настройка сервисов..."
    # Логика настройки systemd сервиса (заглушка)
}

final_setup() {
    mkdir -p "$PROJECT_DIR"/{config,logs,models,backups,modules}
    info "Финальная настройка завершена"
}

show_status() {
    echo ""
    echo "=========================================="
    echo "🚀 MEGA-AGENT УСПЕШНО УСТАНОВЛЕН"
    echo "=========================================="
    echo "✅ Установлены:"
    echo "   • Виртуальное окружение (--system-site-packages)"
    echo "   • Основные зависимости (через pip)"
    echo "   • Системные пакеты: python3-rpi.gpio, python3-spidev"
    echo "   • Каркас модулей в modules/"
    echo ""
    echo "🔧 Следующие шаги:"
    echo "   1. Разработайте логику в modules/*.py"
    echo "   2. Созд
