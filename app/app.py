from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Union

app = Flask(__name__)

DB_FILE = "users.json"
TASKS_FILE = "users_tasks.json"

class UserManager:
    def __init__(self):
        self.users: List[Dict[str, str]] = self._load_users()
        self.tasks: Dict[str, List[Dict[str, Union[str, bool]]]] = self._load_tasks()

    def _load_users(self) -> List[Dict[str, str]]:
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w", encoding="utf-8") as file:
                json.dump([], file)
            return []
        try:
            with open(DB_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _load_tasks(self) -> Dict[str, List[Dict[str, Union[str, bool]]]]:
        if not os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "w", encoding="utf-8") as file:
                json.dump({}, file)
            return {}
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_users(self):
        with open(DB_FILE, "w", encoding="utf-8") as file:
            json.dump(self.users, file, ensure_ascii=False, indent=4)

    def _save_tasks(self):
        with open(TASKS_FILE, "w", encoding="utf-8") as file:
            json.dump(self.tasks, file, ensure_ascii=False, indent=4)

    def _is_email_valid(self, email: str) -> bool:
        return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$", email) is not None

    def _is_phone_valid(self, phone: str) -> bool:
        return (re.match(r"^8\d{10}$", phone) is not None) or (re.match(r"^\+7\d{10}$", phone) is not None)

    def _is_password_valid(self, password: str) -> bool:
        return len(password) >= 5 and password.isalpha()

    def _is_name_valid(self, name: str) -> bool:
        return re.match(r"^[^!@#$%^&*()_+=-]*$", name) is not None

    def register_user(self, user_data: Dict[str, str]) -> bool:
        if not all([
            self._is_name_valid(user_data["name"]),
            self._is_email_valid(user_data["email"]),
            self._is_phone_valid(user_data["phone"]),
            self._is_password_valid(user_data["password"])
        ]):
            return False

        if any(u["email"] == user_data["email"] for u in self.users):
            return False
        if any(u["phone"] == user_data["phone"] for u in self.users):
            return False

        self.users.append(user_data)
        self._save_users()
        return True

    def login_user(self, email_or_phone: str, password: str) -> Union[Dict[str, str], None]:
        for user in self.users:
            if (user["email"] == email_or_phone or user["phone"] == email_or_phone) and user["password"] == password:
                if user['email'] not in self.tasks:
                    self.tasks[user['email']] = []
                    self._save_tasks()
                return user
        return None

    def add_task(self, email: str, task_text: str) -> bool:
        if not task_text:
            return False
            
        new_task = {
            "text": task_text,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if email not in self.tasks:
            self.tasks[email] = []
        
        self.tasks[email].append(new_task)
        self._save_tasks()
        return True

    def get_tasks(self, email: str, filter_type: str = "all") -> List[Dict]:
        if email not in self.tasks:
            return []
            
        if filter_type == "active":
            return [task for task in self.tasks[email] if not task['completed']]
        elif filter_type == "completed":
            return [task for task in self.tasks[email] if task['completed']]
        else:
            return self.tasks[email]

    def toggle_task_status(self, email: str, task_text: str) -> bool:
        for task in self.tasks.get(email, []):
            if task['text'] == task_text:
                task['completed'] = not task['completed']
                self._save_tasks()
                return True
        return False

    def delete_task(self, email: str, task_text: str) -> bool:
        if email in self.tasks:
            self.tasks[email] = [task for task in self.tasks[email] if task['text'] != task_text]
            self._save_tasks()
            return True
        return False

user_manager = UserManager()

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('tasks'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_data = {
            "name": request.form['name'].strip(),
            "email": request.form['email'].strip(),
            "phone": request.form['phone'].strip(),
            "password": request.form['password'].strip()
        }

        if user_manager.register_user(user_data):
            flash('✅ Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        else:
            flash('❌ Ошибка регистрации. Проверьте введенные данные или попробуйте другой email/телефон.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_phone = request.form['email_or_phone'].strip()
        password = request.form['password'].strip()

        user = user_manager.login_user(email_or_phone, password)
        if user:
            session['user'] = user
            flash(f'✅ Вход выполнен! Добро пожаловать, {user["name"]}!', 'success')
            return redirect(url_for('tasks'))
        else:
            flash('❌ Ошибка: Неверный email/телефон или пароль.', 'error')
    
    return render_template('login.html')

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'user' not in session:
        flash('Пожалуйста, войдите в систему для просмотра задач.', 'warning')
        return redirect(url_for('login'))
    
    user = session['user']
    email = user['email']
    filter_type = request.args.get('filter', 'all')
    
    if request.method == 'POST':
        if 'task_text' in request.form:
            task_text = request.form['task_text'].strip()
            if task_text:
                if user_manager.add_task(email, task_text):
                    flash('✅ Задача успешно добавлена!', 'success')
                else:
                    flash('❌ Ошибка при добавлении задачи', 'error')
        elif 'toggle_task' in request.form:
            task_text = request.form['toggle_task']
            if user_manager.toggle_task_status(email, task_text):
                flash('✅ Статус задачи изменен!', 'success')
            else:
                flash('❌ Ошибка при изменении статуса задачи', 'error')
        elif 'delete_task' in request.form:
            task_text = request.form['delete_task']
            if user_manager.delete_task(email, task_text):
                flash('✅ Задача удалена!', 'success')
            else:
                flash('❌ Ошибка при удалении задачи', 'error')
        
        return redirect(url_for('tasks', filter=filter_type))
    
    tasks = user_manager.get_tasks(email, filter_type)
    return render_template('tasks.html', user=user, tasks=tasks, filter_type=filter_type)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)