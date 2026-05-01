import streamlit as st
from simulator.simulator_port import simular_dados, parar_simulacao
from db.auth import get_current_user, require_page_access
from others.env import is_development_mode, is_production_mode

st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

usuario = get_current_user()
if usuario is None:
    st.error("❌ Você precisa estar autenticado para acessar esta página.")
    st.stop()

require_page_access(usuario, "Simulador")

if usuario["role"] == "admin" and is_development_mode():
    try: 
        st.success("Bem-vindo, admin! Você tem acesso total ao sistema. Use as abas para cadastrar bancadas, visualizar a visão geral e acessar o monitoramento detalhado.")
        st.markdown("É possível iniciar uma simulação de dados para testar o sistema. Clique no botão abaixo para começar a simular dados falsos entrando a cada 0.5 segundos e processando as bancadas ativas a cada 10 segundos.")

        if st.button("Iniciar simulação de dados"):
            simular_dados()
            st.success(
                "Simulação iniciada. O sistema agora insere dados falsos a cada 0.5 segundos e processa as bancadas ativas a cada 10 segundos."
            )

        if st.button("Parar simulação de dados"):
            parar_simulacao()
            st.success("Simulação de dados parada.")
            st.stop()
    except Exception as e:
        st.error(f"Erro ao iniciar/parar simulação: {str(e)}")
        
elif usuario["role"] == "admin" and is_production_mode():
    st.warning("⚠️ Simulação de dados está desativada em modo de produção para garantir a integridade dos dados reais. Para testar a simulação, altere o modo para DEVELOPMENT no arquivo .env.")
    