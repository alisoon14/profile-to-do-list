from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Union

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

DB_FILE = "users.json"
TASKS_FILE = "users_tasks.json"
TRASH_FILE = "users_trash.json"

class UserManager:
    def __init__(self):
        self.users = self._load_data(DB_FILE, default=[])
        self.tasks = self._load_data(TASKS_FILE)
        self.trash = self._load_data(TRASH_FILE)

    def _load_data(self, filename: str, default=None):
        if default is None:
            default = {} if filename != DB_FILE else []
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _save_data(self, data, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

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
        self._save_data(self.users, DB_FILE)
        return True

    def login_user(self, email_or_phone: str, password: str) -> Union[Dict[str, str], None]:
        for user in self.users:
            if (user["email"] == email_or_phone or user["phone"] == email_or_phone) and user["password"] == password:
                if user['email'] not in self.tasks:
                    self.tasks[user['email']] = []
                    self._save_data(self.tasks, TASKS_FILE)
                return user
        return None

    def add_task(self, email: str, task_text: str, due_date: str = None) -> bool:
        if not task_text:
            return False
            
        new_task = {
            "text": task_text,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "due_date": due_date  # Добавляем срок выполнения
        }
        
        if email not in self.tasks:
            self.tasks[email] = []
        
        self.tasks[email].append(new_task)
        self._save_data(self.tasks, TASKS_FILE)
        return True

    def is_task_urgent(self, task: Dict) -> bool:
        """Проверяет, является ли задача срочной (осталось <= 3 дня)"""
        if not task.get('due_date'):
            return False
        try:
            due_date = datetime.strptime(task['due_date'], "%Y-%m-%d")
            days_left = (due_date - datetime.now()).days
            return 0 <= days_left <= 3
        except:
            return False

    def is_task_overdue(self, task: Dict) -> bool:
        """Проверяет, просрочена ли задача"""
        if not task.get('due_date'):
            return False
        try:
            due_date = datetime.strptime(task['due_date'], "%Y-%m-%d")
            return (due_date - datetime.now()).days < 0
        except:
            return False

    def get_tasks(self, email: str, filter_type: str = "all") -> List[Dict]:
        if email not in self.tasks:
            return []
        
        if filter_type == "active":
            return [task for task in self.tasks[email] if not task['completed']]
        elif filter_type == "completed":
            return [task for task in self.tasks[email] if task['completed']]
        elif filter_type == "urgent":
            return [task for task in self.tasks[email] if not task['completed'] and 
               (self.is_task_urgent(task) or self.is_task_overdue(task))]
        elif filter_type == "overdue":
            return [task for task in self.tasks[email] if not task['completed'] and 
               self.is_task_overdue(task)]
        else:
            return self.tasks[email]

    def toggle_task_status(self, email: str, task_text: str) -> bool:
        for task in self.tasks.get(email, []):
            if task['text'] == task_text:
                task['completed'] = not task['completed']
                self._save_data(self.tasks, TASKS_FILE)
                return True
        return False

    def delete_task(self, email: str, task_text: str) -> bool:
        task_to_delete = None
        for task in self.tasks.get(email, []):
            if task['text'] == task_text:
                task_to_delete = task
                break
        
        if task_to_delete:
            self.tasks[email].remove(task_to_delete)
            if email not in self.trash:
                self.trash[email] = []
            self.trash[email].append(task_to_delete)
            self._save_data(self.tasks, TASKS_FILE)
            self._save_data(self.trash, TRASH_FILE)
            return True
        return False

    def restore_task(self, email: str, task_text: str) -> bool:
        task_to_restore = None
        for task in self.trash.get(email, []):
            if task['text'] == task_text:
                task_to_restore = task
                break
        
        if task_to_restore:
            self.trash[email].remove(task_to_restore)
            self.tasks[email].append(task_to_restore)
            self._save_data(self.tasks, TASKS_FILE)
            self._save_data(self.trash, TRASH_FILE)
            return True
        return False

    def empty_trash(self, email: str) -> bool:
        if email in self.trash and len(self.trash[email]) > 0:
            self.trash[email] = []
            self._save_data(self.trash, TRASH_FILE)
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
            session.setdefault('theme', 'light')
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
            due_date = request.form.get('due_date', '').strip()
            if task_text:
                if user_manager.add_task(email, task_text, due_date if due_date else None):
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
                flash('✅ Задача перемещена в корзину!', 'success')
            else:
                flash('❌ Ошибка при удалении задачи', 'error')
        
        return redirect(url_for('tasks', filter=filter_type))
    
    tasks = user_manager.get_tasks(email, filter_type)
    trash_count = len(user_manager.trash.get(email, []))
    return render_template('tasks.html', 
                         user=user, 
                         tasks=tasks, 
                         filter_type=filter_type,
                         trash_count=trash_count,
                         now=datetime.now(),
                         datetime=datetime)  

@app.route('/trash')
def trash():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session['user']
    trash_tasks = user_manager.trash.get(user['email'], [])
    return render_template('trash.html', user=user, tasks=trash_tasks)

@app.route('/restore_task', methods=['POST'])
def restore_task():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session['user']
    task_text = request.form['task_text']
    if user_manager.restore_task(user['email'], task_text):
        flash('✅ Задача восстановлена!', 'success')
    else:
        flash('❌ Ошибка восстановления', 'error')
    return redirect(url_for('trash'))

@app.route('/empty_trash', methods=['POST'])
def empty_trash():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session['user']
    if user_manager.empty_trash(user['email']):
        flash('🗑️ Корзина очищена!', 'success')
    else:
        flash('ℹ️ Корзина уже пуста', 'info')
    return redirect(url_for('trash'))

@app.route('/toggle_theme')
def toggle_theme():
    current_theme = session.get('theme', 'light')
    session['theme'] = 'dark' if current_theme == 'light' else 'light'
    return redirect(request.referrer or url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    for file in [DB_FILE, TASKS_FILE, TRASH_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                if file == DB_FILE:
                    json.dump([], f)
                else:
                    json.dump({}, f)
    app.run(debug=True)