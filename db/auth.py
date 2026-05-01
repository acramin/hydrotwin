import streamlit as st
import os

from dotenv import load_dotenv

load_dotenv()

from db.crud import autenticar_usuario, criar_usuario, ensure_default_admin

SESSION_USER_KEY = os.getenv("SESSION_USER_KEY")


def bootstrap_auth():
    ensure_default_admin()

    if SESSION_USER_KEY not in st.session_state:
        st.session_state[SESSION_USER_KEY] = None


def get_current_user():
    bootstrap_auth()
    return st.session_state.get(SESSION_USER_KEY)


def set_current_user(user):
    st.session_state[SESSION_USER_KEY] = user


def logout_user():
    st.session_state[SESSION_USER_KEY] = None


def render_user_badge():
    user = get_current_user()
    if not user:
        return

    with st.sidebar:
        st.caption(f"Logado como {user['username']} ({user['role']})")
        if st.button("Sair", use_container_width=True):
            logout_user()
            st.rerun()


def render_auth_gate(app_name="HydroTwin"):
    bootstrap_auth()
    user = get_current_user()

    if user:
        render_user_badge()
        return user

    st.subheader(f"Acesso ao {app_name}")
    st.info("Entre com uma conta existente ou crie um usuário viewer para acessar as visualizações.")

    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar conta"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Usuário", placeholder="ex: master")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            usuario = autenticar_usuario(username, password)
            if usuario is None:
                st.error("Usuário ou senha inválidos.")
            else:
                set_current_user(usuario)
                st.success(f"Bem-vindo, {usuario['username']}!")
                st.rerun()

    with tab_cadastro:
        with st.form("register_form"):
            novo_username = st.text_input("Novo usuário", placeholder="ex: joao.silva")
            nova_senha = st.text_input("Senha", type="password")
            confirmar_senha = st.text_input("Confirmar senha", type="password")
            submitted = st.form_submit_button("Criar usuário", use_container_width=True)

        if submitted:
            username_normalizado = novo_username.strip()
            if not username_normalizado:
                st.warning("Informe um nome de usuário.")
            elif username_normalizado.lower() == "admin":
                st.warning("O usuário admin é reservado ao administrador padrão.")
            elif len(nova_senha) < 6:
                st.warning("A senha deve ter pelo menos 6 caracteres.")
            elif nova_senha != confirmar_senha:
                st.warning("As senhas informadas não conferem.")
            else:
                try:
                    criar_usuario(username_normalizado, nova_senha, role="viewer")
                except Exception:
                    st.error("Não foi possível criar o usuário. Verifique se o nome já não está em uso.")
                else:
                    usuario = autenticar_usuario(username_normalizado, nova_senha)
                    set_current_user(usuario)
                    st.success("Usuário criado com sucesso. Você já está logado.")
                    st.rerun()

    st.stop()


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
