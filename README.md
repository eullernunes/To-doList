# To-doList

API de tarefas com **FastAPI + JWT** e **front Streamlit**. Monorepo orquestrado com **docker-compose**.

---

##  Features
- Autenticação (criar conta / login) com **JWT Bearer**
- **Criar** e **listar** tarefas do usuário autenticado
- Banco **SQLite** com migrações via **Alembic**
- Docker por serviço (**API** e **Web**)

---

##  Variáveis de Ambiente (API)
Crie `services/api/.env`:
```env
SECRET_KEY=coloque-um-uuid-grande
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=sqlite:///./banco.db
```

---

##  Rodando com Docker (recomendado)
```bash
docker compose up --build
```
- API: <http://localhost:8000/docs> (Swagger) • <http://localhost:8000/redoc>
- Web: <http://localhost:5173>

O compose executa `alembic upgrade head` ao subir a API e usa hot-reload.

---

##  Fluxo rápido (UI)
1. Acesse `http://localhost:5173`
2. **Criar conta** → **Login**
3. **Criar tarefa** → veja em **Minhas tarefas**

---


##  Rodando local (sem Docker)

**API**
```bash
cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# criar .env conforme acima
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Web (Streamlit)**
```bash
cd services/web
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export API_BASE=http://127.0.0.1:8000
streamlit run app.py
```
