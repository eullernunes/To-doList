from pydantic import BaseModel
from datetime import date


# mudar date pra date time
class Task(BaseModel):
    name: str
    description: str
    state: str
    date: str