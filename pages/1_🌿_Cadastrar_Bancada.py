import streamlit as st
from datetime import date

from db.crud import get_bancadas, get_culturas, inserir_bancada, inserir_filete

st.set_page_config(page_title="Hydroponic Monitor", layout="wide")

st.title("🌱 HydroTwin")

# =========================
# 🌿 CADASTRO
# =========================

st.header("Cadastrar nova bancada", help="Preencha os dados abaixo para cadastrar uma nova bancada e começar a monitorar suas condições.")

nome = st.text_input("Nome da bancada", key="nome_bancada", help="Ex: Bancada 1")

culturas = get_culturas()
cultura_dict = {c[1]: c[0] for c in culturas}
opcoes_cultura = ["Selecione a cultura"] + list(cultura_dict.keys())
cultura_nome = st.selectbox("Cultura", opcoes_cultura, index=0, key="cultura_bancada", help="Selecione a cultura que será cultivada nessa bancada")

data_inicio = st.date_input("Data de início", value=date.today(), format="DD/MM/YYYY", help="Data de início do cultivo nessa bancada")

if st.button("Salvar"):
    if cultura_nome == "Selecione a cultura":
        st.warning("Selecione uma cultura antes de salvar.")
        st.stop()
    if not nome:
        st.warning("Digite um nome para a bancada antes de salvar.")
        st.stop()
    if not data_inicio:
        st.warning("Selecione uma data de início antes de salvar.")
        st.stop()

    cultura_id = cultura_dict[cultura_nome]

    for bancada_id, nome, cultura_nome, *_ in get_bancadas(): # Verifica se a bancada já existe
    
        if nome == nome and cultura_nome == cultura_nome:
            inserir_filete(
                bancada_id,
                cultura_id,
                data_inicio.strftime("%Y-%m-%d")
            )
            st.success("Bancada já cadastrada. Novo filete criado para a data de início selecionada.")
        
        else:
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

