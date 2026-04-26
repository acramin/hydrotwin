import streamlit as st
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.crud import get_bancadas
from core.monitoramento_detalhado import (
    carregar_monitoramento_bancada,
    montar_df_anomalias,
    montar_df_contribuicao_risco,
    montar_df_previsoes,
    render_grafico_linha,
    render_grafico_zona,
    render_legenda_zonas,
    VARIAVEIS_ZONA_FORTES,
)
from utils import formatar_data

st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

# =========================
# 🔬 Monitoramento Detalhado
# =========================

st.title("🔬 Monitoramento Detalhado")

rows = get_bancadas()

if not rows:
    st.info("Cadastre uma bancada para começar a gerar status e históricos.")
    st.stop()

mapa_bancadas = {nome: bancada_id for bancada_id, nome, *_ in rows}
bancada = st.selectbox("Selecione a bancada", list(mapa_bancadas.keys()))
bancada_id = mapa_bancadas[bancada]

dados = carregar_monitoramento_bancada(bancada_id=bancada_id, horas=24)
df = dados["df"]
proc = dados["proc"]
limites = dados.get("limites") or {}
resultado_previsao = dados["resultado_previsao"]
resultado_anomalias = dados["resultado_anomalias"]

# STATUS + SCORE
col1, col2 = st.columns(2)
if proc:
    col1.metric("Status", proc["status"])
    col2.metric("Risk Score", f'{proc["score"]:.1f}')
    st.caption(f'Janela processada: {proc["janela_horaria"]} | Amostras: {proc["n_amostras"]} | Atualizado em: {formatar_data(proc["dth_calculado"])}')
else:
    col1.metric("Status", "Sem dados")
    col2.metric("Risk Score", "-")
    st.info("Ainda não há agregação para esta bancada. Assim que a próxima leitura bruta entrar, o cálculo será gerado automaticamente.")
    st.stop()

if df.empty:
    st.warning("Sem leituras brutas recentes para exibir gráficos.")
    st.stop()

# GRÁFICOS DE ZONA (candidatos fortes)
st.subheader("Gráficos por variável")
modo_visualizacao = st.radio(
    "Modo de visualização",
    options=["Zona", "Linha"],
    horizontal=True,
)

if modo_visualizacao == "Zona":
    render_legenda_zonas()

for idx in range(0, len(VARIAVEIS_ZONA_FORTES), 2):
    col_esq, col_dir = st.columns(2)
    metrica_esq, titulo_esq, unidade_esq = VARIAVEIS_ZONA_FORTES[idx]

    with col_esq:
        if modo_visualizacao == "Zona":
            render_grafico_zona(df, metrica_esq, titulo_esq, limites, unidade=unidade_esq)
        else:
            render_grafico_linha(df, metrica_esq, titulo_esq, unidade=unidade_esq)

    if idx + 1 < len(VARIAVEIS_ZONA_FORTES):
        metrica_dir, titulo_dir, unidade_dir = VARIAVEIS_ZONA_FORTES[idx + 1]
        with col_dir:
            if modo_visualizacao == "Zona":
                render_grafico_zona(df, metrica_dir, titulo_dir, limites, unidade=unidade_dir)
            else:
                render_grafico_linha(df, metrica_dir, titulo_dir, unidade=unidade_dir)

# COMPLEMENTAR (mantido para leitura direta)
col1, col2 = st.columns(2)

if "nivel_tanque" in df.columns:
    col1.subheader("Nível de Água")
    col1.line_chart(df.set_index("dth_recebido")["nivel_tanque"])
else:
    col1.subheader("Nível de Água")
    col1.info("Sem coluna de nível de tanque nas leituras recentes.")
    
if "vazao" in df.columns:
    col2.subheader("Vazão")
    col2.line_chart(df.set_index("dth_recebido")["vazao"])
else:
    col2.subheader("Vazão")
    col2.info("Sem coluna de vazão nas leituras recentes.")

risco_df = montar_df_contribuicao_risco(proc)
if not risco_df.empty:
    st.subheader("Contribuição do risco")
    st.dataframe(risco_df, hide_index=True)

st.subheader("Tendência operacional")
col_a, col_b, col_c = st.columns(3)
col_a.metric("Status previsto", resultado_previsao["status"])
col_b.metric("Previsão geral", f'{resultado_previsao["score"]:.1f}')
col_c.metric("Sensores previstos", resultado_previsao["total_previsoes"])

st.caption(resultado_previsao["resumo"])

previsao_df = montar_df_previsoes(resultado_previsao)
if not previsao_df.empty:
    st.dataframe(
        previsao_df,
        hide_index=True,
    )
else:
    st.info("Ainda não há tendência operacional clara para as leituras recentes.")

st.subheader("Detecção de anomalias")
if not resultado_anomalias:
    st.info("Sem dados suficientes para detectar anomalias.")
else:
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Status de anomalia", resultado_anomalias["status"])
    col_b.metric("Anomaly Score", f'{resultado_anomalias["score"]:.1f}')
    col_c.metric("Sensores com anomalia", resultado_anomalias["total_anomalias"])

    anomalias_df = montar_df_anomalias(resultado_anomalias)
    if not anomalias_df.empty:
        st.dataframe(
            anomalias_df,
            hide_index=True,
        )
    else:
        st.success("Nenhuma anomalia relevante detectada na janela recente.")

st.subheader("Leituras recentes")
with st.expander("Ver dados brutos"):
    if df.empty:
        st.write("Sem dados para exibir")
    else:
        st.dataframe(df, hide_index=True)