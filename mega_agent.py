#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import logging
from modules.mesh_network import MeshNetwork
from modules.industrial_protocols import IndustrialProtocols
from modules.integrations import Integrations
from modules.monitoring import MonitoringAnalytics
from modules.business_integrations import BusinessIntegrations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_path='config/settings.json'):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Файл конфигурации {config_path} не найден!")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON в {config_path}: {e}")
        raise

def main():
    logger.info("=== ЗАПУСК MEGA-AGENT ===")
    config = load_config()

    # Создание экземпляров модулей
    mesh = MeshNetwork(config)
    industrial = IndustrialProtocols(config)
    integrations = Integrations(config)
    monitoring = MonitoringAnalytics(config)
    business = BusinessIntegrations(config)

    # Запуск модулей
    try:
        mesh.start()
        industrial.start()
        integrations.start()
        monitoring.start()
        business.start()
        logger.info("Все модули запущены.")
    except Exception as e:
        logger.error(f"Ошибка при запуске модулей: {e}")
        return

    # Основной цикл агента
    logger.info("Вход в основной цикл.")
    try:
        while True:
            # Имитация чтения данных
            temperature = industrial.read_register('modbus_tcp', 100, data_type='float32')
            if temperature is not None:
                logger.info(f"[Modbus] Температура: {temperature:.2f} °C")
                mesh.send_message('lora', 'node_sensor_hub', {'temp': temperature})
                integrations.publish_mqtt('sensors/temp', {'temp': temperature})
                monitoring.collect_data('temperature_kitchen', temperature)
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения (Ctrl+C).")
    finally:
        logger.info("Остановка модулей...")
        try: mesh.stop()
        except: pass
        try: industrial.stop()
        except: pass
        try: integrations.stop()
        except: pass
        try: monitoring.stop()
        except: pass
        try: business.stop()
        except: pass
        logger.info("=== MEGA-AGENT ОСТАНОВЛЕН ===")

if __name__ == "__main__":
    main()
