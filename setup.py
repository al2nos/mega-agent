# setup.py
# Необходим для совместимости с legacy builds, как указано в документации setuptools.
# Даже если основная конфигурация находится в pyproject.toml/setup.cfg,
# этот файл требуется для некоторых инструментов/сценариев сборки.

from setuptools import setup

# setup() будет использовать конфигурацию из pyproject.toml
setup()
