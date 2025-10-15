import streamlit as st
from datetime import date
from services.api import create_task, update_task, delete_task
from logic.filters import parse_date_safe

HAS_DIALOG = hasattr(st, "dialog")

# ---------- Forms ----------
def create_form(prefix="create"):
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

def edit_form(prefix="edit"):
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

# ---------- Dialogs (modais + fallbacks) ----------
def show_create_dialog():
    if HAS_DIALOG:
        @st.dialog("Nova tarefa", width="small")
        def _dlg():
            submit, cancel, name, description, d = create_form(prefix="create_md")
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
        _dlg()
    else:
        with st.container(border=True):
            st.subheader("Nova tarefa")
            submit, cancel, name, description, d = create_form(prefix="create_fb")
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

def show_edit_dialog():
    if not st.session_state.editing_task_id:
        return
    if HAS_DIALOG:
        @st.dialog("Editar tarefa", width="small")
        def _dlg():
            submit, cancel, name, description, d, state = edit_form(prefix="edit_md")
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
        _dlg()
    else:
        with st.container(border=True):
            st.subheader("Editar tarefa")
            submit, cancel, name, description, d, state = edit_form(prefix="edit_fb")
            if cancel:
                st.session_state.editing_task_id = None
                st.stop()
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

def show_confirm_delete_dialog():
    if not st.session_state.confirm_delete_id:
        return
    if HAS_DIALOG:
        @st.dialog("Confirmar exclusão", width="small")
        def _dlg():
            st.write(f"Tem certeza que deseja excluir **{st.session_state.confirm_delete_name}**?")
            c1, c2 = st.columns(2)
            with c1:
                yes = st.button("❌ Confirmar", use_container_width=True, key="delete_yes_md")
            with c2:
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
        _dlg()
    else:
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
