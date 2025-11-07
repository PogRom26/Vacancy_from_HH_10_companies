import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Явно добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from src.db_manager import DBManager


class TestDBManager:
    """Тесты для класса DBManager"""

    @pytest.fixture
    def mock_db_manager(self):
        with patch('src.db_manager.psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_cur = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cur

            db_manager = DBManager()
            db_manager.conn = mock_conn
            db_manager.cur = mock_cur

            yield db_manager, mock_conn, mock_cur

    def test_db_manager_init(self, mock_db_manager):
        """Тест инициализации DBManager"""
        db_manager, mock_conn, mock_cur = mock_db_manager

        assert db_manager.conn is mock_conn
        assert db_manager.cur is mock_cur

    def test_get_companies_and_vacancies_count(self, mock_db_manager):
        """Тест получения компаний и количества вакансий"""
        db_manager, mock_conn, mock_cur = mock_db_manager

        # Мокаем данные из базы
        mock_cur.fetchall.return_value = [
            ('Яндекс', 15),
            ('Сбер', 10),
            ('VK', 8)
        ]

        result = db_manager.get_companies_and_vacancies_count()

        assert len(result) == 3
        assert result[0] == ('Яндекс', 15)
        mock_cur.execute.assert_called_once()

    def test_get_all_vacancies(self, mock_db_manager):
        """Тест получения всех вакансий"""
        db_manager, mock_conn, mock_cur = mock_db_manager

        mock_cur.fetchall.return_value = [
            ('Яндекс', 'Python Developer', 100000, 150000, 'RUR', 'https://hh.ru/vacancy/1'),
            ('Сбер', 'Java Developer', 120000, 180000, 'RUR', 'https://hh.ru/vacancy/2')
        ]

        result = db_manager.get_all_vacancies()

        assert len(result) == 2
        assert result[0][1] == 'Python Developer'
        mock_cur.execute.assert_called_once()

    def test_get_avg_salary(self, mock_db_manager):
        """Тест получения средней зарплаты"""
        db_manager, mock_conn, mock_cur = mock_db_manager

        mock_cur.fetchone.return_value = (125000,)

        result = db_manager.get_avg_salary()

        assert result == 125000
        mock_cur.execute.assert_called_once()

    def test_get_avg_salary_no_data(self, mock_db_manager):
        """Тест получения средней зарплаты при отсутствии данных"""
        db_manager, mock_conn, mock_cur = mock_db_manager

        mock_cur.fetchone.return_value = (None,)

        result = db_manager.get_avg_salary()

        assert result == 0

    def test_get_vacancies_with_higher_salary(self, mock_db_manager):
        """Тест получения вакансий с зарплатой выше средней"""
        db_manager, mock_conn, mock_cur = mock_db_manager

        # Мокаем среднюю зарплату
        with patch.object(db_manager, 'get_avg_salary', return_value=100000):
            mock_cur.fetchall.return_value = [
                ('Яндекс', 'Senior Developer', 200000, 250000, 'RUR', 'https://hh.ru/vacancy/1')
            ]

            result = db_manager.get_vacancies_with_higher_salary()

            assert len(result) == 1
            assert result[0][1] == 'Senior Developer'
            mock_cur.execute.assert_called_once()

    def test_get_vacancies_with_keyword(self, mock_db_manager):
        """Тест поиска вакансий по ключевому слову"""
        db_manager, mock_conn, mock_cur = mock_db_manager

        mock_cur.fetchall.return_value = [
            ('Яндекс', 'Python Developer', 100000, 150000, 'RUR', 'https://hh.ru/vacancy/1')
        ]

        result = db_manager.get_vacancies_with_keyword('python')

        assert len(result) == 1
        assert 'python' in result[0][1].lower()
        mock_cur.execute.assert_called_once()

    def test_close_connection(self, mock_db_manager):
        """Тест закрытия соединения"""
        db_manager, mock_conn, mock_cur = mock_db_manager

        db_manager.close()

        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()