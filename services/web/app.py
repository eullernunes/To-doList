import streamlit as st
from datetime import date
from state.session import init_session_state
from services.api import login, signup, list_tasks
from logic.filters import apply_filter, apply_sort, matches_search, parse_date_safe
from ui.components import show_create_dialog, show_edit_dialog, show_confirm_delete_dialog

st.set_page_config(page_title="To-doList", page_icon="📝", layout="centered")
init_session_state()

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
    # topo
    c1, c2 = st.columns([1, 1])
    with c1:
        st.caption(f"Logado: {st.session_state.email}")
    with c2:
        if st.button("Sair", use_container_width=True):
            st.session_state.token = None
            st.session_state.email = ""
            st.rerun()

    # ações principais
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

    # sidebar (filtros, busca, ordenação)
    with st.sidebar:
        st.header("Filtros")
        view = st.radio(
            "Lista",
            ["Todas", "Prioridade", "Hoje", "Esta semana", "Concluídas", "Em andamento", "Pendentes"],
            index=0
        )
        search = st.text_input("Buscar por nome/descrição", placeholder="ex.: relatório, compra, estudo")
        sort_by = st.selectbox("Ordenar por", ["Data (asc)", "Data (desc)", "Nome A→Z", "Nome Z→A"], index=0)
        st.caption("Dica: clique na ☆ para marcar como favorita.")

    # modal de criação
    if st.session_state.show_create:
        show_create_dialog()

    # listagem
    st.subheader("Minhas tarefas")
    ok, tasks = list_tasks(st.session_state.token)
    if not ok:
        st.error(str(tasks))
    else:
        if not tasks:
            st.info("Nenhuma tarefa.")
        else:
            tasks_filtered = apply_filter(tasks, view, st.session_state.favorites)
            tasks_filtered = [t for t in tasks_filtered if matches_search(t, search)]
            tasks_filtered = apply_sort(tasks_filtered, sort_by)

            st.caption(f"Exibindo {len(tasks_filtered)} de {len(tasks)} tarefas")

            for t in tasks_filtered:
                with st.container(border=True):
                    header_cols = st.columns([0.6, 5.4, 2, 2])  # [fav, nome, editar, excluir]
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
                                "date": (parse_date_safe(t.get("date")) or date.today()),
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
            show_edit_dialog()
            show_confirm_delete_dialog()
