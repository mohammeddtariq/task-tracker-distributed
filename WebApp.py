from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import socket
import json

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this"

def talk_to_server(payload):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", 5555))
        client.send(json.dumps(payload).encode('utf-8'))
        response = client.recv(4096).decode('utf-8')
        client.close()
        return json.loads(response)
    except:
        return {"status": "error", "message": "Server offline"}

# ── AUTH ROUTES ──────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        
        list_type  = request.form.get('list_type', 'personal')
        shared_action = request.form.get('shared_action', 'create')
        if shared_action == 'create':
            project_id = request.form.get('create_project_id', '').strip().upper()
        else:
            project_id = request.form.get('join_project_id', '').strip().upper()

        if list_type not in ('personal', 'shared'):
            list_type = 'personal'
        if list_type == 'shared' and not project_id:
            return render_template('login.html', error="Please provide a Project ID for the Shared list")

        res = talk_to_server({
            "command":       "LOGIN",
            "username":      username,
            "password":      password,
            "list_type":     list_type,
            "project_id":    project_id if list_type == 'shared' else None,
            "shared_action": shared_action if list_type == 'shared' else None
        })
        if res["status"] == "success":
            session['username']   = username
            session['list_type']  = res.get("list_type", "personal")
            session['project_id'] = res.get("project_id")
            return redirect(url_for('home'))
        return render_template('login.html', error=res["message"])
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username   = request.form.get('username', '').strip()
        password   = request.form.get('password', '').strip()
        list_type  = request.form.get('list_type', 'personal')
        
        shared_action = request.form.get('shared_action', 'create')
        if shared_action == 'create':
            project_id = request.form.get('create_project_id', '').strip().upper()
        else:
            project_id = request.form.get('join_project_id', '').strip().upper()

        if list_type not in ('personal', 'shared'):
            list_type = 'personal'
        if not username or not password:
            return render_template('signup.html', error="All fields required")
        if list_type == 'shared' and not project_id:
            return render_template('signup.html', error="Please provide a Project ID for the Shared list")

        res = talk_to_server({
            "command":       "SIGNUP",
            "username":      username,
            "password":      password,
            "list_type":     list_type,
            "project_id":    project_id if list_type == 'shared' else None,
            "shared_action": shared_action if list_type == 'shared' else None
        })
        if res["status"] == "success":
            session['username']   = username
            session['list_type']  = list_type
            session['project_id'] = project_id if list_type == 'shared' else None
            return redirect(url_for('home'))
        return render_template('signup.html', error=res["message"])
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── TASK ROUTES ──────────────────────────────────────────────────────────────

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    list_type  = session.get('list_type', 'personal')
    project_id = session.get('project_id')
    data  = talk_to_server({
        "command":    "GET",
        "username":   session['username'],
        "list_type":  list_type,
        "project_id": project_id
    })
    tasks = data.get("data", [])
    return render_template('index.html',
                           tasks=tasks,
                           username=session['username'],
                           list_type=list_type,
                           project_id=project_id)

@app.route('/add', methods=['POST'])
def add():
    if 'username' not in session:
        return jsonify({"status": "error"}), 401
    task_text  = request.json.get('task')
    priority   = request.json.get('priority', 'med')
    list_type  = session.get('list_type', 'personal')
    project_id = session.get('project_id')
    res = talk_to_server({
        "command":    "ADD",
        "username":   session['username'],
        "list_type":  list_type,
        "project_id": project_id,
        "task":       task_text,
        "priority":   priority
    })
    return jsonify(res)

@app.route('/toggle', methods=['POST'])
def toggle():
    if 'username' not in session:
        return jsonify({"status": "error"}), 401
    list_type  = session.get('list_type', 'personal')
    project_id = session.get('project_id')
    res = talk_to_server({
        "command":    "TOGGLE",
        "username":   session['username'],
        "list_type":  list_type,
        "project_id": project_id,
        "id":         request.json.get('id')
    })
    return jsonify(res)

@app.route('/delete', methods=['POST'])
def delete():
    if 'username' not in session:
        return jsonify({"status": "error"}), 401
    list_type  = session.get('list_type', 'personal')
    project_id = session.get('project_id')
    res = talk_to_server({
        "command":    "DELETE",
        "username":   session['username'],
        "list_type":  list_type,
        "project_id": project_id,
        "id":         request.json.get('id')
    })
    return jsonify(res)

@app.route('/edit', methods=['POST'])
def edit():
    if 'username' not in session:
        return jsonify({"status": "error"}), 401
    list_type  = session.get('list_type', 'personal')
    project_id = session.get('project_id')
    res = talk_to_server({
        "command":    "EDIT",
        "username":   session['username'],
        "list_type":  list_type,
        "project_id": project_id,
        "id":         request.json.get('id'),
        "task":       request.json.get('task')
    })
    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True, port=8080)