from pydantic import BaseModel
from datetime import date

date.fromisoformat('2019-12-04')

class User(BaseModel):
    name: str
    email: str
    password: str



