import streamlit as st
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

render_auth_gate("HydroTwin")

if st.button("Iniciar simulação de dados"):
    simular_dados()
    st.success(
        "Simulação iniciada. O sistema agora insere dados falsos a cada 0.5 segundos e processa as bancadas ativas a cada 10 segundos."
    )

if st.button("Parar simulação de dados"):
    parar_simulacao()
    st.success("Simulação de dados parada.")
    st.stop()
