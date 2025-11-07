import psycopg2
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
import requests
from config import COMPANIES


class HHAPI:
    """Класс для работы с API HH.ru"""

    def __init__(self):
        self.base_url = "https://api.hh.ru/"

    def get_employer_info(self, employer_id):
        """Получение информации о работодателе"""
        url = f"{self.base_url}employers/{employer_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def get_employer_vacancies(self, employer_id):
        """Получение вакансий работодателя"""
        url = f"{self.base_url}vacancies"
        params = {
            'employer_id': employer_id,
            'per_page': 100,
            'page': 0
        }
        vacancies = []

        while True:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                break

            data = response.json()
            vacancies.extend(data['items'])

            params['page'] += 1
            if params['page'] >= data['pages']:
                break

        return vacancies


class Database:
    """Класс для работы с базой данных PostgreSQL"""

    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def create_database(self):
        """Создание базы данных и таблиц"""
        try:
            # Создаем базу данных если не существует
            conn = psycopg2.connect(
                dbname="postgres",
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            conn.autocommit = True
            cursor = conn.cursor()

            cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
            exists = cursor.fetchone()

            if not exists:
                cursor.execute(f"CREATE DATABASE {DB_NAME}")

            cursor.close()
            conn.close()

            # Создаем таблицы
            self.create_tables()

        except Exception as e:
            print(f"Ошибка при создании базы данных: {e}")

    def create_tables(self):
        """Создание таблиц employers и vacancies"""

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
                employer_id INTEGER REFERENCES employers(employer_id),
                vacancy_name VARCHAR(255) NOT NULL,
                salary_from INTEGER,
                salary_to INTEGER,
                currency VARCHAR(10),
                url VARCHAR(255) NOT NULL,
                requirement TEXT,
                responsibility TEXT
            )
        """)

    def insert_employer_data(self):
        """Заполнение таблицы employers данными"""
        hh_api = HHAPI()

        for company in COMPANIES:
            employer_info = hh_api.get_employer_info(company["id"])

            if employer_info:
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
                    employer_info.get('name'),
                    employer_info.get('description'),
                    employer_info.get('site_url'),
                    employer_info.get('open_vacancies', 0)
                ))

                print(f"Добавлен работодатель: {employer_info.get('name')}")

    def insert_vacancies_data(self):
        """Заполнение таблицы vacancies данными"""
        hh_api = HHAPI()

        for company in COMPANIES:
            # Получаем employer_id из базы данных
            self.cursor.execute("SELECT employer_id FROM employers WHERE company_id = %s", (company["id"],))
            result = self.cursor.fetchone()

            if result:
                employer_id = result[0]
                vacancies = hh_api.get_employer_vacancies(company["id"])

                for vacancy in vacancies:
                    salary_from = None
                    salary_to = None
                    currency = None

                    if vacancy.get('salary'):
                        salary = vacancy['salary']
                        salary_from = salary.get('from')
                        salary_to = salary.get('to')
                        currency = salary.get('currency')

                    self.cursor.execute("""
                        INSERT INTO vacancies (employer_id, vacancy_name, salary_from, salary_to, currency, url, requirement, responsibility)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (vacancy_id) DO NOTHING
                    """, (
                        employer_id,
                        vacancy.get('name'),
                        salary_from,
                        salary_to,
                        currency,
                        vacancy.get('alternate_url'),
                        vacancy.get('snippet', {}).get('requirement'),
                        vacancy.get('snippet', {}).get('responsibility')
                    ))

                print(f"Добавлено {len(vacancies)} вакансий для {company['name']}")

    def close(self):
        """Закрытие соединения с базой данных"""
        self.cursor.close()
        self.conn.close()