import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import builtins

# Явно добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from src.main import display_vacancies, main


class TestMain:
    """Тесты для основного файла приложения"""

    def test_display_vacancies_with_data(self):
        """Тест отображения вакансий с данными"""
        test_vacancies = [
            ('Яндекс', 'Python Developer', 100000, 150000, 'RUR', 'https://hh.ru/vacancy/1'),
            ('Сбер', 'Java Developer', 0, 0, '', 'https://hh.ru/vacancy/2')
        ]

        # Проверяем, что функция не падает с данными
        try:
            display_vacancies(test_vacancies, "Тестовые вакансии")
            assert True
        except Exception:
            assert False

    def test_display_vacancies_empty(self):
        """Тест отображения пустого списка вакансий"""
        # Проверяем, что функция не падает с пустым списком
        try:
            display_vacancies([], "Пустые вакансии")
            assert True
        except Exception:
            assert False

    @patch('src.main.Database')
    @patch('src.main.DBManager')
    @patch('builtins.input')
    def test_main_menu_option_1(self, mock_input, mock_db_manager, mock_database):
        """Тест главного меню - опция 1"""
        # Настраиваем моки
        mock_db_instance = Mock()
        mock_db_manager.return_value = mock_db_instance
        mock_db_instance.get_companies_and_vacancies_count.return_value = [
            ('Яндекс', 10),
            ('Сбер', 5)
        ]

        # Симулируем выбор опции 1 и затем выход
        mock_input.side_effect = ['1', '0']

        # Запускаем main и проверяем, что не было исключений
        try:
            main()
            assert True
        except SystemExit:
            assert True
        except Exception:
            assert False