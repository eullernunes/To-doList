from app.models import db, User
from app.main import SECRET_KEY, ALGORITHM, oauth2_schema
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import sessionmaker, Session


def get_session():
    try:
        Session = sessionmaker(bind=db) #Cria conexão com o banco de dados
        session = Session() # Cria uma instância de conexão
        yield session # O yield faz a função retornar um valor mas não encerra a execução função
    finally: # O finally executa independente do resultado do try
        session.close()


def verify_token(token: str = Depends(oauth2_schema), session: Session = Depends(get_session)):
    try:
        dic_info = jwt.decode(token, SECRET_KEY, ALGORITHM)
        user_id = int(dic_info.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail = "Acesso Negado, verifique a validade do token")
    user = session.query(User).filter(User.id==user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail = "Acesso Inválido")
    return user