from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

DB_PATH = '/data/todos.db'
VERSION = os.environ.get('APP_VERSION', 'unknown')
ENV_COLOR = os.environ.get('ENV_COLOR', 'blue')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS todos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  task TEXT NOT NULL,
                  completed INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    todos = conn.execute('SELECT * FROM todos ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('index.html', todos=todos, version=VERSION, env_color=ENV_COLOR)

@app.route('/add', methods=['POST'])
def add_todo():
    task = request.form.get('task')
    if task:
        conn = get_db_connection()
        conn.execute('INSERT INTO todos (task) VALUES (?)', (task,))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/toggle/<int:todo_id>')
def toggle_todo(todo_id):
    conn = get_db_connection()
    todo = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
    if todo:
        new_status = 0 if todo['completed'] else 1
        conn.execute('UPDATE todos SET completed = ? WHERE id = ?', (new_status, todo_id))
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>')
def delete_todo(todo_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'version': VERSION, 'environment': ENV_COLOR}), 200

@app.route('/api/todos')
def api_todos():
    conn = get_db_connection()
    todos = conn.execute('SELECT * FROM todos ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in todos])

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
