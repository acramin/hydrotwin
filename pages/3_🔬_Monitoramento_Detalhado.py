import streamlit as st
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.crud import get_bancadas
from db.auth import render_auth_gate
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

render_auth_gate("HydroTwin")

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
st.subheader("Status consolidado do sistema", help="Como o sistema está operando agora? \n\nStatus consolidado combina risco atual, anomalias e tendência operacional para reduzir ambiguidades na interpretação.")
col1, col2, col3 = st.columns(3)
if proc:
    status_consolidado = proc.get("consolidado_status") or proc["status"]
    score_consolidado = proc.get("consolidado_score")
    motivo_consolidado = proc.get("consolidado_motivo") or "Sem motivo consolidado disponível para esta leitura."

    col1.metric(
        "Status consolidado",
        status_consolidado,
        help="Classificação unificada para evitar conflito entre risco, anomalia e tendência."
    )
    col2.metric(
        "Score consolidado",
        f'{(score_consolidado if score_consolidado is not None else proc["score"]):.1f}',
        help=(
            "Score consolidado (0-100): maior severidade observada entre risco atual, anomalia e tendência operacional."
        )
    )
    col3.metric(
        "Score de risco",
        f'{proc["score"]:.1f}',
        help="Score de risco estatístico da janela processada."
    )
    st.caption(f"Motivo do consolidado: {motivo_consolidado}")
    st.caption(f'Janela processada: {proc["janela_horaria"]} | Amostras: {proc["n_amostras"]} | Atualizado em: {formatar_data(proc["dth_calculado"])}')
else:
    col1.metric("Status consolidado", "Sem dados")
    col2.metric("Score consolidado", "-")
    col3.metric("Score de risco", "-")
    st.info("Ainda não há agregação para esta bancada. Assim que a próxima leitura bruta entrar, o cálculo será gerado automaticamente.")
    st.stop()

if df.empty:
    st.warning("Sem leituras brutas recentes para exibir gráficos.")
    st.stop()

# GRÁFICOS DE ZONA (candidatos fortes)
st.subheader("Gráficos por variável", help="Visualize a evolução de cada métrica ao longo do tempo. \n\nModo 'Zona': gráficos com faixas de risco coloridas, baseados nos limites da bancada, para destacar rapidamente quando uma métrica está em zona de atenção ou crítica. \n\nModo 'Linha': gráficos tradicionais de linha, focando na tendência temporal sem sobreposição de zonas.")
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

st.subheader("Detecção de anomalias", help="Identifique comportamentos incomuns nos dados. \n\nAnomalias são pontos de dados que se desviam significativamente do comportamento esperado, indicando possíveis problemas no sistema.")
if not resultado_anomalias:
    st.info("Sem dados suficientes para detectar anomalias.")
else:
    anomalia_status = proc.get("anomalia_status") if proc else resultado_anomalias["status"]
    anomalia_score = proc.get("anomalia_score") if proc else resultado_anomalias["score"]

    col_a, col_b, col_c = st.columns(3)
    col_a.metric(
        "Status de anomalia",
        anomalia_status,
        help="Status derivado do Score de Anomalia. \n\nFaixas: 0-59 = Saudável, 60-84 = Atenção, 85-100 = Crítico."
    )
    col_b.metric(
        "Score de Anomalia",
        f'{(anomalia_score if anomalia_score is not None else resultado_anomalias["score"]):.1f}',
        help=(
            "Score de anomalia (0-100): por sensor, usa a pior entre duas lentes: \n\n"
            "(1) desvio estatístico robusto da série recente (z-score) e "
            "(2) violação direta de limite mínimo/máximo. \n\n"
            "O score geral é a média dos 3 maiores scores de anomalia "
            "(ou o maior score monitorado, se não houver anomalias >= 60). "
        ),
    )
    col_c.metric("Sensores com anomalia", resultado_anomalias["total_anomalias"])

    anomalias_df = montar_df_anomalias(resultado_anomalias)
    if not anomalias_df.empty:
        st.dataframe(
            anomalias_df,
            hide_index=True,
        )
    else:
        st.success("Nenhuma anomalia relevante detectada na janela recente.")

st.subheader("Tendência operacional", help="Qual é a direção do sistema? \n\nAnálise de tendência recente para cada sensor, indicando se a métrica está melhorando, piorando ou estável. A previsão geral é derivada do sensor com a tendência mais relevante, mas também mostramos o número total de sensores que indicam uma tendência clara.")
status_tendencia = proc.get("tendencia_status") if proc else resultado_previsao["status"]
score_tendencia = proc.get("tendencia_score") if proc else resultado_previsao["score"]
col_a, col_b, col_c = st.columns(3)
col_a.metric(
    "Status previsto",
    status_tendencia,
    help=(
        "Status derivado da Previsão geral. \n\n"
        "Faixas: 0-33 = Saudável, 34-66 = Atenção, 67-100 = Crítico."
    ),
)
col_b.metric(
    "Previsão geral",
    f'{(score_tendencia if score_tendencia is not None else resultado_previsao["score"]):.1f}',
    help=(
        "Score de tendência (0-100): mede quão consistente e relevante é a tendência recente. \n\n" 
        "Composição por sensor: Consistência direcional (40%), Força da tendência/slope (30%), "
        "Estabilidade da série suavizada (20%) e quantidade de amostras (10%). \n\n"
        "A previsão geral mostra o maior score entre as tendências observadas. "
    ),
)
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

st.subheader("Leituras recentes")
with st.expander("Ver dados brutos"):
    if df.empty:
        st.write("Sem dados para exibir")
    else:
        st.dataframe(df, hide_index=True)