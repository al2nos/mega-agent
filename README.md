# 🤖 Мега-агент для Orange Pi Zero 2W

Универсальный голосовой ассистент с искусственным интеллектом, 4-цветным e-paper дисплеем и интеграцией с Ozon и Telegram.

## 🎯 Основные возможности

- 🗣️ Голосовое взаимодействие (русский/английский)
- 🤖 Локальный ИИ (TinyLlama 1.1B)
- 📺 4-цветный e-paper дисплей (Waveshare 2.13inch B)
- 📱 Telegram-бот для удаленного управления
- 🛍️ Интеграция с Ozon API
- 🌐 Веб-интерфейс управления
- ⚡ Управление устройствами через GPIO

## 📋 Требования

- Orange Pi Zero 2W (рекомендуется 1GB RAM)
- Waveshare 2.13inch e-Paper HAT (B) - 4 цвета
- MicroSD карта (16GB+)
- USB-камера (опционально)
- Реле модуль (опционально)
- Микрофон и динамики

## 🚀 Установка

1. Склонируйте репозиторий:
   ```bash
   git clone https://github.com/ваш-логин/mega-agent.git
   cd mega-agent
2. Запустите установочный скрипт:
   chmod +x install_mega_agent.sh
   ./install_mega_agent.sh
3. Перезагрузите систему:
   sudo reboot

🌐 Доступ
Веб-интерфейс: http://ваш-ip:5000
Telegram-бот: настройка через веб-интерфейс
Ozon API: настройка через веб-интерфейс
📖 Документация
Подробная документация находится в каталоге docs/.

🤝 Вклад в проект
Форкните репозиторий
Создайте ветку для вашей функции (git checkout -b feature/AmazingFeature)
Зафиксируйте изменения (git commit -m 'Add some AmazingFeature')
Запушьте ветку (git push origin feature/AmazingFeature)
Откройте Pull Request

📄 Лицензия
Этот проект распространяется по лицензии MIT.
