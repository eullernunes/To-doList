from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import TaskSchema, TaskUpdateSchema
from dependencies import get_session, verify_token
from models import Task, User

task_router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(verify_token)])


@task_router.get("/")
async def tasks():
    """
    Essa é a rota padrão de tarefas do sistema. Todas as rotas de tarefas precisam de autenticação
    """
    return {"mensagem": "Você acessou a rota de tasks"}


@task_router.post("/task")
async def create_task(task_schema: TaskSchema, session: Session = Depends(get_session), user: User = Depends(verify_token)):

    new_task = Task(
        name = task_schema.name, 
        description= task_schema.description, 
        user_id = user.id, 
        date=task_schema.date
    )
    
    session.add(new_task)
    session.commit()
    return{"mensagem": "Tarefa criada com sucesso"}

@task_router.get("/all")
async def list_my_tasks(session: Session = Depends(get_session),user: User = Depends(verify_token)):

    my_tasks = session.query(Task).filter(Task.user_id==user.id).all()

    return {
        "mensagem": "Lista de tarefas do usuário",
        "total": len(my_tasks), 
        "tasks": [
            {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "state": task.state,
                "date": task.date.isoformat() if task.date else None
            } 
            for task in my_tasks
        ],
    }

@task_router.patch("/{task_id}")
async def update_task(task_id: int, task_schema: TaskUpdateSchema, session: Session = Depends(get_session), user: User = Depends(verify_token)):
    
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    if task.user_id != user.id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para alterar esta task")
    
    # O usuário pode mandr qualquer combinação dos campos do schema TaskUpdateSchema
    # por isso usei exclude_unset=True para pegar apenas os campos que vieram na requisição
    # O data = task_schema.model_dump(exclude_unset=True) cria um dicionário com os campos que vieram na requisição
    data = task_schema.model_dump(exclude_unset=True)

    #Aqui percorre cada par (campo, valor) do dicionário e atualiza o atributo do objeto task com o valor correspondente
    for field, value in data.items():
        setattr(task, field, value)

    session.commit()
    session.refresh(task)

    return {
        "mensagem": "Tarefa atualizada com sucesso",
        "task": {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "state": task.state,
            "date": task.date.isoformat() if task.date else None  
        },
    }

@task_router.delete("/{task_id}")
async def delete_task(task_id: int, session: Session = Depends(get_session), user: User = Depends(verify_token)):
    
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    if task.user_id != user.id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para deletar esta task")
    
    session.delete(task)
    session.commit()

    return {"mensagem": "Tarefa deletada com sucesso"}
