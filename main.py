import json
import os
import re
from typing import List, Dict, Union
from datetime import datetime

class UserManagement:
    def __init__(self):
        self.DB_FILE = "users.json"
        self.TASKS_FILE = "users_tasks.json"
        self.users: List[Dict[str, str]] = self._load_users()
        self.tasks: Dict[str, List[Dict[str, Union[str, bool]]]] = self._load_tasks()
        self.current_user: Union[Dict[str, str], None] = None

    def _load_users(self) -> List[Dict[str, str]]:
        if not os.path.exists(self.DB_FILE):
            with open(self.DB_FILE, "w", encoding="utf-8") as file:
                json.dump([], file)
            return []

        try:
            with open(self.DB_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _load_tasks(self) -> Dict[str, List[Dict[str, Union[str, bool]]]]:
        if not os.path.exists(self.TASKS_FILE):
            with open(self.TASKS_FILE, "w", encoding="utf-8") as file:
                json.dump({}, file)
            return {}

        try:
            with open(self.TASKS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_users(self):
        with open(self.DB_FILE, "w", encoding="utf-8") as file:
            json.dump(self.users, file, ensure_ascii=False, indent=4)

    def _save_tasks(self):
        with open(self.TASKS_FILE, "w", encoding="utf-8") as file:
            json.dump(self.tasks, file, ensure_ascii=False, indent=4)

    def _get_valid_input(self, prompt: str, validator) -> str:
        while True:
            value = input(prompt).strip()
            if validator(value):
                return value
            print("Некорректный ввод. Попробуйте ещё раз.")

    def start(self):
        while True:
            if self.current_user:
                self._show_user_menu()
            else:
                self._show_main_menu()

    def _show_main_menu(self):
        print("\nВыберите действие:\n1. Регистрация\n2. Вход\n0. Выход")
        choice = input().strip()

        if choice == "1":
            self.sign_up()
        elif choice == "2":
            self.login()
        elif choice == "0":
            print("Выход из программы.")
            exit()
        else:
            print("Некорректный выбор.")

    def _show_user_menu(self):
        print(f"\nДобро пожаловать, {self.current_user['name']}!")
        print("Выберите действие:")
        print("1. Добавить задачу")
        print("2. Показать мои задачи")
        print("3. Выйти из аккаунта")
        print("0. Выход из программы")
        
        choice = input().strip()
        
        if choice == "1":
            self.add_task()
        elif choice == "2":
            self.show_tasks()
        elif choice == "3":
            self.current_user = None
            print("Вы вышли из аккаунта.")
        elif choice == "0":
            print("Выход из программы.")
            exit()
        else:
            print("Некорректный выбор.")

    def sign_up(self):
        print("\nРегистрация")
        user = {
            "name": self._get_valid_input("Введите имя: ", self._is_name_valid),
            "email": self._get_valid_input("Введите email: ", self._is_email_valid),
            "phone": self._get_valid_input("Введите телефон: ", self._is_phone_valid),
            "password": self._get_valid_input("Введите пароль: ", self._is_password_valid),
        }

        if any(u["email"] == user["email"] for u in self.users):
            print("❌ Ошибка: Пользователь с таким email уже существует!")
            return
        if any(u["phone"] == user["phone"] for u in self.users):
            print("❌ Ошибка: Пользователь с таким телефоном уже существует!")
            return

        self.users.append(user)
        self._save_users()
        print("✅ Регистрация прошла успешно!")

    def login(self):
        print("\nВход в систему:")
        email_or_phone = input("Введите email или телефон: ").strip()
        password = input("Введите пароль: ").strip()

        for user in self.users:
            if (user["email"] == email_or_phone or user["phone"] == email_or_phone) and user["password"] == password:
                print(f"✅ Вход выполнен! Добро пожаловать, {user['name']}!")
                self.current_user = user
                # Создаем запись для задач, если ее нет
                if user['email'] not in self.tasks:
                    self.tasks[user['email']] = []
                    self._save_tasks()
                return

        print("❌ Ошибка: Неверный email/телефон или пароль.")

    def add_task(self):
        if not self.current_user:
            print("Ошибка: пользователь не авторизован")
            return

        print("\nДобавление новой задачи")
        task_text = input("Введите текст задачи: ").strip()
        
        if not task_text:
            print("Текст задачи не может быть пустым!")
            return
        
        new_task = {
            "text": task_text,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        user_email = self.current_user['email']
        if user_email not in self.tasks:
            self.tasks[user_email] = []
        
        self.tasks[user_email].append(new_task)
        self._save_tasks()
        print("✅ Задача успешно добавлена!")

    def show_tasks(self):
        if not self.current_user:
            print("Ошибка: пользователь не авторизован")
            return

        user_email = self.current_user['email']
        if user_email not in self.tasks or not self.tasks[user_email]:
            print("У вас пока нет задач.")
            return

        print("\nВаши задачи:")
        for i, task in enumerate(self.tasks[user_email], 1):
            status = "✓" if task['completed'] else "✗"
            print(f"{i}. [{status}] {task['text']} (добавлено: {task.get('created_at', 'неизвестно')})")

    def _is_email_valid(self, email: str) -> bool:
        return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$", email) is not None

    def _is_phone_valid(self, phone: str) -> bool:
        return (re.match(r"^8\d{10}$", phone) is not None) or (re.match(r"^\+7\d{10}$", phone) is not None)

    def _is_password_valid(self, password: str) -> bool:
        return len(password) >= 5 and password.isalpha()

    def _is_name_valid(self, name: str) -> bool:
        return re.match(r"^[^!@#$%^&*()_+=-]*$", name) is not None




