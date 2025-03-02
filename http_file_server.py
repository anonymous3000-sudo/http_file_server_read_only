from flask import Flask, request, send_from_directory, render_template_string, abort
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
    <h1>Файловый менеджер - Текущая директория: /{{ current_path }}</h1>
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

if __name__ == '__main__':
    app.run(debug=True)
