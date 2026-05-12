# Task Tracker — Distributed To-Do List

A distributed task management app built with Python, Flask, and TCP sockets. Multiple users can sign in and manage their own personal lists or collaborate on shared boards with a team.

---

## How it works

The system is split into three independent parts that talk to each other over the network:

- **Server.py** — the backend. Handles all the data, authentication, and logic. Listens on a TCP socket and processes JSON commands from any connected client.
- **WebApp.py** — a Flask web server that sits between the browser and the backend. It takes HTTP requests from the browser, translates them into socket messages, and sends back the response.
- **Client.py** — a command-line interface that connects directly to the backend server, bypassing the web app entirely.

Both the web interface and the CLI can run at the same time against the same server — which is kind of the whole point.

---

## Features

- Sign up and log in with hashed passwords (SHA-256)
- Personal lists — private, only visible to you
- Shared boards — create or join a board with a Project ID, collaborate with others
- Add, edit, delete, and mark tasks as done
- Priority levels (low, medium, high)
- All data saved to a JSON file so nothing is lost if the server restarts
- Thread-safe — multiple users can read and write at the same time without corrupting the data

---

## Distributed systems concepts in this project

| Concept | How we implemented it |
|---|---|
| Client-server model | Server.py handles both the web app and CLI as separate clients |
| 3-tier architecture | Browser → Flask app → backend server |
| Concurrency | A new thread is spawned for every connected user |
| Thread safety | Mutex lock prevents race conditions on the database file |
| Message passing | JSON payloads over raw TCP sockets |
| Persistence | State is written to todo_db.json after every change |
| Middleware | WebApp.py translates HTTP ↔ TCP |

---

## Files

```
├── Server.py        # core backend server
├── WebApp.py        # Flask middle tier
├── Client.py        # CLI client
├── templates/
│   ├── login.html
│   ├── signup.html
│   └── index.html
└── README.md
```

---

## How to run

Install Flask:
```bash
pip install flask
```

Start the backend:
```bash
python Server.py
```

Then either open the web interface:
```bash
python WebApp.py
# go to http://localhost:8080
```

Or use the CLI directly:
```bash
python Client.py
```

---

## Team

Nada Elsawy, Caren Moheb, Marvel Fady, Mohammed Tariq, Ahmed Ehab, Fredy George, Mazen Abdallah
