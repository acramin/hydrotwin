from __future__ import annotations

from math import isnan

from utils import to_float
from default import DEFAULT_LIMITES

PESOS_PADRAO = {
    "ph": 0.24,
    "ec": 0.24,
    "temperatura_ambiente": 0.18,
    "temperatura_agua": 0.16,
    "luminosidade": 0.08,
    "vazao": 0.04,
    "nivel_tanque": 0.03,
    "umidade": 0.03,
}

def _status_from_score(score):
    if score <= 33:
        return "Saudável"
    if score <= 66:
        return "Atenção"
    return "Crítico"


def _interval_risk(mean, std, limite_min, limite_max):
    if mean is None:
        return 0.0

    if limite_min is None and limite_max is None:
        return min(1.0, (std or 0.0) / max(abs(mean), 1.0)) * 0.35

    if limite_min is not None and limite_max is not None:
        amplitude = max(limite_max - limite_min, 1e-6)
        centro = (limite_min + limite_max) / 2
        metade = amplitude / 2
        distancia_centro = abs(mean - centro)

        if mean < limite_min:
            excesso = (limite_min - mean) / amplitude
            risco_base = 0.72 + min(0.28, excesso)
        elif mean > limite_max:
            excesso = (mean - limite_max) / amplitude
            risco_base = 0.72 + min(0.28, excesso)
        else:
            proximidade_borda = max(0.0, 1.0 - (metade - distancia_centro) / max(metade, 1e-6))
            risco_base = proximidade_borda * 0.35

        variabilidade = min(1.0, (std or 0.0) / max(amplitude * 0.25, 1e-6))
        return min(1.0, 0.75 * risco_base + 0.25 * variabilidade)

    if limite_min is not None:
        if mean < limite_min:
            excesso = (limite_min - mean) / max(abs(limite_min), 1.0)
            return min(1.0, 0.8 + excesso)

        variabilidade = min(1.0, (std or 0.0) / max(abs(limite_min), 1.0))
        return variabilidade * 0.25

    if limite_max is not None:
        if mean > limite_max:
            excesso = (mean - limite_max) / max(abs(limite_max), 1.0)
            return min(1.0, 0.8 + excesso)

        variabilidade = min(1.0, (std or 0.0) / max(abs(limite_max), 1.0))
        return variabilidade * 0.25

    return 0.0


def _estatistica(linha, chave, sufixo):
    valor = linha.get(f"{chave}_{sufixo}")
    return to_float(valor)


def calcular_risco_estatistico(estatisticas, cultura=None):
    cultura = cultura or {}
    pesos = PESOS_PADRAO.copy()
    contribs = {}
    soma_pesos = 0.0
    soma_ponderada = 0.0

    for metrica, peso in pesos.items():
        media = _estatistica(estatisticas, metrica, "mean")
        desvio = _estatistica(estatisticas, metrica, "std")
        quantidade = _estatistica(estatisticas, metrica, "count")

        if quantidade is None or quantidade <= 0 or media is None:
            continue

        limite_min = cultura.get(f"{metrica}_min")
        limite_max = cultura.get(f"{metrica}_max")
        
        #print(limite_max, limite_min)

        if limite_min is None and limite_max is None:
            limite_min, limite_max = DEFAULT_LIMITES.get(metrica, (None, None))

        risco = _interval_risk(media, desvio, to_float(limite_min), to_float(limite_max))

        amostras = _estatistica(estatisticas, metrica, "min")
        maximo = _estatistica(estatisticas, metrica, "max")
        amplitude_observada = None
        if amostras is not None and maximo is not None:
            amplitude_observada = maximo - amostras
            if amplitude_observada > 0:
                risco = min(1.0, risco + min(0.15, amplitude_observada / max(abs(media), 1.0) * 0.03))

        contribs[metrica] = round(risco * 100, 1)
        soma_ponderada += risco * peso
        soma_pesos += peso

    score = 0.0 if soma_pesos == 0 else round((soma_ponderada / soma_pesos) * 100, 1)

    return {
        "score": score,
        "status": _status_from_score(score),
        "detalhes": contribs,
    }


def score_para_status(score):
    return _status_from_score(to_float(score) or 0.0)


def _normalizar_status(status):
    if not status:
        return "Sem dados"
    if status == "Estável":
        return "Saudável"
    return status


def calcular_status_consolidado(
    risco_score,
    anomalia_score,
    tendencia_score,
    risco_status=None,
    anomalia_status=None,
    tendencia_status=None,
):
    risco_score = to_float(risco_score) or 0.0
    anomalia_score = to_float(anomalia_score) or 0.0
    tendencia_score = to_float(tendencia_score) or 0.0

    risco_status_norm = _normalizar_status(risco_status or score_para_status(risco_score))
    anomalia_status_norm = _normalizar_status(anomalia_status or score_para_status(anomalia_score))
    tendencia_status_norm = _normalizar_status(tendencia_status or score_para_status(tendencia_score))

    score = max(risco_score, anomalia_score, tendencia_score)

    if risco_score >= 67 or anomalia_score >= 85:
        return {
            "status": "Crítico",
            "score": round(score, 1),
            "motivo": "Risco atual elevado ou anomalia crítica detectada.",
            "componentes": {
                "risco": risco_status_norm,
                "anomalia": anomalia_status_norm,
                "tendencia": tendencia_status_norm,
            },
        }

    if risco_score >= 34 or anomalia_score >= 60 or tendencia_score >= 67:
        return {
            "status": "Atenção",
            "score": round(score, 1),
            "motivo": "Algum indicador aponta atenção ou tendência de piora.",
            "componentes": {
                "risco": risco_status_norm,
                "anomalia": anomalia_status_norm,
                "tendencia": tendencia_status_norm,
            },
        }

    return {
        "status": "Saudável",
        "score": round(score, 1),
        "motivo": "Indicadores de risco, anomalia e tendência dentro do esperado.",
        "componentes": {
            "risco": risco_status_norm,
            "anomalia": anomalia_status_norm,
            "tendencia": tendencia_status_norm,
        },
    }

