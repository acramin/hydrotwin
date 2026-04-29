import streamlit as st
from datetime import date
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.auth import render_auth_gate, require_role
from db.crud import get_bancadas, get_culturas, inserir_bancada, inserir_filete

st.set_page_config(page_title="Hydroponic Monitor", layout="wide")

st.title("🌱 HydroTwin")

usuario = render_auth_gate("HydroTwin")
require_role(usuario, "admin", "A página de cadastro de bancadas é restrita ao usuário com permissão de admin.")

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

    # print(f"Dados para cadastro: Nome: {nome}, Cultura: {cultura_nome} (ID: {cultura_id}), Data de início: {data_inicio}")

    if len(get_bancadas()) == 0:
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
    
    else:
        for bancada_id, nome_bancada, cultura_nome_cadastrada, *_ in get_bancadas(): # Verifica se a bancada já existe
            
            if nome == nome_bancada and cultura_nome == cultura_nome_cadastrada:
                inserir_filete(
                    bancada_id,
                    cultura_id,
                    data_inicio.strftime("%Y-%m-%d")
                )
                st.success("Bancada já cadastrada. Novo filete criado para a data de início selecionada.")
                break
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

