import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Конфигурационные параметры базы данных
DB_NAME = os.getenv("DB_NAME", "hh_vacancies")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password_here")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Список компаний для сбора данных
COMPANIES = [
    {"id": 1740, "name": "Яндекс"},
    {"id": 15478, "name": "VK"},
    {"id": 3529, "name": "Сбер"},
    {"id": 4181, "name": "2ГИС"},
    {"id": 1057, "name": "Касперский"},
    {"id": 907345, "name": "Тинькофф"},
    {"id": 4934, "name": "Билайн"},
    {"id": 39305, "name": "Газпром нефть"},
    {"id": 64174, "name": "СберТех"},
    {"id": 2324020, "name": "Ozon"}
]