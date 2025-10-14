from pydantic import BaseModel
from datetime import date as DateType
from typing import Optional

class UserSchema(BaseModel):
    name: str
    email: str
    password: str

    class Config:
        from_attributes = True

class TaskSchema(BaseModel):
    name: str
    description: str
    date: DateType

    class Config:
        from_attributes = True

class TaskUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    state: Optional[str] = None
    date: Optional[DateType] = None

class LoginSchema(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True
