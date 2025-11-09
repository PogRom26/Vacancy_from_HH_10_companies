import os
import sys

from src.config import (COMPANIES, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT,
                        DB_USER)

# Явно добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))


class TestConfig:
    """Тесты для конфигурационного файла"""

    def test_db_variables_exist(self):
        """Проверка наличия переменных базы данных"""
        assert DB_NAME is not None
        assert DB_USER is not None
        assert DB_PASSWORD is not None
        assert DB_HOST is not None
        assert DB_PORT is not None

    def test_db_variables_types(self):
        """Проверка типов переменных базы данных"""
        assert isinstance(DB_NAME, str)
        assert isinstance(DB_USER, str)
        assert isinstance(DB_PASSWORD, str)
        assert isinstance(DB_HOST, str)
        assert isinstance(DB_PORT, str)

    def test_companies_list(self):
        """Проверка списка компаний"""
        assert isinstance(COMPANIES, list)
        assert len(COMPANIES) >= 10

        for company in COMPANIES:
            assert "id" in company
            assert "name" in company
            assert isinstance(company["id"], int)
            assert isinstance(company["name"], str)
            assert company["id"] > 0
            assert len(company["name"]) > 0

    def test_companies_unique_ids(self):
        """Проверка уникальности ID компаний"""
        company_ids = [company["id"] for company in COMPANIES]
        assert len(company_ids) == len(set(company_ids))
