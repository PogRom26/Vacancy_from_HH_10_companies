import psycopg2

from src.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


class DBManager:
    """Класс для управления данными в PostgreSQL"""

    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
            )
            self.cur = self.conn.cursor()
            print("✅ Успешное подключение к базе данных")
        except Exception as e:
            print(f"❌ Ошибка подключения к базе данных: {e}")
            raise

    def get_companies_and_vacancies_count(self):
        """
        Получает список всех компаний и количество вакансий у каждой компании
        """
        try:
            query = """
                SELECT e.company_name, COUNT(v.vacancy_id) as vacancy_count
                FROM employers e
                LEFT JOIN vacancies v ON e.employer_id = v.employer_id
                GROUP BY e.company_name
                ORDER BY vacancy_count DESC
            """
            self.cur.execute(query)
            return self.cur.fetchall()
        except Exception as e:
            print(f"❌ Ошибка при получении списка компаний: {e}")
            return []

    def get_all_vacancies(self):
        """
        Получает список всех вакансий с указанием названия компании,
        названия вакансии, зарплаты и ссылки на вакансию
        """
        try:
            query = """
                SELECT 
                    e.company_name,
                    v.vacancy_name,
                    COALESCE(v.salary_from, 0) as salary_from,
                    COALESCE(v.salary_to, 0) as salary_to,
                    v.currency,
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                ORDER BY e.company_name, v.vacancy_name
            """
            self.cur.execute(query)
            return self.cur.fetchall()
        except Exception as e:
            print(f"❌ Ошибка при получении списка вакансий: {e}")
            return []

    def get_avg_salary(self):
        """
        Получает среднюю зарплату по вакансиям
        """
        try:
            query = """
                SELECT 
                    AVG(
                        CASE 
                            WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL THEN (salary_from + salary_to) / 2
                            WHEN salary_from IS NOT NULL THEN salary_from
                            WHEN salary_to IS NOT NULL THEN salary_to
                            ELSE NULL
                        END
                    ) as avg_salary
                FROM vacancies 
                WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
            """
            self.cur.execute(query)
            result = self.cur.fetchone()
            return round(result[0]) if result and result[0] else 0
        except Exception as e:
            print(f"❌ Ошибка при расчете средней зарплаты: {e}")
            return 0

    def get_vacancies_with_higher_salary(self):
        """
        Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям
        """
        try:
            avg_salary = self.get_avg_salary()

            query = """
                SELECT 
                    e.company_name,
                    v.vacancy_name,
                    COALESCE(v.salary_from, 0) as salary_from,
                    COALESCE(v.salary_to, 0) as salary_to,
                    v.currency,
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                WHERE 
                    (CASE 
                        WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL THEN (salary_from + salary_to) / 2
                        WHEN salary_from IS NOT NULL THEN salary_from
                        WHEN salary_to IS NOT NULL THEN salary_to
                        ELSE 0
                    END) > %s
                ORDER BY 
                    (CASE 
                        WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL THEN (salary_from + salary_to) / 2
                        WHEN salary_from IS NOT NULL THEN salary_from
                        WHEN salary_to IS NOT NULL THEN salary_to
                        ELSE 0
                    END) DESC
            """
            self.cur.execute(query, (avg_salary,))
            return self.cur.fetchall()
        except Exception as e:
            print(f"❌ Ошибка при получении вакансий с высокой зарплатой: {e}")
            return []

    def get_vacancies_with_keyword(self, keyword):
        """
        Получает список всех вакансий, в названии которых содержатся переданные слова
        """
        try:
            query = """
                SELECT 
                    e.company_name,
                    v.vacancy_name,
                    COALESCE(v.salary_from, 0) as salary_from,
                    COALESCE(v.salary_to, 0) as salary_to,
                    v.currency,
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                WHERE LOWER(v.vacancy_name) LIKE LOWER(%s)
                ORDER BY e.company_name, v.vacancy_name
            """
            self.cur.execute(query, (f"%{keyword}%",))
            return self.cur.fetchall()
        except Exception as e:
            print(f"❌ Ошибка при поиске вакансий по ключевому слову: {e}")
            return []

    def close(self):
        """Закрытие соединения с базой данных"""
        if hasattr(self, "cur"):
            self.cur.close()
        if hasattr(self, "conn"):
            self.conn.close()
        print("✅ Соединение с базой данных закрыто")
