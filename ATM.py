import sqlite3
import hashlib
import os

def md5sum(value):
    return hashlib.md5(value.encode()).hexdigest()

def init_db():
    db_exists = os.path.exists("atm.db")
    with sqlite3.connect("atm.db") as db:
        cursor = db.cursor()
        
        
        if db_exists:
            print("База данных уже существует.")
        else:
            print("Создание новой базы данных.")
        

        cursor.execute("DROP TABLE client")


        # Создаем таблицу client с колонкой balance
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS client(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER CHECK(age >= 0),
            sex INTEGER CHECK(sex IN (0, 1)) NOT NULL DEFAULT 1,
            number TEXT UNIQUE NOT NULL,
            pin TEXT NOT NULL,
            balance BIGINT NOT NULL DEFAULT 0
        );
        """)
        
        # Создаем таблицу bank
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank(
            name TEXT PRIMARY KEY,
            description TEXT,
            balance BIGINT NOT NULL DEFAULT 10000
        );
        """)
        
        # Вставляем данные в таблицу bank, если они еще не существуют
        cursor.execute("""
        INSERT OR IGNORE INTO bank (name, description, balance) VALUES 
        ('Main Bank', 'Главный банк системы', 10000);
        """)
        
        db.commit()
        print("Таблицы созданы или уже существуют.")

def registration():
    name = input("Ваше имя: ").strip()
    age = input("Сколько вам лет: ").strip()
    if not age.isdigit() or int(age) < 0:
        print("Некорректный возраст.")
        return

    sex = input("Вы мужчина (1) или женщина (0): ").strip()
    if sex not in ('0', '1'):
        print("Некорректный ввод.")
        return
    
    number = input("Введите номер телефона: ").strip()
    if not number.isdigit() or len(number) < 10:
        print("Некорректный номер телефона.")
        return
    
    pin = input("Придумайте PIN (4 цифры): ").strip()
    if not pin.isdigit() or len(pin) != 4:
        print("PIN-код должен состоять из 4 цифр.")
        return
    
    try:
        db = sqlite3.connect('atm.db')
        cursor = db.cursor()
        db.create_function("md5", 1, md5sum)

        cursor.execute("SELECT number FROM client WHERE number = ?", [number])
        if cursor.fetchone():
            print("Этот номер уже зарегистрирован.")
        else:
            cursor.execute(
                "INSERT INTO client(name, age, sex, number, pin, balance) VALUES(?,?,?,?, md5(?), 0)",
                (name, int(age), int(sex), number, pin)
            )
            db.commit()
            print("Регистрация прошла успешно!")
    except sqlite3.Error as e:
        print("Ошибка:", e)
    finally:
        cursor.close()
        db.close()

def log_in():
    number = input("Введите номер телефона: ").strip()
    pin = input("Введите PIN-код: ").strip()

    if not number.isdigit() or not pin.isdigit() or len(pin) != 4:
        print("Неверный формат ввода.")
        return

    try:
        db = sqlite3.connect('atm.db')
        cursor = db.cursor()
        db.create_function("md5", 1, md5sum)

        cursor.execute("SELECT id FROM client WHERE number = ?", [number])
        user = cursor.fetchone()
        if not user:
            print("Этот номер не зарегистрирован.")
            return

        cursor.execute("SELECT id FROM client WHERE number = ? AND pin = md5(?)", [number, pin])
        if cursor.fetchone():
            print("Вход выполнен.")
            give(number)
        else:
            print("Неверный PIN-код.")
    except sqlite3.Error as e:
        print("Ошибка:", e)
    finally:
        cursor.close()
        db.close()

def check_balance(number):
    try:
        db = sqlite3.connect('atm.db')
        cursor = db.cursor()

        # Отладочное сообщение: проверяем, какие колонки есть в таблице client
        cursor.execute("PRAGMA table_info(client)")
        columns = cursor.fetchall()
        print("Колонки в таблице client:", columns)

        cursor.execute("SELECT balance FROM client WHERE number = ?", [number])
        balance = cursor.fetchone()

        if balance is not None:
            print(f"Ваш баланс: {balance[0]} грн.")
        else:
            print("Ошибка: клиент не найден.")
    except sqlite3.Error as e:
        print("Ошибка:", e)
    finally:
        cursor.close()
        db.close()

def give(number):
    print("\nBANKDyTsKwOlE")
    
    try:
        db = sqlite3.connect('atm.db')
        cursor = db.cursor()

        cursor.execute("SELECT age FROM client WHERE number = ?", [number])
        user_age = cursor.fetchone()
        if not user_age or user_age[0] < 14:
            print("Вам недостаточно лет для использования банка.")
            return

        while True:
            action = input("\nВыберите действие:\n1. Посмотреть баланс\n2. Внести деньги\n3. Снять деньги\n4. Выйти\nВаш выбор: ").strip()

            if action == "1":
                check_balance(number)

            elif action == "2":
                amount = input("Введите сумму для пополнения: ").strip()
                if not amount.isdigit() or int(amount) < 500:
                    print("Минимальная сумма пополнения — 500 грн.")
                    continue

                amount = int(amount)
                cursor.execute("UPDATE client SET balance = balance + ? WHERE number = ?", [amount, number])
                cursor.execute("UPDATE bank SET balance = balance + ? WHERE name = 'Main Bank'", [amount])
                db.commit()
                print(f"Вы внесли {amount} грн на свой счет.")
                check_balance(number)

            elif action == "3":
                amount = input("Введите сумму для снятия: ").strip()
                if not amount.isdigit() or int(amount) <= 0:
                    print("Некорректная сумма.")
                    continue
                
                amount = int(amount)
                cursor.execute("SELECT balance FROM client WHERE number = ?", [number])
                user_balance = cursor.fetchone()[0]

                if amount > user_balance:
                    print("Недостаточно средств на вашем счете.")
                    continue

                commission = int(amount * 0.02)  # Комиссия 2%
                total_amount = amount + commission  # Сумма списания

                cursor.execute("UPDATE client SET balance = balance - ? WHERE number = ?", [total_amount, number])
                cursor.execute("UPDATE bank SET balance = balance + ? WHERE name = 'Main Bank'", [commission])
                db.commit()

                print(f"Вы сняли {amount} грн.")
                print(f"Комиссия составила {commission} грн.")
                print(f"Итоговая сумма списания: {total_amount} грн.")
                
                check_balance(number)

            elif action == "4":
                print("Выход в главное меню.")
                break
            else:
                print("Некорректный выбор, попробуйте снова.")

    except sqlite3.Error as e:
        print("Ошибка:", e)
    finally:
        cursor.close()
        db.close()

def view_balance_by_number():
    number = input("Введите номер телефона клиента: ").strip()
    if not number.isdigit() or len(number) < 10:
        print("Некорректный номер телефона.")
        return

    try:
        db = sqlite3.connect('atm.db')
        cursor = db.cursor()

        cursor.execute("SELECT balance FROM client WHERE number = ?", [number])
        balance = cursor.fetchone()

        if balance is not None:
            print(f"Баланс клиента с номером {number}: {balance[0]} грн.")
        else:
            print("Клиент с таким номером не найден.")
    except sqlite3.Error as e:
        print("Ошибка:", e)
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    init_db()
    while True:
        choice = input("\n1. Регистрация\n2. Вход\n3. Просмотр баланса по номеру\n4. Выход\nВыберите действие: ").strip()
        if choice == "1":
            registration()
        elif choice == "2":
            log_in()
        elif choice == "3":
            view_balance_by_number()
        elif choice == "4":
            print("Выход из программы.")
            break
        else:
            print("Неверный выбор.")