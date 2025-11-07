from database import Database
from db_manager import DBManager


def main():
    # Создание и заполнение базы данных
    print("Создание базы данных...")
    db = Database()
    db.create_database()

    print("Заполнение данных о работодателях...")
    db.insert_employer_data()

    print("Заполнение данных о вакансиях...")
    db.insert_vacancies_data()

    db.close()
    print("База данных успешно создана и заполнена!")

    # Работа с данными через DBManager
    manager = DBManager()

    while True:
        print("\n" + "=" * 50)
        print("Меню работы с базой данных вакансий")
        print("=" * 50)
        print("1. Список компаний и количество вакансий")
        print("2. Список всех вакансий")
        print("3. Средняя зарплата по вакансиям")
        print("4. Вакансии с зарплатой выше средней")
        print("5. Поиск вакансий по ключевому слову")
        print("0. Выход")

        choice = input("\nВыберите пункт меню: ")

        if choice == "1":
            print("\nКомпании и количество вакансий:")
            companies = manager.get_companies_and_vacancies_count()
            for company, count in companies:
                print(f"{company}: {count} вакансий")

        elif choice == "2":
            print("\nВсе вакансии:")
            vacancies = manager.get_all_vacancies()
            for company, name, salary_from, salary_to, currency, url in vacancies:
                salary_info = ""
                if salary_from or salary_to:
                    if salary_from and salary_to:
                        salary_info = f"{salary_from} - {salary_to} {currency}"
                    elif salary_from:
                        salary_info = f"от {salary_from} {currency}"
                    else:
                        salary_info = f"до {salary_to} {currency}"
                else:
                    salary_info = "не указана"

                print(f"{company}: {name} | Зарплата: {salary_info} | {url}")

        elif choice == "3":
            avg_salary = manager.get_avg_salary()
            print(f"\nСредняя зарплата по вакансиям: {avg_salary} руб.")

        elif choice == "4":
            print("\nВакансии с зарплатой выше средней:")
            vacancies = manager.get_vacancies_with_higher_salary()
            for company, name, salary_from, salary_to, currency, url in vacancies:
                salary_info = f"{salary_from} - {salary_to} {currency}" if salary_from and salary_to else f"от {salary_from} {currency}" if salary_from else f"до {salary_to} {currency}"
                print(f"{company}: {name} | Зарплата: {salary_info} | {url}")

        elif choice == "5":
            keyword = input("Введите ключевое слово для поиска: ")
            vacancies = manager.get_vacancies_with_keyword(keyword)
            print(f"\nРезультаты поиска по слову '{keyword}':")
            for company, name, salary_from, salary_to, currency, url in vacancies:
                salary_info = ""
                if salary_from or salary_to:
                    if salary_from and salary_to:
                        salary_info = f"{salary_from} - {salary_to} {currency}"
                    elif salary_from:
                        salary_info = f"от {salary_from} {currency}"
                    else:
                        salary_info = f"до {salary_to} {currency}"
                else:
                    salary_info = "не указана"

                print(f"{company}: {name} | Зарплата: {salary_info} | {url}")

        elif choice == "0":
            break
        else:
            print("Неверный выбор. Попробуйте снова.")

    manager.close()
    print("Работа завершена!")


if __name__ == "__main__":
    main()