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

st.title("📊 Visão Geral")

status = get_last_status()

st.caption(f"Status atual das bancadas, indicadores rápidos e alertas ativos.\nAtualizado a cada 15 minutos.\nÚltima atualização: {status.get('atualizado_em', 'N/A')}")

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
    ##st.markdown(str(kpis))
    
    if kpis:
        st.markdown(f"**{nome.capitalize()}**")
        colunas = st.columns(min(4, len(kpis[nome])))
        for i, (k, v) in enumerate(kpis[nome].items()):
            colunas[i % len(colunas)].metric(k.capitalize().replace("_", " "), f"{v:.2f}" if isinstance(v, (int, float)) else v)

#Alertas ativos
alertas = get_alertas()
st.subheader("Alertas Ativos")

if not alertas:
    st.success("Nenhum alerta ativo! Todas as bancadas estão saudáveis.")
else:
    for alerta in alertas:
        st.warning(alerta)
