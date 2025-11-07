import pytest
import sys
import os

# Добавляем путь к src для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Настройка тестового окружения для всех тестов"""
    # Сохраняем оригинальные переменные окружения
    original_env = os.environ.copy()

    # Устанавливаем тестовые переменные окружения
    os.environ['DB_NAME'] = 'test_db'
    os.environ['DB_USER'] = 'test_user'
    os.environ['DB_PASSWORD'] = 'test_password'
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_PORT'] = '5432'

    yield

    # Восстанавливаем оригинальные переменные окружения
    os.environ.clear()
    os.environ.update(original_env)