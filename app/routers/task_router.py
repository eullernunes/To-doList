from fastapi import APIRouter
from models.task_model import Task
from typing import List

task_router = APIRouter()

task_db: List[Task] = []

@task_router.post("/tasks/", response_model = Task)

def criar_task(task: Task):
    task_db.append(task)
    return task


@task_router.get("/tasks/", response_model = List[Task])

def listar_tasks():
    return task_db