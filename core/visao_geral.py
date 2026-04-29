import pandas as pd
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.crud import *
from others.utils import formatar_data

def get_last_status():
    status = {}
    
    for bancada_id, nome, *_ in get_bancadas():
        
        if not bancada_id:
            return
        
        leitura = get_sensor_proc_ultimo(bancada_id)

        if leitura:
            status[nome] = leitura.get("status_exibicao")
            status["atualizado_em"] = formatar_data(leitura["dth_calculado"])
            continue
        else:
            status[nome] = "Sem dados"
            status["atualizado_em"] = "N/A"

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
    
    for bancada_id, nome, *_ in get_bancadas():
        alertas_bancada = get_alertas_ativos(bancada_id)
        for alerta in alertas_bancada:
            alertas.append(f"{nome}: {alerta['mensagem']}")

    return alertas