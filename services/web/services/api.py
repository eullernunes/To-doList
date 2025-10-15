import os
import httpx
from datetime import date
from typing import Any, Tuple

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

def _client(token: str | None = None) -> httpx.Client:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.Client(base_url=API_BASE, headers=headers, timeout=15.0)

def login(email: str, password: str) -> Tuple[bool, Any]:
    with _client() as c:
        r = c.post("/auth/login", json={"email": email, "password": password})
        if r.is_success:
            return True, r.json()["access_token"]
        return False, r.json().get("detail", r.text)

def signup(name: str, email: str, password: str) -> Tuple[bool, str]:
    with _client() as c:
        r = c.post("/auth/create_account", json={"name": name, "email": email, "password": password})
        if r.is_success:
            return True, "Usuário criado!"
        return False, r.json().get("detail", r.text)

def list_tasks(token: str) -> Tuple[bool, Any]:
    with _client(token) as c:
        r = c.get("/tasks/all")
        if r.is_success:
            return True, r.json().get("tasks", [])
        return False, r.json().get("detail", r.text)

def create_task(token: str, name: str, description: str, d: date) -> Tuple[bool, str]:
    with _client(token) as c:
        payload = {"name": name, "description": description, "date": d.isoformat()}
        r = c.post("/tasks/task", json=payload)
        if r.is_success:
            return True, "Tarefa criada!"
        return False, r.json().get("detail", r.text)

def update_task(token: str, task_id: int, *, name=None, description=None, d: date | None=None, state=None) -> Tuple[bool, str]:
    with _client(token) as c:
        data = {}
        if name is not None: data["name"] = name
        if description is not None: data["description"] = description
        if d is not None: data["date"] = d.isoformat()
        if state is not None: data["state"] = state
        r = c.patch(f"/tasks/{task_id}", json=data)
        if r.is_success:
            return True, "Tarefa atualizada!"
        return False, r.json().get("detail", r.text)

def delete_task(token: str, task_id: int) -> Tuple[bool, str]:
    with _client(token) as c:
        r = c.delete(f"/tasks/{task_id}")
        if r.is_success:
            return True, "Tarefa excluída!"
        return False, r.json().get("detail", r.text)
