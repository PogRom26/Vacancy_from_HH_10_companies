from src.database import Database
from src.db_manager import DBManager


def display_vacancies(vacancies, title):
    """Утилита для отображения списка вакансий"""
    if not vacancies:
        print(f"\n{title}: нет данных")
        return

    print(f"\n{title}:")
    print("-" * 80)
    for vacancy in vacancies:
        if len(vacancy) >= 6:  # Проверяем, что достаточно данных
            company, name, salary_from, salary_to, currency, url = vacancy[:6]

            salary_info = ""
            if salary_from or salary_to:
                if salary_from and salary_to and salary_from > 0 and salary_to > 0:
                    salary_info = f"{salary_from:,} - {salary_to:,} {currency}"
                elif salary_from and salary_from > 0:
                    salary_info = f"от {salary_from:,} {currency}"
                elif salary_to and salary_to > 0:
                    salary_info = f"до {salary_to:,} {currency}"
            else:
                salary_info = "не указана"

            print(f"🏢 {company}")
            print(f"   💼 {name}")
            print(f"   💰 Зарплата: {salary_info}")
            print(f"   🔗 {url}")
            print("-" * 80)


def main():
    print("🚀 Запуск проекта по сбору вакансий с HH.ru")

    try:
        # Создание и заполнение базы данных
        print("\n📊 Создание базы данных...")
        db = Database()
        db.create_database()

        print("\n👥 Заполнение данных о работодателях...")
        db.insert_employer_data()

        print("\n💼 Заполнение данных о вакансиях...")
        db.insert_vacancies_data()

        db.close()
        print("\n✅ База данных успешно создана и заполнена!")

        # Работа с данными через DBManager
        manager = DBManager()

        while True:
            print("\n" + "=" * 60)
            print("🎯 Меню работы с базой данных вакансий")
            print("=" * 60)
            print("1. 📈 Список компаний и количество вакансий")
            print("2. 📋 Список всех вакансий")
            print("3. 💵 Средняя зарплата по вакансиям")
            print("4. ⬆️ Вакансии с зарплатой выше средней")
            print("5. 🔍 Поиск вакансий по ключевому слову")
            print("0. ❌ Выход")

            choice = input("\n🎲 Выберите пункт меню: ").strip()

            if choice == "1":
                print("\n📊 Компании и количество вакансий:")
                companies = manager.get_companies_and_vacancies_count()
                if companies:
                    for company, count in companies:
                        print(f"   {company}: {count} вакансий")
                else:
                    print("   Нет данных о компаниях")

            elif choice == "2":
                vacancies = manager.get_all_vacancies()
                display_vacancies(vacancies, "Все вакансии")

            elif choice == "3":
                avg_salary = manager.get_avg_salary()
                print(f"\n💵 Средняя зарплата по вакансиям: {avg_salary:,} руб.")

            elif choice == "4":
                vacancies = manager.get_vacancies_with_higher_salary()
                display_vacancies(vacancies, "Вакансии с зарплатой выше средней")

            elif choice == "5":
                keyword = input("\n🔍 Введите ключевое слово для поиска: ").strip()
                if keyword:
                    vacancies = manager.get_vacancies_with_keyword(keyword)
                    display_vacancies(
                        vacancies, f"Результаты поиска по слову '{keyword}'"
                    )
                else:
                    print("⚠️ Пожалуйста, введите ключевое слово")

            elif choice == "0":
                print("\n👋 До свидания!")
                break
            else:
                print("⚠️ Неверный выбор. Попробуйте снова.")

        manager.close()

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("Проверьте настройки подключения к базе данных в файле .env")


if __name__ == "__main__":
    main()
