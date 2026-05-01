import sys
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.auth import get_current_user, bootstrap_auth, logout_user
from others.page_access import get_allowed_pages

# Configurar página
st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

# Bootstrap de autenticação
bootstrap_auth()

# Definir páginas públicas (sem restrição de login)
home = st.Page("HydroTwin.py", title="🌱 HydroTwin")
faq = st.Page("pages/4_❓_FAQ.py", title="FAQ")

# Definir páginas restritas (exigem login)
controle_bancadas = st.Page(
    "pages/1_🌿_Painel_de_Controle_-_Bancadas.py", 
    title="Painel de Controle"
)
visao_geral = st.Page(
    "pages/2_📊_Visão_Geral.py", 
    title="Visão Geral"
)
monitoramento_detalhado = st.Page(
    "pages/3_🔬_Monitoramento_Detalhado.py", 
    title="Monitoramento Detalhado"
)
simulador = st.Page(
    "pages/5_🕹️_Simulador.py", 
    title="Simulador"
)

# Obter usuário atual
usuario = get_current_user()

# Construir lista de páginas baseada em autenticação
if usuario is None:
    # Usuário não autenticado: apenas Home e FAQ
    pages = [home, faq]
else:
    # Usuário autenticado: Home + FAQ + páginas da role
    pages = [home, faq]
    
    user_role = usuario.get("role", "viewer")
    allowed_pages = get_allowed_pages(user_role)
    
    # Adicionar páginas permitidas pela role
    if "Painel de Controle - Bancadas" in allowed_pages:
        pages.append(controle_bancadas)
    if "Visão Geral" in allowed_pages:
        pages.append(visao_geral)
    if "Monitoramento Detalhado" in allowed_pages:
        pages.append(monitoramento_detalhado)
    if "Simulador" in allowed_pages:
        pages.append(simulador)

# Renderizar user badge na sidebar
if usuario is not None:
    with st.sidebar:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.caption(f"👤 {usuario['username']} ({usuario['role']})")
        with col2:
            if st.button("🚪 Sair", use_container_width=True):
                logout_user()
                st.rerun()

# Renderizar navegação
pg = st.navigation(pages)
pg.run()