"""
Главный файл каталога. Объединяет основной каталог и тестовые программы.
"""

from .programs_catalog import PROGRAMS_CATALOG
from .test_catalog import TEST_CATALOG

CATALOG = TEST_CATALOG + PROGRAMS_CATALOG
