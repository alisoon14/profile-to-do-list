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

        while True:
            print("\nФильтр задач:")
            print("1. Все задачи")
            print("2. Только активные")
            print("3. Только выполненные")
            print("0. Вернуться в меню")
            
            filter_choice = input("Выберите действие (0-3): ").strip()
            
            if filter_choice == "0":
                break
                
            tasks_to_show = []
            if filter_choice == "1":
                tasks_to_show = self.tasks[user_email]
                print("\nВсе задачи:")
            elif filter_choice == "2":
                tasks_to_show = [task for task in self.tasks[user_email] if not task['completed']]
                print("\nАктивные задачи:")
            elif filter_choice == "3":
                tasks_to_show = [task for task in self.tasks[user_email] if task['completed']]
                print("\nВыполненные задачи:")
            else:
                print("Некорректный выбор, попробуйте еще раз.")
                continue

            if not tasks_to_show:
                print("Нет задач для отображения.")
                continue

            for i, task in enumerate(tasks_to_show, 1):
                status = "✓" if task['completed'] else "✗"
                print(f"{i}. [{status}] {task['text']} (добавлено: {task.get('created_at', 'неизвестно')})")

            print("\nВыберите действие:")
            print("1. Изменить статус задачи")
            print("2. Удалить задачу")
            print("0. Вернуться к фильтрам")
            
            action_choice = input().strip()
            
            if action_choice == "1":
                self._toggle_task_status(user_email, tasks_to_show)
            elif action_choice == "2":
                self._delete_task(user_email, tasks_to_show)
            elif action_choice == "0":
                continue
            else:
                print("Некорректный выбор.")

    def _toggle_task_status(self, user_email: str, tasks_to_show: List[Dict]):
        try:
            task_num = int(input("Введите номер задачи для изменения статуса: ").strip())
            if 1 <= task_num <= len(tasks_to_show):
                
                task_text = tasks_to_show[task_num - 1]['text']
                for task in self.tasks[user_email]:
                    if task['text'] == task_text:
                        task['completed'] = not task['completed']
                        self._save_tasks()
                        print(f"Статус задачи '{task['text']}' изменен на {'✓' if task['completed'] else '✗'}")
                        break
            else:
                print("Неверный номер задачи.")
        except ValueError:
            print("Пожалуйста, введите число.")

    def _delete_task(self, user_email: str, tasks_to_show: List[Dict]):
        try:
            task_num = int(input("Введите номер задачи для удаления: ").strip())
            if 1 <= task_num <= len(tasks_to_show):
                task_text = tasks_to_show[task_num - 1]['text']
                
                self.tasks[user_email] = [task for task in self.tasks[user_email] if task['text'] != task_text]
                self._save_tasks()
                print(f"Задача '{task_text}' удалена.")
            else:
                print("Неверный номер задачи.")
        except ValueError:
            print("Пожалуйста, введите число.")

    def _is_email_valid(self, email: str) -> bool:
        return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$", email) is not None

    def _is_phone_valid(self, phone: str) -> bool:
        return (re.match(r"^8\d{10}$", phone) is not None) or (re.match(r"^\+7\d{10}$", phone) is not None)

    def _is_password_valid(self, password: str) -> bool:
        return len(password) >= 5 and password.isalpha()

    def _is_name_valid(self, name: str) -> bool:
        return re.match(r"^[^!@#$%^&*()_+=-]*$", name) is not None


if __name__ == "__main__":
    manager = UserManagement()
    manager.start()