import streamlit as st
import pandas as pd
from db.crud import get_bancadas, get_raw_recent, get_sensor_proc_ultimo

st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

# st.title("🌱 HydroTwin")

# st.header("Monitoramento")

# st.markdown(
#     """
#     - Seleção de bancada
#     - Gráficos em tempo real (Um por variável) 👉 linha temporal
#     - Faixas ideais (gráfico de zonas)
#     - Estado atual + score
#     - Histórico / log de eventos
#     - Média suavizada (média móvel) para identificar tendências
#     """)

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
    st.info("Ainda não há agregação em sensor_proc para esta bancada. Assim que a próxima leitura bruta entrar, o cálculo será gerado automaticamente.")

if not df.empty:
    df["dth_recebido"] = pd.to_datetime(df["dth_recebido"])
    df = df.sort_values("dth_recebido")
else:
    st.warning("Sem leituras brutas recentes para exibir gráficos.")

# GRÁFICOS PRINCIPAIS
st.subheader("Temperatura")
if not df.empty:
    st.line_chart(df.set_index("dth_recebido")["temperatura_ambiente"])

st.subheader("pH")
if not df.empty:
    st.line_chart(df.set_index("dth_recebido")["ph"])

# SECUNDÁRIOS
col1, col2 = st.columns(2)

col1.subheader("TDS")
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

st.subheader("Leituras recentes")
with st.expander("Ver dados brutos"):
    if df.empty:
        st.write("Sem dados para exibir")
    else:
        st.dataframe(df, hide_index=True)