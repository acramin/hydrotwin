from math import isnan

from default import DEFAULT_LIMITES

# utils para normalização e conversão de dados
def to_float(valor):
	if valor is None:
		return None

	try:
		numero = float(valor)
	except (TypeError, ValueError):
		return None

	if isnan(numero):
		return None

	return numero


def normalizar_limites(limites):
	if limites is None:
		return DEFAULT_LIMITES
	return limites


## utils de formatação de data e hora
from datetime import datetime, timedelta
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