import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from src.database import Database, HHAPI
from src.config import COMPANIES


class TestHHAPI:
    """Тесты для класса HHAPI"""

    @pytest.fixture
    def hh_api(self):
        return HHAPI()

    def test_init(self, hh_api):
        """Тест инициализации HHAPI"""
        assert hh_api.base_url == "https://api.hh.ru/"
        assert 'User-Agent' in hh_api.headers

    @patch('src.database.requests.get')
    def test_get_employer_info_success(self, mock_get, hh_api):
        """Тест успешного получения информации о работодателе"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 1740,
            'name': 'Яндекс',
            'description': 'Test description',
            'site_url': 'https://yandex.ru',
            'open_vacancies': 10
        }
        mock_get.return_value = mock_response

        result = hh_api.get_employer_info(1740)

        assert result is not None
        assert result['name'] == 'Яндекс'
        mock_get.assert_called_once()

    @patch('src.database.requests.get')
    def test_get_employer_info_failure(self, mock_get, hh_api):
        """Тест неудачного получения информации о работодателе"""
        # Создаем мок, который имитирует RequestException
        mock_get.side_effect = requests.RequestException("404 Error")

        result = hh_api.get_employer_info(999999)

        assert result is None

    @patch('src.database.requests.get')
    def test_get_employer_info_http_error(self, mock_get, hh_api):
        """Тест получения HTTP ошибки"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Error")
        mock_get.return_value = mock_response

        result = hh_api.get_employer_info(999999)

        assert result is None

    @patch('src.database.requests.get')
    def test_get_employer_vacancies_success(self, mock_get, hh_api):
        """Тест успешного получения вакансий"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'name': 'Python Developer',
                    'salary': {'from': 100000, 'to': 150000, 'currency': 'RUR'},
                    'alternate_url': 'https://hh.ru/vacancy/123',
                    'snippet': {'requirement': 'Python experience', 'responsibility': 'Development'}
                }
            ],
            'pages': 1,
            'page': 0
        }
        mock_get.return_value = mock_response

        result = hh_api.get_employer_vacancies(1740)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['name'] == 'Python Developer'

    @patch('src.database.requests.get')
    def test_get_employer_vacancies_api_error(self, mock_get, hh_api):
        """Тест получения ошибки API при запросе вакансий"""
        mock_response = Mock()
        mock_response.status_code = 429  # Too Many Requests
        mock_get.return_value = mock_response

        result = hh_api.get_employer_vacancies(1740)

        assert isinstance(result, list)
        assert len(result) == 0

    @patch('src.database.requests.get')
    def test_get_employer_vacancies_no_items(self, mock_get, hh_api):
        """Тест получения вакансий без items"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [],
            'pages': 0,
            'page': 0
        }
        mock_get.return_value = mock_response

        result = hh_api.get_employer_vacancies(1740)

        assert isinstance(result, list)
        assert len(result) == 0


class TestDatabase:
    """Тесты для класса Database"""

    @pytest.fixture
    def mock_db(self):
        """Фикстура для мока базы данных"""
        with patch('src.database.psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.autocommit = True

            db = Database()
            db.conn = mock_conn
            db.cursor = mock_cursor

            yield db, mock_connect, mock_conn, mock_cursor

    def test_database_init(self, mock_db):
        """Тест инициализации базы данных"""
        db, mock_connect, mock_conn, mock_cursor = mock_db

        assert db.conn is mock_conn
        assert db.cursor is mock_cursor

    def test_create_tables(self, mock_db):
        """Тест создания таблиц"""
        db, mock_connect, mock_conn, mock_cursor = mock_db

        db.create_tables()

        # Проверяем, что execute вызывался для создания таблиц
        assert mock_cursor.execute.call_count >= 2

        # Получаем все вызовы execute
        calls = [call[0][0] for call in mock_cursor.execute.call_args_list]

        # Проверяем, что есть вызовы CREATE TABLE
        create_table_calls = [call for call in calls if 'CREATE TABLE' in call]
        assert len(create_table_calls) >= 2

    @patch('src.database.psycopg2.connect')
    def test_create_database_new_db(self, mock_connect):
        """Тест создания новой базы данных"""
        # Мокаем первое соединение (к postgres)
        mock_conn1 = Mock()
        mock_cursor1 = Mock()
        # Мокаем второе соединение (к новой БД)
        mock_conn2 = Mock()
        mock_cursor2 = Mock()

        mock_connect.side_effect = [mock_conn1, mock_conn2]
        mock_conn1.cursor.return_value = mock_cursor1
        mock_conn2.cursor.return_value = mock_cursor2
        mock_conn1.autocommit = True
        mock_conn2.autocommit = True

        # База данных не существует
        mock_cursor1.fetchone.return_value = None

        db = Database()
        db.create_database()

        # Проверяем, что CREATE DATABASE был вызван
        mock_cursor1.execute.assert_called()

    @patch('src.database.psycopg2.connect')
    def test_create_database_existing_db(self, mock_connect):
        """Тест работы с существующей базой данных"""
        mock_conn1 = Mock()
        mock_cursor1 = Mock()
        mock_conn2 = Mock()
        mock_cursor2 = Mock()

        mock_connect.side_effect = [mock_conn1, mock_conn2]
        mock_conn1.cursor.return_value = mock_cursor1
        mock_conn2.cursor.return_value = mock_cursor2
        mock_conn1.autocommit = True
        mock_conn2.autocommit = True

        # База данных уже существует
        mock_cursor1.fetchone.return_value = [1]

        db = Database()
        db.create_database()

        # Проверяем, что CREATE DATABASE НЕ был вызван
        create_db_calls = [call for call in mock_cursor1.execute.call_args_list
                           if 'CREATE DATABASE' in str(call)]
        assert len(create_db_calls) == 0

    @patch('src.database.HHAPI')
    @patch('src.database.time.sleep')
    def test_insert_employer_data(self, mock_sleep, mock_hh_api, mock_db):
        """Тест вставки данных работодателей"""
        db, mock_connect, mock_conn, mock_cursor = mock_db

        mock_api_instance = Mock()
        mock_hh_api.return_value = mock_api_instance
        mock_api_instance.get_employer_info.return_value = {
            'name': 'Яндекс',
            'description': 'Test description',
            'site_url': 'https://yandex.ru',
            'open_vacancies': 5
        }

        db.insert_employer_data()

        # Проверяем, что API вызывалось для каждой компании
        assert mock_api_instance.get_employer_info.call_count == len(COMPANIES)

        # Проверяем, что execute вызывался для каждой компании
        assert mock_cursor.execute.call_count == len(COMPANIES)

    @patch('src.database.HHAPI')
    @patch('src.database.time.sleep')
    def test_insert_employer_data_with_none(self, mock_sleep, mock_hh_api, mock_db):
        """Тест вставки данных работодателей с None ответом"""
        db, mock_connect, mock_conn, mock_cursor = mock_db

        mock_api_instance = Mock()
        mock_hh_api.return_value = mock_api_instance
        # Возвращаем None для некоторых компаний
        mock_api_instance.get_employer_info.side_effect = [
                                                              {'name': 'Яндекс', 'description': 'Test',
                                                               'site_url': 'https://yandex.ru', 'open_vacancies': 5},
                                                              None,  # Вторая компания возвращает None
                                                              {'name': 'Сбер', 'description': 'Test',
                                                               'site_url': 'https://sber.ru', 'open_vacancies': 3}
                                                          ] + [None] * 7  # Остальные компании тоже возвращают None

        db.insert_employer_data()

        # Проверяем, что API вызывалось для каждой компании, даже если возвращает None
        assert mock_api_instance.get_employer_info.call_count == len(COMPANIES)

    @patch('src.database.HHAPI')
    @patch('src.database.time.sleep')
    def test_insert_vacancies_data(self, mock_sleep, mock_hh_api, mock_db):
        """Тест вставки данных вакансий"""
        db, mock_connect, mock_conn, mock_cursor = mock_db

        # Мокаем выборку employer_id
        mock_cursor.fetchone.return_value = (1,)

        mock_api_instance = Mock()
        mock_hh_api.return_value = mock_api_instance
        mock_api_instance.get_employer_vacancies.return_value = [
            {
                'name': 'Python Developer',
                'salary': {'from': 100000, 'to': 150000, 'currency': 'RUR'},
                'alternate_url': 'https://hh.ru/vacancy/123',
                'snippet': {'requirement': 'Python', 'responsibility': 'Development'}
            }
        ]

        db.insert_vacancies_data()

        # Проверяем, что API вызывалось для каждой компании
        assert mock_api_instance.get_employer_vacancies.call_count == len(COMPANIES)

    @patch('src.database.HHAPI')
    @patch('src.database.time.sleep')
    def test_insert_vacancies_data_no_employer(self, mock_sleep, mock_hh_api, mock_db):
        """Тест вставки вакансий когда работодатель не найден"""
        db, mock_connect, mock_conn, mock_cursor = mock_db

        # Мокаем, что employer_id не найден
        mock_cursor.fetchone.return_value = None

        mock_api_instance = Mock()
        mock_hh_api.return_value = mock_api_instance

        db.insert_vacancies_data()

        # Проверяем, что get_employer_vacancies НЕ вызывалось
        assert mock_api_instance.get_employer_vacancies.call_count == 0

    def test_close_connection(self, mock_db):
        """Тест закрытия соединения"""
        db, mock_connect, mock_conn, mock_cursor = mock_db

        db.close()

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()