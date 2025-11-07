import psycopg2
from psycopg2 import OperationalError, sql
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
import requests
from config import COMPANIES
import time


class HHAPI:
    """Класс для работы с API HH.ru"""

    def __init__(self):
        self.base_url = "https://api.hh.ru/"
        self.headers = {'User-Agent': 'HH-API-Client/1.0'}

    def get_employer_info(self, employer_id):
        """Получение информации о работодателе"""
        url = f"{self.base_url}employers/{employer_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка при получении данных о работодателе {employer_id}: {e}")
            return None

    def get_employer_vacancies(self, employer_id):
        """Получение вакансий работодателя"""
        url = f"{self.base_url}vacancies"
        params = {
            'employer_id': employer_id,
            'per_page': 50,
            'page': 0
        }
        vacancies = []

        try:
            while True:
                response = requests.get(url, params=params, headers=self.headers)

                # Проверяем статус ответа
                if response.status_code != 200:
                    print(f"⚠️ Ошибка API: {response.status_code} для работодателя {employer_id}")
                    break

                data = response.json()

                # Проверяем наличие ключа 'items'
                if 'items' not in data:
                    print(f"⚠️ Нет ключа 'items' в ответе для работодателя {employer_id}")
                    break

                # Фильтруем вакансии с None значениями
                valid_vacancies = [v for v in data['items'] if v is not None]
                vacancies.extend(valid_vacancies)

                # Проверяем, есть ли следующая страница
                params['page'] += 1
                if params['page'] >= data.get('pages', 0):
                    break

                # Задержка для соблюдения лимитов API
                time.sleep(0.1)

        except requests.RequestException as e:
            print(f"❌ Ошибка при получении вакансий для работодателя {employer_id}: {e}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка для работодателя {employer_id}: {e}")

        return vacancies


class Database:
    """Класс для работы с базой данных PostgreSQL"""

    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                dbname="postgres",  # Сначала подключаемся к стандартной БД
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()
            print("✅ Успешное подключение к PostgreSQL")
        except OperationalError as e:
            print(f"❌ Ошибка подключения к PostgreSQL: {e}")
            raise

    def create_database(self):
        """Создание базы данных и таблиц"""
        try:
            # Проверяем существование базы данных
            self.cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (DB_NAME,))
            exists = self.cursor.fetchone()

            if not exists:
                self.cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
                print(f"✅ База данных {DB_NAME} создана")
            else:
                print(f"✅ База данных {DB_NAME} уже существует")

            # Закрываем текущее соединение и подключаемся к новой БД
            self.cursor.close()
            self.conn.close()

            # Подключаемся к созданной базе данных
            self.conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()

            # Создаем таблицы
            self.create_tables()

        except Exception as e:
            print(f"❌ Ошибка при создании базы данных: {e}")
            raise

    def create_tables(self):
        """Создание таблиц employers и vacancies"""
        try:
            # Таблица работодателей
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS employers (
                    employer_id SERIAL PRIMARY KEY,
                    company_id INTEGER UNIQUE NOT NULL,
                    company_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    website VARCHAR(255),
                    open_vacancies INTEGER
                )
            """)

            # Таблица вакансий
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS vacancies (
                    vacancy_id SERIAL PRIMARY KEY,
                    employer_id INTEGER REFERENCES employers(employer_id) ON DELETE CASCADE,
                    vacancy_name VARCHAR(255) NOT NULL,
                    salary_from INTEGER,
                    salary_to INTEGER,
                    currency VARCHAR(10),
                    url VARCHAR(255) NOT NULL,
                    requirement TEXT,
                    responsibility TEXT
                )
            """)

            print("✅ Таблицы созданы успешно")

        except Exception as e:
            print(f"❌ Ошибка при создании таблиц: {e}")
            raise

    def insert_employer_data(self):
        """Заполнение таблицы employers данными"""
        hh_api = HHAPI()

        for company in COMPANIES:
            print(f"📋 Получаем данные о компании: {company['name']}...")
            employer_info = hh_api.get_employer_info(company["id"])

            if employer_info:
                try:
                    self.cursor.execute("""
                        INSERT INTO employers (company_id, company_name, description, website, open_vacancies)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (company_id) DO UPDATE SET
                        company_name = EXCLUDED.company_name,
                        description = EXCLUDED.description,
                        website = EXCLUDED.website,
                        open_vacancies = EXCLUDED.open_vacancies
                    """, (
                        company["id"],
                        employer_info.get('name', company['name']),
                        employer_info.get('description', '')[:1000],  # Ограничиваем длину
                        employer_info.get('site_url', ''),
                        employer_info.get('open_vacancies', 0)
                    ))

                    print(f"✅ Добавлен работодатель: {employer_info.get('name', company['name'])}")

                except Exception as e:
                    print(f"❌ Ошибка при добавлении работодателя {company['name']}: {e}")

            # Задержка для соблюдения лимитов API
            time.sleep(0.2)

    def insert_vacancies_data(self):
        """Заполнение таблицы vacancies данными"""
        hh_api = HHAPI()


        for company in COMPANIES:
            # Получаем employer_id из базы данных
            self.cursor.execute("SELECT employer_id FROM employers WHERE company_id = %s", (company["id"],))
            result = self.cursor.fetchone()

            if result:
                employer_id = result[0]
                print(f"📝 Получаем вакансии для: {company['name']}...")
                vacancies = hh_api.get_employer_vacancies(company["id"])

                added_count = 0
                for vacancy in vacancies:
                    try:
                        # Безопасное извлечение данных с проверками
                        vacancy_name = vacancy.get('name', 'Не указано')
                        if not vacancy_name:
                            vacancy_name = 'Не указано'

                        # Обработка зарплаты с проверками
                        salary_from = None
                        salary_to = None
                        currency = None

                        salary_data = vacancy.get('salary')
                        if salary_data:
                            salary_from = salary_data.get('from')
                            salary_to = salary_data.get('to')
                            currency = salary_data.get('currency')

                        # Обработка URL
                        url = vacancy.get('alternate_url', '')
                        if not url:
                            url = vacancy.get('url', '')

                        # Безопасное извлечение snippet данных
                        snippet = vacancy.get('snippet') or {}
                        requirement = snippet.get('requirement', '') or ''
                        responsibility = snippet.get('responsibility', '') or ''

                        # Ограничение длины текстовых полей
                        vacancy_name = str(vacancy_name)[:250]
                        requirement = str(requirement)[:1000]
                        responsibility = str(responsibility)[:1000]
                        url = str(url)[:255]

                        self.cursor.execute("""
                            INSERT INTO vacancies 
                            (employer_id, vacancy_name, salary_from, salary_to, currency, url, requirement, responsibility)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            employer_id,
                            vacancy_name,
                            salary_from,
                            salary_to,
                            currency,
                            url,
                            requirement,
                            responsibility
                        ))
                        added_count += 1

                    except Exception as e:
                        print(f"❌ Ошибка при добавлении вакансии '{vacancy.get('name', 'Unknown')}': {e}")
                        # Для отладки можно вывести проблемную вакансию
                        # print(f"Проблемные данные: {vacancy}")
                        continue

                print(f"✅ Добавлено {added_count} вакансий для {company['name']}")

            # Задержка для соблюдения лимитов API
            time.sleep(0.3)

    def close(self):
        """Закрытие соединения с базой данных"""
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()
        print("✅ Соединение с базой данных закрыто")