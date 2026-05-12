import socket
import threading
import json
import os
import hashlib
import secrets
import time

DB_FILE = "todo_db.json"
list_lock = threading.Lock()

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "tasks": []}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_visible_tasks(tasks, username, list_type, project_id=None):
    """Return tasks visible to the user based on their list type and project ID."""
    if list_type == "personal":
        # Strictly private: only tasks the user owns that are personal
        return [t for t in tasks
                if t.get("owner") == username and t.get("list_type") == "personal"]
    else:
        # Shared: only tasks belonging to the exact same project_id
        return [t for t in tasks
                if t.get("list_type") == "shared" and t.get("project_id") == project_id]

def handle_client(client_socket):
    while True:
        try:
            request_data = client_socket.recv(4096).decode('utf-8')
            if not request_data:
                break

            request = json.loads(request_data)
            command = request.get("command")

            with list_lock:
                db = load_db()
                users = db["users"]
                tasks = db["tasks"]

                # ── AUTH COMMANDS ────────────────────────────────────────────
                if command == "SIGNUP":
                    username   = request.get("username")
                    password   = request.get("password")
                    list_type  = request.get("list_type", "personal")
                    project_id = request.get("project_id")
                    project_id = project_id.strip().upper() if project_id else ""
                    shared_action = request.get("shared_action", "create")

                    if list_type not in ("personal", "shared"):
                        list_type = "personal"

                    # Get all existing project IDs from users and tasks
                    existing_ids = {u.get("project_id") for u in users.values() if u.get("project_id")}
                    existing_ids.update({t.get("project_id") for t in tasks if t.get("project_id")})

                    if list_type == "shared" and not project_id:
                        response = {"status": "error", "message": "A Project ID is required for Shared lists"}
                    elif list_type == "shared" and shared_action == "join" and project_id not in existing_ids:
                        response = {"status": "error", "message": "Project ID not found. Please check the ID and try again."}
                    elif list_type == "shared" and shared_action == "create" and project_id in existing_ids:
                        response = {"status": "error", "message": "Project ID already exists. Please pick a different one."}
                    elif username in users:
                        response = {"status": "error", "message": "Username already exists"}
                    else:
                        user_record = {
                            "password":   hash_password(password),
                            "list_type":  list_type,
                            "project_id": project_id if list_type == "shared" else None
                        }
                        users[username] = user_record
                        save_db(db)
                        response = {
                            "status":     "success",
                            "message":    "Account created",
                            "list_type":  list_type,
                            "project_id": project_id if list_type == "shared" else None
                        }

                elif command == "LOGIN":
                    username = request.get("username")
                    password = request.get("password")
                    user     = users.get(username)
                    
                    list_type  = request.get("list_type", "personal")
                    project_id = request.get("project_id")
                    project_id = project_id.strip().upper() if project_id else ""
                    shared_action = request.get("shared_action", "create")

                    if user and user["password"] == hash_password(password):
                        if list_type not in ("personal", "shared"):
                            list_type = "personal"

                        existing_ids = {u.get("project_id") for u in users.values() if u.get("project_id")}
                        existing_ids.update({t.get("project_id") for t in tasks if t.get("project_id")})

                        if list_type == "shared" and not project_id:
                            response = {"status": "error", "message": "A Project ID is required for Shared lists"}
                        elif list_type == "shared" and shared_action == "join" and project_id not in existing_ids:
                            response = {"status": "error", "message": "Project ID not found. Please check the ID and try again."}
                        elif list_type == "shared" and shared_action == "create" and project_id in existing_ids:
                            response = {"status": "error", "message": "Project ID already exists. Please pick a different one."}
                        else:
                            # CRITICAL FIX: Only update project_id if they log into a shared board.
                            # If they log into personal, DO NOT overwrite their project_id with None.
                            # This allows the user to have both a personal list and a shared list simultaneously!
                            if list_type == "shared":
                                user["project_id"] = project_id
                            
                            user["list_type"] = list_type
                            save_db(db)

                            response = {
                                "status":     "success",
                                "message":    "Logged in",
                                "list_type":  list_type,  # Return the list_type they selected on the login page!
                                "project_id": project_id if list_type == "shared" else None
                            }
                    else:
                        response = {"status": "error", "message": "Invalid username or password"}

                # ── TASK COMMANDS ────────────────────────────────────────────
                elif command == "GET":
                    username   = request.get("username")
                    list_type  = request.get("list_type", "personal")
                    project_id = request.get("project_id")
                    visible    = get_visible_tasks(tasks, username, list_type, project_id)
                    response   = {"status": "success", "data": visible}

                elif command == "ADD":
                    username   = request.get("username")
                    list_type  = request.get("list_type", "personal")
                    project_id = request.get("project_id")
                    task_text  = request.get("task")
                    priority   = request.get("priority", "med")
                    task = {
                        "id":         secrets.token_hex(8),
                        "text":       task_text,
                        "owner":      username,
                        "list_type":  list_type,
                        "project_id": project_id if list_type == "shared" else None,
                        "priority":   priority,
                        "done":       False,
                        "ts":         int(time.time())
                    }
                    tasks.insert(0, task)
                    save_db(db)
                    visible  = get_visible_tasks(tasks, username, list_type, project_id)
                    response = {"status": "success", "data": visible}

                elif command == "TOGGLE":
                    task_id    = request.get("id")
                    username   = request.get("username")
                    list_type  = request.get("list_type", "personal")
                    project_id = request.get("project_id")
                    task = next((t for t in tasks if t["id"] == task_id), None)
                    if not task:
                        response = {"status": "error", "message": "Task not found"}
                    elif task["owner"] != username:
                        response = {"status": "error", "message": "Not your task"}
                    else:
                        task["done"] = not task["done"]
                        save_db(db)
                        visible  = get_visible_tasks(tasks, username, list_type, project_id)
                        response = {"status": "success", "data": visible}

                elif command == "DELETE":
                    task_id    = request.get("id")
                    username   = request.get("username")
                    list_type  = request.get("list_type", "personal")
                    project_id = request.get("project_id")
                    task = next((t for t in tasks if t["id"] == task_id), None)
                    if not task:
                        response = {"status": "error", "message": "Task not found"}
                    elif task["owner"] != username:
                        response = {"status": "error", "message": "Not your task"}
                    else:
                        tasks.remove(task)
                        save_db(db)
                        visible  = get_visible_tasks(tasks, username, list_type, project_id)
                        response = {"status": "success", "data": visible}

                elif command == "EDIT":
                    task_id    = request.get("id")
                    new_text   = request.get("task")
                    username   = request.get("username")
                    list_type  = request.get("list_type", "personal")
                    project_id = request.get("project_id")
                    task = next((t for t in tasks if t["id"] == task_id), None)
                    if not task:
                        response = {"status": "error", "message": "Task not found"}
                    elif task["owner"] != username:
                        response = {"status": "error", "message": "Not your task"}
                    else:
                        task["text"] = new_text
                        save_db(db)
                        visible  = get_visible_tasks(tasks, username, list_type, project_id)
                        response = {"status": "success", "data": visible}

                else:
                    response = {"status": "error", "message": "Unknown command"}

            client_socket.send(json.dumps(response).encode('utf-8'))

        except Exception as e:
            print(f"Client error: {e}")
            break

    client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 5555))
    server.listen(5)
    print("Server listening on port 5555...")
    while True:
        client, addr = server.accept()
        print(f"Connected: {addr}")
        threading.Thread(target=handle_client, args=(client,)).start()

if __name__ == "__main__":
    start_server()