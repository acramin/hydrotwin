import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from db.crud import get_bancadas, get_culturas, inserir_bancada, inserir_filete

st.set_page_config(page_title="Hydroponic Monitor", layout="wide", page_icon="🌱")

st.title("🌱 HydroTwin")

st.header("Monitoramento")

# conexão com banco
conn = sqlite3.connect("db\\hydroponic.db")

# carregar dados
df = pd.read_sql("""
SELECT * FROM sensor_raw
ORDER BY dth_recebido DESC
""", conn)

if df.empty:
    st.warning("Sem dados ainda...")
    st.stop()

# converter tempo
df["dth_recebido"] = pd.to_datetime(df["dth_recebido"])

# -----------------------------
# KPIs (última leitura)
# -----------------------------
ultima = df.iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric("pH", round(ultima["ph"], 2))
col2.metric("Temperatura (°C)", round(ultima["temperatura"], 2))
col3.metric("Condutividade", round(ultima["condutividade"], 2))

# -----------------------------
# Classificação
# -----------------------------
def classificar(ph, temp, cond):
    score = 0

    if ph < 5.8 or ph > 7.2:
        score += 2
    elif ph < 6.0 or ph > 7.0:
        score += 1

    if temp < 18 or temp > 26:
        score += 2
    elif temp < 20 or temp > 24:
        score += 1

    if cond < 1.2 or cond > 2.2:
        score += 2
    elif cond < 1.4 or cond > 2.0:
        score += 1

    if score <= 2:
        return "🟢 Saudável"
    elif score <= 4:
        return "🟡 Atenção"
    else:
        return "🔴 Crítico"

status = classificar(
    ultima["ph"],
    ultima["temperatura"],
    ultima["condutividade"]
)

st.subheader(f"Status Atual: {status}")

# -----------------------------
# Gráficos
# -----------------------------
st.subheader("📈 Histórico")

df_sorted = df.sort_values("dth_recebido")

st.line_chart(df_sorted.set_index("dth_recebido")[["ph"]])
st.line_chart(df_sorted.set_index("dth_recebido")[["temperatura"]])
st.line_chart(df_sorted.set_index("dth_recebido")[["condutividade"]])

df_filete = pd.read_sql("""
SELECT 
    f.bancada_id,
    julianday('now') - julianday(f.data_plantio) AS idade_dias
FROM filetes f
""", conn)

st.subheader("🌿 Idade dos Filetes")

st.dataframe(df_filete)

# -----------------------------
# Tabela
# -----------------------------
with st.expander("Ver dados brutos"):
    st.dataframe(df)