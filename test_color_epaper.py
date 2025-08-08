#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест 4-цветного e-paper дисплея Waveshare 2.13inch B
"""

try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'waveshare_epd'))
    
    # Попробуем импортировать напрямую
    from waveshare_epd.epd2in13b_v3 import EPD
    
    print("🔍 Запуск теста 4-color e-paper дисплея...")
    
    # Создание экземпляра дисплея
    epd = EPD()
    
    # Инициализация
    if epd.module_init() == 0:
        print("✅ Дисплей инициализирован")
        
        # Очистка дисплея
        epd.Clear()
        print("🧹 Дисплей очищен")
        
        # Тест - просто засыпаем
        epd.sleep()
        print("😴 Дисплей переведен в режим сна")
        
        epd.module_exit()
        print("✅ Тест 4-color e-paper дисплея завершен успешно!")
    else:
        print("❌ Ошибка инициализации дисплея")
        
except ImportError as e:
    print(f"❌ Драйвер 4-color e-paper не найден: {e}")
    print("Убедитесь, что драйвер установлен корректно")
except Exception as e:
    print(f"❌ Ошибка теста 4-color e-paper: {e}")
    print("Проверьте подключение дисплея к SPI")

if __name__ == "__main__":
    print("🎨 Waveshare 4-Color e-Paper 2.13inch B Test")
    print("=============================================")