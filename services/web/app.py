import os
import streamlit as st
import httpx
from datetime import date, datetime, timedelta

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
if "_edit_defaults" not in st.session_state:
    st.session_state._edit_defaults = {"name": "", "description": "", "date": date.today(), "state": "PENDENTE"}
if "favorites" not in st.session_state:
    st.session_state.favorites = set()  # ids favoritos (somente front por enquanto)

# suporte a modais nativos
HAS_DIALOG = hasattr(st, "dialog")

# ---------- HTTP / API ----------
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

# ---------- Helpers de UI / Filtro / Ordenação ----------
def _parse_date_safe(dstr: str | None):
    try:
        return datetime.strptime(dstr, "%Y-%m-%d").date() if dstr else None
    except Exception:
        return None

def _matches_search(t: dict, q: str) -> bool:
    if not q:
        return True
    q = q.lower().strip()
    return q in (t.get("name","").lower()) or q in (t.get("description","") or "").lower()

def _apply_filter(tasks: list[dict], view: str) -> list[dict]:
    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)

    out = []
    for t in tasks:
        d = _parse_date_safe(t.get("date"))
        state = (t.get("state") or "PENDENTE").upper()
        is_fav = t.get("id") in st.session_state.favorites

        if view == "Todas":
            pass
        elif view == "Favoritas" and not is_fav:
            continue
        elif view == "Hoje" and d != today:
            continue
        elif view == "Atrasadas" and (d is None or d >= today):
            continue
        elif view == "Esta semana":
            if d is None or not (start_week <= d <= end_week):
                continue
        elif view == "Concluídas" and state != "CONCLUIDA":
            continue
        elif view == "Em andamento" and state != "ANDAMENTO":
            continue
        elif view == "Pendentes" and state != "PENDENTE":
            continue

        out.append(t)
    return out

def _apply_sort(tasks: list[dict], sort_by: str) -> list[dict]:
    if sort_by == "Data (asc)":
        return sorted(tasks, key=lambda t: (_parse_date_safe(t.get("date")) or date.max, t.get("name","").lower()))
    if sort_by == "Data (desc)":
        return sorted(tasks, key=lambda t: (_parse_date_safe(t.get("date")) or date.min, t.get("name","").lower()), reverse=True)
    if sort_by == "Nome A→Z":
        return sorted(tasks, key=lambda t: t.get("name","").lower())
    if sort_by == "Nome Z→A":
        return sorted(tasks, key=lambda t: t.get("name","").lower(), reverse=True)
    return tasks

# ---------- Form UIs ----------
def _create_form_ui(prefix="create"):
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

def _edit_form_ui(prefix="edit"):
    name = st.text_input("Nome", value=st.session_state._edit_defaults.get("name", ""), key=f"{prefix}_name")
    d = st.date_input("Data", value=st.session_state._edit_defaults.get("date", date.today()),
                      format="YYYY-MM-DD", key=f"{prefix}_date")
    description = st.text_area("Descrição", value=st.session_state._edit_defaults.get("description", ""),
                               height=100, key=f"{prefix}_desc")
    state = st.selectbox(
        "Estado",
        options=["PENDENTE", "ANDAMENTO", "CONCLUIDA"],
        index=["PENDENTE", "ANDAMENTO", "CONCLUIDA"].index(
            st.session_state._edit_defaults.get("state", "PENDENTE")
        ),
        key=f"{prefix}_state"
    )
    col_a, col_b = st.columns(2)
    with col_a:
        submit = st.button("Salvar alterações", use_container_width=True, key=f"{prefix}_submit")
    with col_b:
        cancel = st.button("Cancelar", use_container_width=True, key=f"{prefix}_cancel")
    return submit, cancel, name, description, d, state

# ---------- Dialogs (modais) ----------
def _create_dialog_fallback():
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
                    st.session_state._create_defaults = {"name": "", "description": "", "date": date.today()}
                    st.rerun()
                else:
                    st.error(str(msg))

def _edit_dialog_fallback(task_id: int):
    with st.container(border=True):
        st.subheader("Editar tarefa")
        submit, cancel, name, description, d, state = _edit_form_ui(prefix="edit_fb")
        if cancel:
            st.session_state.editing_task_id = None
            st.stop()
        if submit:
            ok_upd, msg_upd = update_task(
                st.session_state.token, task_id,
                name=name.strip(), description=description.strip(), d=d, state=state
            )
            if ok_upd:
                st.success(str(msg_upd))
                st.session_state.editing_task_id = None
                st.rerun()
            else:
                st.error(str(msg_upd))

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

    @st.dialog("Editar tarefa", width="small")
    def edit_task_dialog():
        submit, cancel, name, description, d, state = _edit_form_ui(prefix="edit_md")
        if cancel:
            st.session_state.editing_task_id = None
            st.rerun()
        if submit:
            ok_upd, msg_upd = update_task(
                st.session_state.token,
                st.session_state.editing_task_id,
                name=name.strip(), description=description.strip(), d=d, state=state
            )
            if ok_upd:
                st.success(str(msg_upd))
                st.session_state.editing_task_id = None
                st.rerun()
            else:
                st.error(str(msg_upd))

# ---------- UI ----------
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
    c1, c2 = st.columns([1, 1])
    with c1:
        st.caption(f"Logado: {st.session_state.email}")
    with c2:
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

    with st.sidebar:
        st.header("Filtros")
        view = st.radio(
            "Lista",
            ["Todas", "Favoritas", "Hoje", "Atrasadas", "Esta semana", "Concluídas", "Em andamento", "Pendentes"],
            index=0
        )
        search = st.text_input("Buscar por nome/descrição", placeholder="ex.: relatório, compra, estudo")
        sort_by = st.selectbox("Ordenar por", ["Data (asc)", "Data (desc)", "Nome A→Z", "Nome Z→A"], index=0)
        st.caption("Dica: clique na ☆ para marcar como favorita.")

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
            tasks_filtered = _apply_filter(tasks, view)
            tasks_filtered = [t for t in tasks_filtered if _matches_search(t, search)]
            tasks_filtered = _apply_sort(tasks_filtered, sort_by)

            st.caption(f"Exibindo {len(tasks_filtered)} de {len(tasks)} tarefas")

            for t in tasks_filtered:
                with st.container(border=True):
                    header_cols = st.columns([0.6, 5.4, 2, 2])
                    with header_cols[0]:
                        is_fav = t["id"] in st.session_state.favorites
                        star = "⭐" if is_fav else "☆"
                        if st.button(star, key=f"fav_{t['id']}", use_container_width=True):
                            if is_fav:
                                st.session_state.favorites.discard(t["id"])
                            else:
                                st.session_state.favorites.add(t["id"])
                            st.rerun()

                    with header_cols[1]:
                        st.markdown(f"**{t['name']}**")

                    with header_cols[2]:
                        if st.button("✏️ Editar", key=f"edit_{t['id']}", use_container_width=True):
                            st.session_state._edit_defaults = {
                                "name": t["name"],
                                "description": t.get("description") or "",
                                "date": (_parse_date_safe(t.get("date")) or date.today()),
                                "state": t.get("state") or "PENDENTE",
                            }
                            st.session_state.editing_task_id = t["id"]
                            st.rerun()

                    with header_cols[3]:
                        if st.button("🗑️ Excluir", key=f"del_{t['id']}", use_container_width=True):
                            st.session_state.confirm_delete_id = t["id"]
                            st.session_state.confirm_delete_name = t["name"]
                            st.rerun()

                    st.caption(t.get("description") or "—")
                    st.text(f"Estado: {t.get('state') or 'PENDENTE'} | Data: {t.get('date') or '—'}")

            # modais pendentes
            if st.session_state.editing_task_id:
                if HAS_DIALOG:
                    edit_task_dialog()
                else:
                    _edit_dialog_fallback(st.session_state.editing_task_id)

            if st.session_state.confirm_delete_id and HAS_DIALOG:
                confirm_delete_dialog()
            elif st.session_state.confirm_delete_id and not HAS_DIALOG:
                # fallback inline para confirmação
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
