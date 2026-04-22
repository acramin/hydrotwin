import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

from core.getters import *

# =========================
# 📊 Visão Geral
# =========================

st.title("📊 Visão Geral")

status = get_last_status()

# print("Status:", status)

if len(status) == 0:
    st.info("Cadastre uma bancada para começar a gerar status e históricos.")
    st.stop()

st.caption(f"Status atual das bancadas, indicadores rápidos e alertas ativos.\nAtualizado a cada 5 segundos.\nÚltima atualização: {status.get('atualizado_em', 'N/A')}")

# STATUS
st.subheader("Status das Bancadas")

status.pop("atualizado_em", None)  # Remove o timestamp do status para exibir só as bancadas

if not status:
    st.info("Nenhuma bancada cadastrada ainda.")
else:
    colunas = st.columns(min(4, len(status)))
    for i, (b, s) in enumerate(status.items()):
        emoji = "⚪" if s == "Sem dados" else "🟢" if "Saudável" in s else "🟡" if "Atenção" in s else "🔴" 
        colunas[i % len(colunas)].metric(b.capitalize(), f"{emoji} {s}")

# KPIs
st.subheader("Indicadores Gerais")

for bancada_id, nome, *_ in get_bancadas():
    kpis = get_kpis(bancada_id, nome)
    
    if len(kpis.get(nome, {})) == 0:
        st.info(f"Nenhum KPI calculado ainda para a bancada {nome}. Assim que as próximas leituras brutas entrarem, os cálculos serão gerados automaticamente.")
    
    if kpis:
        st.markdown(f"**{nome.capitalize()}**")
        colunas = st.columns(min(4, len(kpis[nome])))
        for i, (k, v) in enumerate(kpis[nome].items()):
            colunas[i % len(colunas)].metric(k.capitalize().replace("_", " "), f"{v:.2f}" if isinstance(v, (int, float)) else v)

#Alertas ativos
alertas = get_alertas()
st.subheader("Alertas Ativos")

if not alertas:
    st.success("Nenhum alerta ativo!")
else:
    for alerta in alertas:
        st.warning(alerta)
