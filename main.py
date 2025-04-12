import json
import os
import re
from typing import List, Dict

class UserManagement:
    def __init__(self):
        self.DB_FILE = "users.json"
        self.users: List[Dict[str, str]] = self._load_users()

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

    def _save_users(self):
        with open(self.DB_FILE, "w", encoding="utf-8") as file:
            json.dump(self.users, file, ensure_ascii=False, indent=4)

    def _get_valid_input(self, prompt: str, validator) -> str:
        while True:
            value = input(prompt).strip()
            if validator(value):
                return value
            print("Некорректный ввод. Попробуйте ещё раз.")

    def start(self):
        while True:
            print("\nВыберите действие:\n1. Регистрация\n2. Вход\n0. Выход")
            choice = input().strip()

            if choice == "1":
                self.sign_up()
            elif choice == "2":
                self.login()
            elif choice == "0":
                print("Выход из программы.")
                break
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
                return

        print("❌ Ошибка: Неверный email/телефон или пароль.")

    def _is_email_valid(self, email: str) -> bool:
        return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$", email) is not None

    def _is_phone_valid(self, phone: str) -> bool:
        return (re.match(r"^8\d{10}$", phone) is not None) or (re.match(r"^\+7\d{10}$", phone) is not None)

    def _is_password_valid(self, password: str) -> bool:
        return len(password) >= 5 and password.isalpha()

    def _is_name_valid(self, name: str) -> bool:
        return re.match(r"^[^!@#$%^&*()_+=-]*$", name) is not None

if __name__ == "__main__":
    UserManagement().start()