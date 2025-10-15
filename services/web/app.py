import os
import streamlit as st
import httpx
from datetime import date, datetime

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="To-doList", page_icon="📝", layout="centered")

# ---- session state ----
if "token" not in st.session_state:
    st.session_state.token = None
if "email" not in st.session_state:
    st.session_state.email = ""
if "show_create" not in st.session_state:
    st.session_state.show_create = False
if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None
if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None
if "confirm_delete_name" not in st.session_state:
    st.session_state.confirm_delete_name = ""
if "_create_defaults" not in st.session_state:
    st.session_state._create_defaults = {"name": "", "description": "", "date": date.today()}

# detecção de suporte a st.dialog (Streamlit 1.31+)
HAS_DIALOG = hasattr(st, "dialog")

# ---- http client / API ----
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

def update_task(token: str, task_id: int, *, name=None, description=None, d: date | None=None, state=None):
    with client(token) as c:
        data = {}
        if name is not None: data["name"] = name
        if description is not None: data["description"] = description
        if d is not None: data["date"] = d.isoformat()
        if state is not None: data["state"] = state
        r = c.patch(f"/tasks/{task_id}", json=data)
        if r.is_success:
            return True, "Tarefa atualizada!"
        return False, r.json().get("detail", r.text)

def delete_task(token: str, task_id: int):
    with client(token) as c:
        r = c.delete(f"/tasks/{task_id}")
        if r.is_success:
            return True, "Tarefa excluída!"
        return False, r.json().get("detail", r.text)

# ---- dialogs (modais) ----
def _create_form_ui(prefix="create"):
    # usa defaults do session_state para manter valores se o usuário fechar/abrir
    name = st.text_input("Nome", value=st.session_state._create_defaults.get("name", ""), key=f"{prefix}_name")
    d = st.date_input("Data", value=st.session_state._create_defaults.get("date", date.today()),
                      format="YYYY-MM-DD", key=f"{prefix}_date")
    description = st.text_area("Descrição", value=st.session_state._create_defaults.get("description", ""),
                               height=100, key=f"{prefix}_desc")
    col_a, col_b = st.columns(2)
    with col_a:
        submit = st.button("Salvar", use_container_width=True, key=f"{prefix}_submit")
    with col_b:
        cancel = st.button("Cancelar", use_container_width=True, key=f"{prefix}_cancel")
    return submit, cancel, name, description, d

def _create_dialog_fallback():
    # fallback em versões antigas do Streamlit sem st.dialog
    with st.container(border=True):
        st.subheader("Nova tarefa")
        submit, cancel, name, description, d = _create_form_ui(prefix="create_fb")
        if cancel:
            st.session_state.show_create = False
            st.stop()
        if submit:
            if not name.strip():
                st.warning("Informe um nome.")
            else:
                ok, msg = create_task(st.session_state.token, name.strip(), description.strip(), d)
                if ok:
                    st.success(str(msg))
                    st.session_state.show_create = False
                    # limpa defaults
                    st.session_state._create_defaults = {"name": "", "description": "", "date": date.today()}
                    st.rerun()
                else:
                    st.error(str(msg))

if HAS_DIALOG:
    @st.dialog("Nova tarefa", width="small")
    def new_task_dialog():
        submit, cancel, name, description, d = _create_form_ui(prefix="create_md")
        if cancel:
            st.session_state.show_create = False
            st.rerun()
        if submit:
            if not name.strip():
                st.warning("Informe um nome.")
                st.stop()
            ok, msg = create_task(st.session_state.token, name.strip(), description.strip(), d)
            if ok:
                st.success(str(msg))
                st.session_state.show_create = False
                st.session_state._create_defaults = {"name": "", "description": "", "date": date.today()}
                st.rerun()
            else:
                st.error(str(msg))

    @st.dialog("Confirmar exclusão", width="small")
    def confirm_delete_dialog():
        st.write(f"Tem certeza que deseja excluir **{st.session_state.confirm_delete_name}**?")
        col1, col2 = st.columns(2)
        with col1:
            yes = st.button("❌ Confirmar", use_container_width=True, key="delete_yes_md")
        with col2:
            no = st.button("↩️ Cancelar", use_container_width=True, key="delete_no_md")

        if no:
            st.session_state.confirm_delete_id = None
            st.session_state.confirm_delete_name = ""
            st.rerun()

        if yes:
            ok_del, msg_del = delete_task(st.session_state.token, st.session_state.confirm_delete_id)
            if ok_del:
                st.success(str(msg_del))
                st.session_state.confirm_delete_id = None
                st.session_state.confirm_delete_name = ""
                st.rerun()
            else:
                st.error(str(msg_del))

# ---------- UI ----------
st.title("📝 To-doList")

# ---- auth ----
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
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.caption(f"Logado: {st.session_state.email}")
    with col_right:
        if st.button("Sair", use_container_width=True):
            st.session_state.token = None
            st.session_state.email = ""
            st.rerun()

    actions = st.columns([1, 1, 1])
    with actions[0]:
        if st.button("➕ Nova tarefa", use_container_width=True):
            st.session_state.show_create = True
            st.rerun()
    with actions[1]:
        if st.button("🔄 Recarregar", use_container_width=True):
            st.rerun()
    with actions[2]:
        pass

    # abre o modal de criação (ou fallback)
    if st.session_state.show_create:
        if HAS_DIALOG:
            new_task_dialog()
        else:
            _create_dialog_fallback()

    st.subheader("Minhas tarefas")
    ok, tasks = list_tasks(st.session_state.token)
    if not ok:
        st.error(str(tasks))
    else:
        if not tasks:
            st.info("Nenhuma tarefa.")
        else:
            for t in tasks:
                with st.container(border=True):
                    header_cols = st.columns([6, 2, 2])
                    with header_cols[0]:
                        st.markdown(f"**{t['name']}**")
                    with header_cols[1]:
                        if st.button("✏️ Editar", key=f"edit_{t['id']}", use_container_width=True):
                            st.session_state.editing_task_id = t["id"]
                            st.session_state._edit_name = t["name"]
                            st.session_state._edit_description = t.get("description") or ""
                            try:
                                dval = t.get("date")
                                st.session_state._edit_date = (
                                    datetime.strptime(dval, "%Y-%m-%d").date() if dval else date.today()
                                )
                            except Exception:
                                st.session_state._edit_date = date.today()
                            st.session_state._edit_state = (t.get("state") or "PENDENTE")
                            st.rerun()

                    with header_cols[2]:
                        if st.button("🗑️ Excluir", key=f"del_{t['id']}", use_container_width=True):
                            st.session_state.confirm_delete_id = t["id"]
                            st.session_state.confirm_delete_name = t["name"]
                            if HAS_DIALOG:
                                st.rerun()  # para abrir o dialog logo abaixo
                            else:
                                # fallback simples: mostrar botões inline (último recurso)
                                st.session_state._fallback_inline_confirm = True
                                st.rerun()

                    # abre o modal de confirmação se necessário
                    if HAS_DIALOG and st.session_state.confirm_delete_id == t["id"]:
                        confirm_delete_dialog()

                    # edição inline (mantida)
                    if st.session_state.editing_task_id == t["id"]:
                        with st.form(f"form-edit-{t['id']}", clear_on_submit=False):
                            name_ed = st.text_input("Nome", value=st.session_state.get("_edit_name", t["name"]))
                            d_ed = st.date_input(
                                "Data",
                                value=st.session_state.get("_edit_date", date.today()),
                                format="YYYY-MM-DD"
                            )
                            description_ed = st.text_area(
                                "Descrição",
                                value=st.session_state.get("_edit_description", t.get("description") or ""),
                                height=100
                            )
                            state_ed = st.selectbox(
                                "Estado",
                                options=["PENDENTE", "ANDAMENTO", "CONCLUIDA"],
                                index=["PENDENTE", "ANDAMENTO", "CONCLUIDA"].index(
                                    (st.session_state.get("_edit_state") or "PENDENTE")
                                ),
                            )

                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                submit_edit = st.form_submit_button("Salvar alterações", use_container_width=True)
                            with col_cancel:
                                cancel_edit = st.form_submit_button("Cancelar", use_container_width=True)

                        if cancel_edit:
                            st.session_state.editing_task_id = None
                            st.rerun()

                        if submit_edit:
                            ok_upd, msg_upd = update_task(
                                st.session_state.token,
                                t["id"],
                                name=name_ed.strip(),
                                description=description_ed.strip(),
                                d=d_ed,
                                state=state_ed,
                            )
                            if ok_upd:
                                st.success(str(msg_upd))
                                st.session_state.editing_task_id = None
                                st.rerun()
                            else:
                                st.error(str(msg_upd))
                    else:
                        st.caption(t.get("description") or "—")
                        st.text(f"Estado: {t.get('state') or 'PENDENTE'} | Data: {t.get('date') or '—'}")

            # fallback para confirmação inline (sem st.dialog)
            if not HAS_DIALOG and st.session_state.get("_fallback_inline_confirm") and st.session_state.confirm_delete_id:
                with st.container(border=True):
                    st.write(f"Confirmar exclusão de **{st.session_state.confirm_delete_name}**?")
                    c1, c2 = st.columns(2)
                    with c1:
                        yes = st.button("❌ Confirmar", use_container_width=True, key="delete_yes_fb")
                    with c2:
                        no = st.button("↩️ Cancelar", use_container_width=True, key="delete_no_fb")
                    if no:
                        st.session_state.confirm_delete_id = None
                        st.session_state.confirm_delete_name = ""
                        st.session_state._fallback_inline_confirm = False
                        st.rerun()
                    if yes:
                        ok_del, msg_del = delete_task(st.session_state.token, st.session_state.confirm_delete_id)
                        if ok_del:
                            st.success(str(msg_del))
                            st.session_state.confirm_delete_id = None
                            st.session_state.confirm_delete_name = ""
                            st.session_state._fallback_inline_confirm = False
                            st.rerun()
                        else:
                            st.error(str(msg_del))
