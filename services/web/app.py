import os
import streamlit as st
import httpx
from datetime import date

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="To-doList", page_icon="📝", layout="centered")

if "token" not in st.session_state:
    st.session_state.token = None
if "email" not in st.session_state:
    st.session_state.email = ""

def client(token: str | None = None) -> httpx.Client:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.Client(base_url=API_BASE, headers=headers, timeout=15.0)

def login(email: str, password: str):
    with client() as c:
        r = c.post("/auth/login", json={"email": email, "password": password})
        if r.is_success:
            return True, r.json()["access_token"]
        return False, r.json().get("detail", r.text)

def signup(name: str, email: str, password: str):
    with client() as c:
        r = c.post("/auth/create_account", json={"name": name, "email": email, "password": password})
        if r.is_success:
            return True, "Usuário criado!"
        return False, r.json().get("detail", r.text)

def list_tasks(token: str):
    with client(token) as c:
        r = c.get("/tasks/all")
        if r.is_success:
            return True, r.json().get("tasks", [])
        return False, r.json().get("detail", r.text)

def create_task(token: str, name: str, description: str, d: date):
    with client(token) as c:
        payload = {"name": name, "description": description, "date": d.isoformat()}
        r = c.post("/tasks/task", json=payload)
        if r.is_success:
            return True, "Tarefa criada!"
        return False, r.json().get("detail", r.text)

st.title("📝 To-doList")

if not st.session_state.token:
    tab_login, tab_signup = st.tabs(["Entrar", "Criar conta"])

    with tab_login:
        with st.form("login"):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            ok = st.form_submit_button("Login")
        if ok:
            success, data = login(email.strip(), password)
            if success:
                st.session_state.token = data
                st.session_state.email = email.strip()
                st.success("Login OK")
                st.rerun()
            else:
                st.error(str(data))

    with tab_signup:
        with st.form("signup"):
            name = st.text_input("Nome")
            email2 = st.text_input("E-mail")
            password2 = st.text_input("Senha", type="password")
            ok2 = st.form_submit_button("Criar usuário")
        if ok2:
            if not name or not email2 or not password2:
                st.warning("Preencha todos os campos.")
            else:
                success, data = signup(name.strip(), email2.strip(), password2)
                if success:
                    st.success(str(data))
                else:
                    st.error(str(data))

else:
    col1, col2 = st.columns([1,1])
    with col1:
        st.caption(f"Logado: {st.session_state.email}")
    with col2:
        if st.button("Sair", use_container_width=True):
            st.session_state.token = None
            st.session_state.email = ""
            st.rerun()

    st.subheader("Criar tarefa")
    with st.form("create-task", clear_on_submit=True):
        name = st.text_input("Nome")
        d = st.date_input("Data", value=date.today(), format="YYYY-MM-DD")
        description = st.text_area("Descrição", height=100)
        submit = st.form_submit_button("Salvar")
    if submit:
        if not name.strip():
            st.warning("Informe um nome.")
        else:
            success, data = create_task(st.session_state.token, name.strip(), description.strip(), d)
            if success:
                st.success(str(data))
                st.rerun()
            else:
                st.error(str(data))

    st.subheader("Minhas tarefas")
    if st.button("Recarregar"):
        st.rerun()

    ok, data = list_tasks(st.session_state.token)
    if not ok:
        st.error(str(data))
    else:
        if not data:
            st.info("Nenhuma tarefa.")
        else:
            for t in data:
                with st.container(border=True):
                    st.markdown(f"**{t['name']}**")
                    st.caption(t.get("description") or "—")
                    st.text(f"Estado: {t.get('state') or 'PENDENTE'} | Data: {t.get('date') or '—'}")
