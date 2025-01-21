# app.py
from flask import Flask, render_template, request, jsonify, g
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Database setup
DATABASE = os.path.join(os.path.expanduser('~'), 'mysite', 'todo.db')
app.config['DATABASE'] = DATABASE

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                urgent BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/todos', methods=['GET'])
def get_todos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, task, completed, urgent, created_at
        FROM todos
        ORDER BY urgent DESC, created_at DESC
    ''')
    todos = [{'id': row[0],
              'task': row[1],
              'completed': bool(row[2]),
              'urgent': bool(row[3]),
              'created_at': row[4]} for row in cursor.fetchall()]
    return jsonify(todos)

@app.route('/api/todos', methods=['POST'])
def add_todo():
    task = request.json.get('task')
    urgent = request.json.get('urgent', False)

    if not task:
        return jsonify({'error': 'Task is required'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO todos (task, urgent) VALUES (?, ?)',
                  (task, urgent))
    db.commit()
    return jsonify({
        'id': cursor.lastrowid,
        'task': task,
        'completed': False,
        'urgent': urgent
    })

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    completed = request.json.get('completed')
    urgent = request.json.get('urgent')

    db = get_db()
    cursor = db.cursor()

    if completed is not None:
        cursor.execute('UPDATE todos SET completed = ? WHERE id = ?',
                      (completed, todo_id))

    if urgent is not None:
        cursor.execute('UPDATE todos SET urgent = ? WHERE id = ?',
                      (urgent, todo_id))

    db.commit()
    return jsonify({'success': True})

@app.route('/api/notes', methods=['GET'])
def get_notes():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, content, created_at
        FROM notes
        ORDER BY created_at DESC
    ''')
    notes = [{'id': row[0],
              'content': row[1],
              'created_at': row[2]} for row in cursor.fetchall()]
    return jsonify(notes)

@app.route('/api/notes', methods=['POST'])
def add_note():
    content = request.json.get('content')

    if not content:
        return jsonify({'error': 'Content is required'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO notes (content) VALUES (?)', (content,))
    db.commit()
    return jsonify({
        'id': cursor.lastrowid,
        'content': content,
        'created_at': datetime.now().isoformat()
    })

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    content = request.json.get('content')
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE notes SET content = ? WHERE id = ?', (content, note_id))
    db.commit()
    return jsonify({'success': True})

app.teardown_appcontext(close_db)

# Initialize the database when the app starts
init_db()

# This is for PythonAnywhere
application = app

if __name__ == '__main__':
    app.run()