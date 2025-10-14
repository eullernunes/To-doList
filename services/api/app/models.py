from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Date
from sqlalchemy.orm import declarative_base, relationship
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "banco.db")

#cria conexão com o banco
db = create_engine(f"sqlite:///{db_path}")

#cria a base do banco de dados
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column("id", Integer, primary_key = True, autoincrement = True)
    name = Column("name", String, nullable = False)
    email =  Column("email", String, nullable = False)
    password = Column("password", String, nullable = False)

    tasks = relationship("Task", back_populates="user")

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password


class Task(Base):
    __tablename__ = "tasks"

    id = Column("id", Integer, primary_key = True, autoincrement = True)
    name = Column("name", String, nullable = False)
    description = Column("description", String)
    state = Column("state", String)
    date = Column("date", Date, nullable = False)

    user_id = Column("user_id", Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="tasks")
    


    def __init__(self, name, description, user_id, date, state="PENDENTE"):
        self.name = name
        self.description = description
        self.user_id = user_id
        self.date = date
        self.state = state

