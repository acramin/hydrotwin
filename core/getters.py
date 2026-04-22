import pandas as pd
from datetime import datetime, timedelta

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.crud import *

## utils
def formatar_data(dth):
    if not isinstance(dth, datetime):
        dth = datetime.strptime(dth, "%Y-%m-%d %H:%M:%S")
    if not dth:
        return "N/A"
    return dth.strftime("%d/%m/%Y %H:%M:%S")

def formatar_data_relativa(dth):
    if not isinstance(dth, datetime):
        dth = datetime.strptime(dth, "%Y-%m-%d %H:%M:%S")
    if not dth:
        return "N/A"
    
    agora = datetime.now()
    delta = agora - dth

    if delta < timedelta(minutes=1):
        return "Agora"
    elif delta < timedelta(hours=1):
        minutos = int(delta.total_seconds() // 60)
        return f"{minutos} min atrás"
    elif delta < timedelta(days=1):
        horas = int(delta.total_seconds() // 3600)
        return f"{horas} h atrás"
    else:
        dias = delta.days
        return f"{dias} dia(s) atrás"

def formatar_horario(dth):
    if not isinstance(dth, datetime):
        dth = datetime.strptime(dth, "%Y-%m-%d %H:%M:%S")
    if not dth:
        return "N/A"
    return dth.strftime("%H:%M:%S")

## Getters da One Page
def get_last_status():
    status = {}
    
    for bancada_id, nome, *_ in get_bancadas():
        
        if not bancada_id:
            return
        
        leitura = get_sensor_proc_ultimo(bancada_id)
        dth_calculado = 'atualizado_em' if leitura else None

        if leitura:
            status[nome] = leitura["status"]
            continue
        else:
            status[nome] = "Sem dados"
    
        status[dth_calculado] = formatar_horario(leitura["dth_calculado"]) if dth_calculado else "N/A"
        
    return status

def get_kpis(bancada_id, nome):
    kpis = {}
    
    leitura = get_sensor_proc_ultimo(bancada_id)
    
    if leitura:
        kpis[nome] = {}
        kpis[nome]["nível tanque"] = "OK" if leitura["nivel_tanque_mean"] > 50 else "Baixo"
        kpis[nome]["ph"] = leitura["ph_mean"]
        kpis[nome]["ec"] = leitura["ec_mean"]
        kpis[nome]["umidade"] = leitura["umidade_mean"]
        kpis[nome]["temperatura_ambiente"] = leitura["temperatura_ambiente_mean"]
        kpis[nome]["temperatura_água"] = leitura["temperatura_agua_mean"]
        kpis[nome]["luminosidade"] = leitura["luminosidade_mean"]
        kpis[nome]["vazão_água"] = leitura["vazao_mean"]

    return kpis

def get_alertas():
    alertas = []
    
    for bandada_id, nome, *_ in get_bancadas():
        alertas_bancada = get_alertas_ativos(bandada_id)
        for alerta in alertas_bancada:
            alertas.append(f"{nome}: {alerta['mensagem']}")

    return alertas

# ## Getters para a Dashboard
# def get_status():
#     ## pra que? onde vai usar? precisamos disso? talvez seja melhor só ter o get_last_status e deixar o score pra outro getter específico
#     status = {}
    
#     for bancada_id, nome, *_ in get_bancadas():
#         leitura = get_proc_recent(bancada_id)

#         if leitura:
#             status[nome] = {
#                 "status": leitura["status"],
#                 "score": leitura["score"]
#             }
#             continue
#         else:
#             status[nome] = {
#                 "status": "Sem dados",
#                 "score": None
#             }
        
#     return status

# def get_time_series():
#     now = datetime.now()
#     times = [now - timedelta(seconds=i*5) for i in range(20)][::-1]

#     df = pd.DataFrame({
#         "time": times,
#         "temp": [random.uniform(22, 28) for _ in times],
#         "ph": [random.uniform(5.5, 7.5) for _ in times],
#         "tds": [random.randint(700, 1200) for _ in times],
#         "nivel": [random.uniform(0, 1) for _ in times]
#     })

#     return df

# def get_eventos():
    # return [
    #     "14:32 → pH fora do ideal",
    #     "14:35 → pH voltou ao normal",
    #     "14:40 → nível caiu"
    # ]