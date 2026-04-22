import streamlit as st
import pandas as pd
from db.crud import get_bancadas, get_raw_recent, get_sensor_proc_ultimo
from core.anomalias import detectar_anomalias

st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

# st.markdown(
#     """
#     - Seleção de bancada
#     - Gráficos em tempo real (Um por variável) 👉 linha temporal
#     - Faixas ideais (gráfico de zonas)
#     - Estado atual + score
#     - Histórico / log de eventos
#     - Média suavizada (média móvel) para identificar tendências
#     """)

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

df = get_raw_recent(bancada_id=bancada_id, horas=24)
proc = get_sensor_proc_ultimo(bancada_id)

# STATUS + SCORE
col1, col2 = st.columns(2)
if proc:
    col1.metric("Status", proc["status"])
    col2.metric("Risk Score", f'{proc["score"]:.1f}')
    st.caption(f'Janela processada: {proc["janela_horaria"]} | Amostras: {proc["n_amostras"]} | Atualizado em: {proc["dth_calculado"]}')
else:
    col1.metric("Status", "Sem dados")
    col2.metric("Risk Score", "-")
    st.info("Ainda não há agregação para esta bancada. Assim que a próxima leitura bruta entrar, o cálculo será gerado automaticamente.")
    st.stop()

if not df.empty:
    df["dth_recebido"] = pd.to_datetime(df["dth_recebido"])
    df = df.sort_values("dth_recebido")
    resultado_anomalias = detectar_anomalias(df)
else:
    resultado_anomalias = None
    st.warning("Sem leituras brutas recentes para exibir gráficos.")
    st.stop()

# GRÁFICOS PRINCIPAIS
st.subheader("Temperatura")
if not df.empty:
    st.line_chart(df.set_index("dth_recebido")["temperatura_ambiente"])

st.subheader("pH")
if not df.empty:
    st.line_chart(df.set_index("dth_recebido")["ph"])

# SECUNDÁRIOS
col1, col2 = st.columns(2)

col1.subheader("EC")
if not df.empty:
    col1.line_chart(df.set_index("dth_recebido")["ec"])

col2.subheader("Nível de Água")
if not df.empty:
    col2.line_chart(df.set_index("dth_recebido")["nivel_tanque"])

if proc and proc.get("detalhes"):
    st.subheader("Contribuição do risco")
    risco_df = pd.DataFrame(
        sorted(proc["detalhes"].items(), key=lambda item: item[1], reverse=True),
        columns=["sensor", "risco_%"],
    )
    st.dataframe(risco_df, hide_index=True)

st.subheader("Detecção de anomalias")
if not resultado_anomalias:
    st.info("Sem dados suficientes para detectar anomalias.")
else:
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Status de anomalia", resultado_anomalias["status"])
    col_b.metric("Anomaly Score", f'{resultado_anomalias["score"]:.1f}')
    col_c.metric("Sensores com anomalia", resultado_anomalias["total_anomalias"])

    if resultado_anomalias["anomalias"]:
        anomalias_df = pd.DataFrame(resultado_anomalias["anomalias"])
        st.dataframe(
            anomalias_df[
                [
                    "nome",
                    "severidade",
                    "score",
                    "valor_atual",
                    "mediana",
                    "z_score",
                    "n_amostras",
                    "mensagem",
                ]
            ],
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