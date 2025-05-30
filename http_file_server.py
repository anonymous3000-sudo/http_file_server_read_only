from flask import Flask, request, send_from_directory, render_template_string, abort, redirect, url_for
import os
import sys
from werkzeug.security import safe_join
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]

@auth.verify_password
def verify_password(username, password):
    if username == USERNAME and password == PASSWORD:
        return True
    return False

ROOT_DIR = os.path.abspath('.')

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Файловый менеджер</title>
</head>
<body>
    <h1>Файловый менеджер - Содержимое директории: /{{ current_path }}</h1>
    <ul>
        {% if parent_path %}
            <li><a href="/?path={{ parent_path }}">.. (вверх)</a></li>
        {% endif %}
        {% for file in files %}
            <li>
                {% if file.is_dir %}
                    <a href="/?path={{ file.path }}">{{ file.name }}/</a>
                {% else %}
                    <a href="/download?path={{ file.path }}">{{ file.name }}</a>
                {% endif %}
            </li>
        {% endfor %}
    </ul>
    <hr>
    <!-- Форма загрузки файла -->
    <h3>Загрузить файл</h3>
    <form method="post" action="/upload" enctype="multipart/form-data">
        <input type="hidden" name="path" value="{{ current_path }}">
        <input type="file" name="file" required>
        <button type="submit">Add file</button>
    </form>
    <!-- Форма создания новой папки -->
    <h3>Создать папку</h3>
    <form method="post" action="/mkdir">
        <input type="hidden" name="path" value="{{ current_path }}">
        <input type="text" name="folder" placeholder="Название папки" required>
        <button type="submit">Add path</button>
    </form>
</body>
</html>
'''

@app.route('/')
@auth.login_required
def index():
    path = request.args.get('path', '')
    abs_path = safe_join(ROOT_DIR, path)
    if abs_path is None or not os.path.exists(abs_path):
        abort(404)

    if os.path.isfile(abs_path):
        return send_from_directory(os.path.dirname(abs_path), os.path.basename(abs_path), as_attachment=True)

    items = []
    with os.scandir(abs_path) as it:
        for entry in it:
            items.append({
                'name': entry.name,
                'path': os.path.join(path, entry.name),
                'is_dir': entry.is_dir()
            })

    parent_path = os.path.dirname(path) if path else ''
    return render_template_string(TEMPLATE, files=items, current_path=path, parent_path=parent_path)

@app.route('/download')
@auth.login_required
def download():
    path = request.args.get('path', '')
    abs_path = safe_join(ROOT_DIR, path)
    if abs_path is None or not os.path.exists(abs_path) or os.path.isdir(abs_path):
        abort(404)
    return send_from_directory(os.path.dirname(abs_path), os.path.basename(abs_path), as_attachment=True)

@app.route('/upload', methods=['POST'])
@auth.login_required
def upload():
    path = request.form.get('path', '')
    abs_path = safe_join(ROOT_DIR, path)
    if abs_path is None or not os.path.isdir(abs_path):
        abort(404)
    file = request.files.get('file')
    if not file:
        abort(400)
    filename = file.filename
    # Сохраняем файл в текущую директорию
    file.save(os.path.join(abs_path, filename))
    return redirect(url_for('index', path=path))

@app.route('/mkdir', methods=['POST'])
@auth.login_required
def mkdir():
    path = request.form.get('path', '')
    folder_name = request.form.get('folder', '')
    abs_path = safe_join(ROOT_DIR, path)
    if abs_path is None or not os.path.isdir(abs_path):
        abort(404)
    new_folder_path = safe_join(abs_path, folder_name)
    try:
        os.mkdir(new_folder_path)
    except Exception as e:
        abort(400, description=str(e))
    return redirect(url_for('index', path=path))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
