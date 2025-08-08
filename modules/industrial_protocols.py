#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с промышленными протоколами
"""

import logging
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import time
# import asyncio # Для асинхронных клиентов MQTT-SN, CoAP

logger = logging.getLogger(__name__)

class IndustrialProtocols:
    def __init__(self, config):
        self.config = config.get('industrial', {})
        self.enabled = self.config.get('enabled', False)
        self.protocols = self.config.get('protocols', [])
        self.connections = {}
        self.data_cache = {}

    def start(self):
        """Инициализация подключений к промышленным протоколам"""
        if not self.enabled:
            logger.info("Поддержка промышленных протоколов отключена")
            return

        logger.info("Инициализация промышленных протоколов")

        for protocol in self.protocols:
            try:
                if protocol == 'modbus_tcp':
                    self._connect_modbus_tcp()
                elif protocol == 'modbus_rtu':
                    self._connect_modbus_rtu()
                elif protocol == 'mqtt_sn':
                    self._setup_mqtt_sn()
                elif protocol == 'coap':
                    self._setup_coap()
            except Exception as e:
                logger.error(f"Ошибка инициализации протокола {protocol}: {e}")

    def stop(self):
        """Закрытие подключений"""
        logger.info("Закрытие подключений промышленных протоколов")
        for name, conn in self.connections.items():
            if hasattr(conn, 'close'):
                try:
                    conn.close()
                    logger.debug(f"Закрыто соединение {name}")
                except Exception as e:
                    logger.error(f"Ошибка закрытия {name}: {e}")

    def _connect_modbus_tcp(self):
        """Подключение к Modbus TCP устройству"""
        modbus_config = self.config.get('modbus_tcp', {})
        host = modbus_config.get('host', '127.0.0.1')
        port = modbus_config.get('port', 502)
        unit_id = modbus_config.get('unit_id', 1)

        try:
            client = ModbusTcpClient(host, port)
            # Проверка соединения
            # client.connect() не всегда требуется, соединение открывается при запросе
            # Но можно выполнить тестовый запрос
            # result = client.read_holding_registers(0, 1, slave=unit_id)
            # if not result.isError():
            self.connections['modbus_tcp'] = {
                'client': client,
                'unit_id': unit_id
            }
            logger.info(f"Modbus TCP клиент подключен к {host}:{port}")
            # else:
            #     logger.error(f"Ошибка тестового запроса Modbus TCP: {result}")
        except Exception as e:
            logger.error(f"Ошибка подключения Modbus TCP: {e}")

    def _connect_modbus_rtu(self):
        """Подключение к Modbus RTU устройству"""
        modbus_config = self.config.get('modbus_rtu', {})
        port = modbus_config.get('port', '/dev/ttyUSB0')
        baudrate = modbus_config.get('baudrate', 9600)
        parity = modbus_config.get('parity', 'N')
        stopbits = modbus_config.get('stopbits', 1)
        unit_id = modbus_config.get('unit_id', 1)

        try:
            client = ModbusSerialClient(
                port=port,
                baudrate=baudrate,
                parity=parity,
                stopbits=stopbits,
                # bytesize=8,
                # timeout=3
            )
            self.connections['modbus_rtu'] = {
                'client': client,
                'unit_id': unit_id
            }
            logger.info(f"Modbus RTU клиент настроен на {port}")
        except Exception as e:
            logger.error(f"Ошибка настройки Modbus RTU: {e}")

    def _setup_mqtt_sn(self):
        """Настройка MQTT-SN (заглушка)"""
        logger.info("MQTT-SN настройка (заглушка)")
        # Реализация с использованием библиотек типа paho-mqtt с расширениями для MQTT-SN
        # или специализированных библиотек

    def _setup_coap(self):
        """Настройка CoAP (заглушка)"""
        logger.info("CoAP настройка (заглушка)")
        # Реализация с использованием aiocoap или аналогичных библиотек

    def read_modbus_register(self, protocol_type, address, count=1, data_type='uint16'):
        """
        Чтение регистров Modbus
        :param protocol_type: 'modbus_tcp' или 'modbus_rtu'
        :param address: Адрес регистра
        :param count: Количество регистров для чтения
        :param data_type: Тип данных ('uint16', 'int16', 'uint32', 'int32', 'float32')
        :return: Значение или None
        """
        if protocol_type not in self.connections:
            logger.warning(f"Протокол {protocol_type} не подключен")
            return None

        conn_info = self.connections[protocol_type]
        client = conn_info['client']
        unit_id = conn_info['unit_id']

        try:
            # Выбор типа запроса в зависимости от количества регистров
            if count == 1:
                response = client.read_holding_registers(address, count, slave=unit_id)
            else:
                response = client.read_holding_registers(address, count, slave=unit_id)

            if response.isError():
                logger.error(f"Ошибка Modbus: {response}")
                return None

            # Декодирование данных
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.BIG)
            
            if data_type == 'uint16':
                value = decoder.decode_16bit_uint()
            elif data_type == 'int16':
                value = decoder.decode_16bit_int()
            elif data_type == 'uint32':
                value = decoder.decode_32bit_uint()
            elif data_type == 'int32':
                value = decoder.decode_32bit_int()
            elif data_type == 'float32':
                value = decoder.decode_32bit_float()
            else:
                # По умолчанию возвращаем список регистров
                value = response.registers

            # Кэширование
            cache_key = f"{protocol_type}_{address}_{count}_{data_type}"
            self.data_cache[cache_key] = {
                'value': value,
                'timestamp': time.time()
            }

            return value

        except Exception as e:
            logger.error(f"Ошибка чтения Modbus {protocol_type}: {e}")
            return None

    def write_modbus_register(self, protocol_type, address, value, data_type='uint16'):
        """
        Запись в регистр Modbus
        :param protocol_type: 'modbus_tcp' или 'modbus_rtu'
        :param address: Адрес регистра
        :param value: Значение для записи
        :param data_type: Тип данных
        :return: True/False
        """
        if protocol_type not in self.connections:
            logger.warning(f"Протокол {protocol_type} не подключен")
            return False

        conn_info = self.connections[protocol_type]
        client = conn_info['client']
        unit_id = conn_info['unit_id']

        try:
            # Реализация записи зависит от типа данных
            # Пример для одиночного регистра uint16
            if data_type in ['uint16', 'int16']:
                response = client.write_register(address, int(value), slave=unit_id)
            else:
                # Для многорегистровых типов нужно конвертировать значение
                logger.warning(f"Запись типа {data_type} не реализована")
                return False

            if response.isError():
                logger.error(f"Ошибка записи Modbus: {response}")
                return False

            logger.debug(f"Записано в {protocol_type} адрес {address}: {value}")
            return True

        except Exception as e:
            logger.error(f"Ошибка записи Modbus {protocol_type}: {e}")
            return False

# Пример использования
if __name__ == "__main__":
    # Пример конфигурации
    config = {
        'industrial': {
            'enabled': True,
            'protocols': ['modbus_tcp'],
            'modbus_tcp': {
                'host': '127.0.0.1',
                'port': 502,
                'unit_id': 1
            }
        }
    }

    industrial = IndustrialProtocols(config)
    industrial.start()

    # Попытка чтения (если есть реальное устройство)
    # value = industrial.read_modbus_register('modbus_tcp', 0, 1, 'uint16')
    # print(f"Прочитанное значение: {value}")

    industrial.stop()
