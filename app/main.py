from fastapi import FastAPI
from routers.task_router import task_router
#from routers.user_router import user_router


app = FastAPI()


app.include_router(task_router)
#app.include_router(user_router)
