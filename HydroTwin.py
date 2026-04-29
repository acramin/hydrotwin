import streamlit as st
from core.visao_geral import get_last_status
from simulator.simulator_port import simular_dados, parar_simulacao
from db.auth import render_auth_gate

st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

st.title("🌱 HydroTwin")

st.markdown(
    """
    Aqui pode ser uma descrição geral do projeto, explicando o que é o HydroTwin, seus objetivos e funcionalidades.
    Explicar como que adiciona uma nova bancada, como que os dados são coletados e monitorados, e o que os usuários podem esperar do sistema.
    O acesso agora é feito com login: usuários novos entram como `viewer` e o usuário `admin` com role `admin` é o único com acesso ao cadastro de bancadas.
    Colocar também um link para o repositório do projeto no GitHub, para que os interessados possam acessar o código-fonte e contribuir.
    Colocar imagens ilustrativas do sistema, como diagramas de arquitetura, fotos das bancadas, ou gráficos de monitoramento, para tornar a página mais visual e atrativa.
    """
)

usuario = render_auth_gate("HydroTwin")

status = get_last_status()

if usuario["role"] == "viewer" and len(status) == 0:
    st.info("Bem-vindo ao HydroTwin! Você tem acesso de visualização. Aguarde até que o admin cadastre uma bancada para acessar os dados de monitoramento.")
    st.stop()
elif usuario["role"] == "viewer" and len(status) > 0:
    st.info("Bem-vindo ao HydroTwin! Você tem acesso de visualização. Explore a visão geral e o monitoramento detalhado para acompanhar suas bancadas.")
    st.stop()
    
if usuario["role"] == "admin":
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
