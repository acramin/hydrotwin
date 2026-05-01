import streamlit as st

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.crud import autenticar_usuario, criar_usuario, ensure_default_admin
from others.env import is_development_mode, user_session_key, get_admin_credentials

SESSION_USER_KEY = user_session_key()

def bootstrap_auth():
    ensure_default_admin()

    if SESSION_USER_KEY not in st.session_state:
        st.session_state[SESSION_USER_KEY] = None
    
    # Em modo DEVELOPMENT, fazer login automático como admin se não houver usuário logado
    if is_development_mode() and st.session_state[SESSION_USER_KEY] is None:
        try:
            usuario = autenticar_usuario(
                *get_admin_credentials()
            )
            if usuario:
                st.session_state[SESSION_USER_KEY] = usuario
        except Exception:
            pass  # Se falhar, continua sem login automático


def get_current_user():
    bootstrap_auth()
    return st.session_state.get(SESSION_USER_KEY)


def set_current_user(user):
    st.session_state[SESSION_USER_KEY] = user


def logout_user():
    st.session_state[SESSION_USER_KEY] = None


def require_role(user, allowed_roles, message=None):
    if isinstance(allowed_roles, str):
        allowed_roles = {allowed_roles}
    else:
        allowed_roles = set(allowed_roles)

    if user["role"] not in allowed_roles:
        st.error(message or "Seu perfil não tem acesso a esta área.")
        st.stop()


def require_page_access(user, page_name):
    """
    Verifica se o usuário tem acesso à página.
    Se não tiver, exibe uma mensagem de erro e interrompe a execução.
    """
    from others.page_access import has_page_access
    
    if not has_page_access(user["role"], page_name):
        st.error(f"Seu perfil ({user['role']}) não tem acesso a esta página.")
        st.info("Se você acredita que isso é um erro, entre em contato com o administrador do sistema.")
        st.stop()
