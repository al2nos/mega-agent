#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для мониторинга и аналитики
"""

import logging
import pandas as pd
import numpy as np
import json
import time
import os
from datetime import datetime, timedelta
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import smtplib
# import sqlite3 # Для локальной БД истории

logger = logging.getLogger(__name__)

class MonitoringAnalytics:
    def __init__(self, config):
        self.config = config.get('monitoring', {})
        self.enabled = self.config.get('enabled', False)
        self.data_storage = self.config.get('data_storage', 'memory') # 'memory', 'file', 'database'
        self.storage_path = self.config.get('storage_path', './monitoring_data')
        self.data_history = {} # Для хранения в памяти
        self.alerts_history = []
        self.insights = []

        # Создание директории для хранения данных, если нужно
        if self.data_storage == 'file':
            os.makedirs(self.storage_path, exist_ok=True)

    def start(self):
        """Запуск модуля мониторинга"""
        if not self.enabled:
            logger.info("Модуль мониторинга отключен")
            return

        logger.info("Модуль мониторинга и аналитики запущен")

    def stop(self):
        """Остановка модуля"""
        logger.info("Модуль мониторинга остановлен")
        # Здесь можно добавить сохранение данных при остановке

    def collect_data(self, data_type, data, timestamp=None):
        """
        Сбор данных для анализа
        :param data_type: Тип данных (например, 'temperature', 'energy', 'device_status')
        :param data: Собственно данные
        :param timestamp: Временная метка (по умолчанию текущее время)
        """
        if timestamp is None:
            timestamp = time.time()

        record = {
            'timestamp': timestamp,
            'data': data
        }

        if self.data_storage == 'memory':
            if data_type not in self.data_history:
                self.data_history[data_type] = []
            self.data_history[data_type].append(record)

            # Ограничение размера истории в памяти (например, последние 1000 записей)
            if len(self.data_history[data_type]) > 1000:
                self.data_history[data_type] = self.data_history[data_type][-1000:]

        elif self.data_storage == 'file':
            # Сохранение в файл
            filename = os.path.join(self.storage_path, f"{data_type}.jsonl")
            with open(filename, 'a') as f:
                f.write(json.dumps(record) + '\n')

        logger.debug(f"Собраны данные {data_type}: {data}")

    def analyze_patterns(self, data_type, window_size=100):
        """
        Анализ паттернов в данных
        :param data_type: Тип данных для анализа
        :param window_size: Размер окна для анализа
        :return: Статистика
        """
        data_points = self._get_data_points(data_type, window_size)
        if not data_points:
            return None

        try:
            # Преобразование в pandas DataFrame для удобства
            df = pd.DataFrame(data_points)
            
            # Если данные - словари, попробуем извлечь числовые значения
            if df['data'].dtype == 'object':
                # Простая попытка: если data - число или строка-число
                numeric_data = pd.to_numeric(df['data'], errors='coerce')
                if not numeric_data.isna().all():
                    df['numeric_value'] = numeric_data
                else:
                    # Если не удалось, возвращаем базовую статистику по времени
                    stats = {
                        'count': len(df),
                        'time_span': df['timestamp'].max() - df['timestamp'].min() if len(df) > 1 else 0
                    }
                    return stats
            else:
                df['numeric_value'] = df['data']

            # Расчет статистики
            stats = {
                'count': len(df),
                'mean': df['numeric_value'].mean(),
                'std': df['numeric_value'].std(),
                'min': df['numeric_value'].min(),
                'max': df['numeric_value'].max(),
                'median': df['numeric_value'].median(),
                'trend': self._calculate_trend(df['numeric_value'].values)
            }

            return stats

        except Exception as e:
            logger.error(f"Ошибка анализа данных {data_type}: {e}")
            return None

    def _get_data_points(self, data_type, limit=None):
        """Получение точек данных из хранилища"""
        if self.data_storage == 'memory':
            points = self.data_history.get(data_type, [])
        elif self.data_storage == 'file':
            points = []
            filename = os.path.join(self.storage_path, f"{data_type}.jsonl")
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        lines = f.readlines()
                        if limit:
                            lines = lines[-limit:] # Последние N записей
                        for line in lines:
                            points.append(json.loads(line.strip()))
                except Exception as e:
                    logger.error(f"Ошибка чтения файла {filename}: {e}")
        else:
            points = []

        return points

    def _calculate_trend(self, values):
        """Расчет тренда"""
        if len(values) < 2:
            return 'stable'

        # Простой линейный тренд с использованием numpy
        x = np.arange(len(values))
        # Используем polyfit для линейной регрессии
        if len(np.unique(values)) > 1: # Проверка, что не все значения одинаковы
            slope = np.polyfit(x, values, 1)[0]
            if slope > 0.1:
                return 'increasing'
            elif slope < -0.1:
                return 'decreasing'
            else:
                return 'stable'
        else:
            return 'stable'

    def predict_future(self, data_type, periods=24):
        """
        Прогнозирование на будущее
        :param data_type: Тип данных
        :param periods: Количество периодов для прогноза
        :return: Прогноз
        """
        data_points = self._get_data_points(data_type)
        if len(data_points) < 10:
            return None

        try:
            # Извлечение числовых значений
            values = []
            for point in data_points:
                try:
                    val = float(point['data'])
                    values.append(val)
                except (ValueError, TypeError):
                    continue

            if len(values) < 10:
                return None

            # Используем простое экспоненциальное сглаживание для прогноза
            alpha = 0.3  # Коэффициент сглаживания
            last_value = values[-1]
            predictions = []

            for i in range(periods):
                predicted = alpha * last_value + (1 - alpha) * last_value
                predictions.append(predicted)
                last_value = predicted # Для следующей итерации

            return predictions

        except Exception as e:
            logger.error(f"Ошибка прогнозирования для {data_type}: {e}")
            return None

    def generate_insights(self):
        """Генерация инсайтов на основе собранных данных"""
        insights = []

        # Анализ различных типов данных
        for data_type in self.data_history.keys() if self.data_storage == 'memory' else []:
            stats = self.analyze_patterns(data_type)
            if stats:
                insight = self._create_insight_from_stats(data_type, stats)
                if insight:
                    insights.append(insight)

        self.insights = insights
        return insights

    def _create_insight_from_stats(self, data_type, stats):
        """Создание инсайта из статистики"""
        if stats['trend'] == 'increasing':
            return {
                'type': data_type,
                'priority': 'medium',
                'message': f'{data_type} показывает растущую тенденцию. Среднее значение: {stats["mean"]:.2f}'
            }
        elif stats['trend'] == 'decreasing':
            return {
                'type': data_type,
                'priority': 'medium',
                'message': f'{data_type} показывает снижающуюся тенденцию. Среднее значение: {stats["mean"]:.2f}'
            }
        elif stats['std'] > (stats['mean'] * 0.2): # Высокое отклонение
            return {
                'type': data_type,
                'priority': 'low',
                'message': f'{data_type} имеет высокую вариабельность. Стандартное отклонение: {stats["std"]:.2f}'
            }
        return None

    def add_alert(self, alert_type, message, level='info'):
        """
        Добавление алерта в историю
        :param alert_type: Тип алерта
        :param message: Сообщение
        :param level: Уровень (info, warning, error)
        """
        alert = {
            'timestamp': time.time(),
            'type': alert_type,
            'level': level,
            'message': message
        }
        self.alerts_history.append(alert)
        logger.log(
            logging.INFO if level == 'info' else logging.WARNING if level == 'warning' else logging.ERROR,
            f"Алерт [{level.upper()}] {alert_type}: {message}"
        )

        # Ограничение размера истории алертов
        if len(self.alerts_history) > 1000:
            self.alerts_history = self.alerts_history[-1000:]

    def get_alerts_history(self, hours=24):
        """
        Получение истории алертов за последние N часов
        :param hours: Количество часов
        :return: Список алертов
        """
        since = time.time() - (hours * 3600)
        recent_alerts = [a for a in self.alerts_history if a['timestamp'] >= since]
        return recent_alerts

    def get_daily_report(self):
        """Генерация ежедневного отчета"""
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'summary': {
                'total_data_points': sum(len(v) for v in self.data_history.values()) if self.data_storage == 'memory' else 'N/A',
                'total_alerts': len(self.alerts_history),
                'active_data_types': list(self.data_history.keys()) if self.data_storage == 'memory' else 'N/A',
                'insights_count': len(self.insights)
            },
            'analytics': {},
            'recent_alerts': self.get_alerts_history(24), # Алерты за последние 24 часа
            'insights': self.insights
        }

        # Добавляем аналитику по каждой системе
        if self.data_storage == 'memory':
            for data_type in self.data_history:
                stats = self.analyze_patterns(data_type)
                if stats:
                    report['analytics'][data_type] = stats

        return report

    def export_data(self, data_type, format='csv', filename=None):
        """
        Экспорт данных
        :param data_type: Тип данных
        :param format: Формат ('csv', 'json')
        :param filename: Имя файла (по умолчанию генерируется)
        """
        data_points = self._get_data_points(data_type)
        if not data_points:
            logger.warning(f"Нет данных для экспорта типа {data_type}")
            return None

        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{data_type}_{timestamp}.{format}"

        filepath = os.path.join(self.storage_path, filename)

        try:
            if format == 'csv':
                df = pd.DataFrame(data_points)
                # Преобразование timestamp в читаемый формат
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                df.to_csv(filepath, index=False)
            elif format == 'json':
                with open(filepath, 'w') as f:
                    json.dump(data_points, f, indent=2)

            logger.info(f"Данные {data_type} экспортированы в {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Ошибка экспорта данных {data_type}: {e}")
            return None

# Пример использования
if __name__ == "__main__":
    # Пример конфигурации
    config = {
        'monitoring': {
            'enabled': True,
            'data_storage': 'memory', # или 'file'
            'storage_path': './monitoring_data'
        }
    }

    monitoring = MonitoringAnalytics(config)
    monitoring.start()

    # Симуляция сбора данных
    import random
    for i in range(20):
        temp = 20 + random.uniform(-5, 5)
        monitoring.collect_data('temperature', temp)
        time.sleep(0.1)

    # Анализ
    stats = monitoring.analyze_patterns('temperature')
    print(f"Статистика температуры: {stats}")

    # Прогноз
    forecast = monitoring.predict_future('temperature', 5)
    print(f"Прогноз температуры: {forecast}")

    # Инсайты
    insights = monitoring.generate_insights()
    print(f"Инсайты: {insights}")

    monitoring.stop()
