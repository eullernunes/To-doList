from datetime import date
import streamlit as st

def init_session_state() -> None:
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

def has_dialog() -> bool:
    import streamlit as st
    return hasattr(st, "dialog")
