from __future__ import annotations

from math import isnan

import pandas as pd

from utils import normalizar_limites, to_float
from default import METRICAS_CONFIG


def _status_from_score(score):
	if score >= 85:
		return "Crítico"
	if score >= 60:
		return "Atenção"
	return "Estável"


def _zscore_robusto(serie):
	mediana = float(serie.median())
	mad = float((serie - mediana).abs().median())

	q1 = float(serie.quantile(0.25))
	q3 = float(serie.quantile(0.75))
	iqr = max(0.0, q3 - q1)

	desvio = float(serie.std(ddof=0))
	escala = max(mad * 1.4826, iqr / 1.349 if iqr > 0 else 0.0, desvio, 1e-6)

	valor_atual = float(serie.iloc[-1])
	z = abs(valor_atual - mediana) / escala

	return z, valor_atual, mediana, escala


def _score_por_limite(valor_atual, limite_min, limite_max):
	score = 0.0
	motivo = None

	if limite_min is not None and valor_atual < limite_min:
		distancia = (limite_min - valor_atual) / max(abs(limite_min), 1.0)
		score = 70 + min(30, distancia * 100)
		motivo = f"abaixo do limite mínimo ({limite_min:.2f})"
	elif limite_max is not None and valor_atual > limite_max:
		distancia = (valor_atual - limite_max) / max(abs(limite_max), 1.0)
		score = 70 + min(30, distancia * 100)
		motivo = f"acima do limite maximo ({limite_max:.2f})"

	return score, motivo


def detectar_anomalias(df, limites=None, min_amostras=12):
	if df is None or df.empty:
		return {
			"status": "Sem dados",
			"score": 0.0,
			"total_anomalias": 0,
			"anomalias": [],
			"detalhes": {},
		}

	limites = normalizar_limites(limites)

	anomalias = []
	detalhes = {}

	for metrica, config in METRICAS_CONFIG.items():
		if metrica not in df.columns:
			continue

		serie = pd.to_numeric(df[metrica], errors="coerce").dropna()
		if serie.empty:
			continue

		quantidade = int(serie.count())
		valor_atual = float(serie.iloc[-1])
		limite_min, limite_max = limites.get(metrica, (None, None))
		limite_min = to_float(limite_min)
		limite_max = to_float(limite_max)

		score_limite, motivo_limite = _score_por_limite(valor_atual, limite_min, limite_max)

		score_modelo = 0.0
		z_score = 0.0
		mediana = float(serie.median())

		if quantidade >= min_amostras:
			z_score, valor_atual, mediana, _ = _zscore_robusto(serie)
			score_modelo = min(100.0, z_score * 22.0)

		score_sensor = max(score_modelo, score_limite)
		detalhes[metrica] = round(score_sensor, 1)

		if score_sensor < 60:
			continue

		unidade = config.get("unidade", "")
		sufixo_unidade = f" {unidade}" if unidade else ""
		motivo = motivo_limite or "desvio estatistico da serie recente"

		anomalias.append(
			{
				"sensor": metrica,
				"nome": config.get("label", metrica),
				"severidade": _status_from_score(score_sensor),
				"score": round(score_sensor, 1),
				"valor_atual": round(valor_atual, 3),
				"mediana": round(mediana, 3),
				"z_score": round(z_score, 3),
				"limite_min": limite_min,
				"limite_max": limite_max,
				"n_amostras": quantidade,
				"mensagem": (
					f"{config.get('label', metrica)} em {valor_atual:.3f}{sufixo_unidade}; "
					f"motivo: {motivo}."
				),
			}
		)

	anomalias.sort(key=lambda item: item["score"], reverse=True)

	if anomalias:
		top_scores = [item["score"] for item in anomalias[:3]]
		score_geral = round(sum(top_scores) / len(top_scores), 1)
	else:
		score_geral = round(max(detalhes.values()) if detalhes else 0.0, 1)

	return {
		"status": _status_from_score(score_geral) if detalhes else "Sem dados",
		"score": score_geral,
		"total_anomalias": len(anomalias),
		"anomalias": anomalias,
		"detalhes": detalhes,
	}
