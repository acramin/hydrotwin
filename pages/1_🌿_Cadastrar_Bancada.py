import streamlit as st
from datetime import date

from db.crud import get_culturas, inserir_bancada, inserir_filete

st.set_page_config(page_title="Hydroponic Monitor", layout="wide")

st.title("🌱 HydroTwin")


# =========================
# 🌿 CADASTRO
# =========================


st.header("Cadastrar nova bancada")

nome = st.text_input("Nome da bancada", key="nome_bancada")

culturas = get_culturas()
cultura_dict = {c[1]: c[0] for c in culturas}
opcoes_cultura = ["Selecione a cultura"] + list(cultura_dict.keys())
cultura_nome = st.selectbox("Cultura", opcoes_cultura, index=0)

data_inicio = st.date_input("Data de início", value=date.today())

if st.button("Salvar"):
    if cultura_nome == "Selecione a cultura":
        st.warning("Selecione uma cultura antes de salvar.")
        st.stop()

    cultura_id = cultura_dict[cultura_nome]

    bancada_id = inserir_bancada(
        nome,
        cultura_id
    )
    
    if bancada_id is None:
        st.error("ID da bancada não encontrado. Por favor, cadastre a bancada primeiro.")
        st.stop()
    
    inserir_filete(
        bancada_id,
        cultura_id,
        data_inicio.strftime("%Y-%m-%d")
    )
    st.success("Bancada cadastrada com sucesso!")

