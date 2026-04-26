from __future__ import annotations

from math import isnan

import pandas as pd

from core.classificar import DEFAULT_LIMITES, score_para_status


METRICAS_CONFIG = {
	"ph": {"label": "pH", "unidade": ""},
	"ec": {"label": "EC", "unidade": "mS/cm"},
	"temperatura_ambiente": {"label": "Temperatura ambiente", "unidade": "C"},
	"temperatura_agua": {"label": "Temperatura água", "unidade": "C"},
	"luminosidade": {"label": "Luminosidade", "unidade": "h"},
	"vazao": {"label": "Vazão", "unidade": "L/min"},
	"nivel_tanque": {"label": "Nível do tanque", "unidade": "%"},
	"umidade": {"label": "Umidade", "unidade": "%"},
}


def _to_float(valor):
	if valor is None:
		return None

	try:
		numero = float(valor)
	except (TypeError, ValueError):
		return None

	if isnan(numero):
		return None

	return numero


def _normalizar_limites(limites):
	return DEFAULT_LIMITES if limites is None else limites


def _tendencia_from_slope(slope, tolerancia=1e-6):
	if slope > tolerancia:
		return "Subindo"
	if slope < -tolerancia:
		return "Descendo"
	return "Estável"


def _regressao_linear(tempos_horas, valores):
	n = len(valores)
	if n < 2:
		return None

	media_x = sum(tempos_horas) / n
	media_y = sum(valores) / n
	ss_xx = sum((x - media_x) ** 2 for x in tempos_horas)
	if ss_xx <= 1e-12:
		return None

	ss_xy = sum((x - media_x) * (y - media_y) for x, y in zip(tempos_horas, valores))
	slope = ss_xy / ss_xx
	intercepto = media_y - slope * media_x
	previstos = [intercepto + slope * x for x in tempos_horas]
	ss_tot = sum((y - media_y) ** 2 for y in valores)
	ss_res = sum((y - y_hat) ** 2 for y, y_hat in zip(valores, previstos))
	r2 = 0.0 if ss_tot <= 1e-12 else max(0.0, 1.0 - (ss_res / ss_tot))

	return slope, intercepto, r2


def _confianca_projecao(qtd_amostras, r2):
	fator_amostras = min(1.0, qtd_amostras / 12.0)
	fator_r2 = min(1.0, max(0.0, r2))
	confianca = (0.45 * fator_amostras + 0.55 * fator_r2) * 100
	return round(confianca, 1)


def _limite_relevante(valor_atual, slope, limite_min, limite_max):
	if limite_min is None and limite_max is None:
		return None, None

	if limite_min is not None and valor_atual < limite_min:
		return limite_min, "mínimo"

	if limite_max is not None and valor_atual > limite_max:
		return limite_max, "máximo"

	if slope > 0 and limite_max is not None:
		return limite_max, "máximo"

	if slope < 0 and limite_min is not None:
		return limite_min, "mínimo"

	return None, None


def _formatar_horas(valor):
	if valor is None:
		return "Sem previsão"
	if valor < 1:
		return "< 1 h"
	return f"{valor:.1f} h"


def _score_previsao(horas_ate_limite, horizonte_max_horas, confianca):
	urgencia = max(0.0, 1.0 - (horas_ate_limite / max(horizonte_max_horas, 1e-6)))
	return round(min(100.0, urgencia * 100.0 * (confianca / 100.0)), 1)


def prever_estado(df, limites=None, min_amostras=8, horizonte_max_horas=24, janela_pontos=12):
	if df is None or df.empty:
		return {
			"status": "Sem dados",
			"score": 0.0,
			"resumo": "Sem dados suficientes para prever o comportamento.",
			"total_previsoes": 0,
			"previsoes": [],
		}

	limites = _normalizar_limites(limites)
	dados = df.copy()
	if "dth_recebido" not in dados.columns:
		return {
			"status": "Sem dados",
			"score": 0.0,
			"resumo": "A série não possui coluna de data para calcular tendência.",
			"total_previsoes": 0,
			"previsoes": [],
		}

	dados["dth_recebido"] = pd.to_datetime(dados["dth_recebido"], errors="coerce")
	dados = dados.dropna(subset=["dth_recebido"]).sort_values("dth_recebido")

	if dados.empty:
		return {
			"status": "Sem dados",
			"score": 0.0,
			"resumo": "A série não possui leituras válidas para prever comportamento.",
			"total_previsoes": 0,
			"previsoes": [],
		}

	dados = dados.tail(max(min_amostras, janela_pontos))
	previsoes = []

	for metrica, config in METRICAS_CONFIG.items():
		if metrica not in dados.columns:
			continue

		serie = pd.to_numeric(dados[metrica], errors="coerce")
		base = pd.DataFrame({"dth_recebido": dados["dth_recebido"], "valor": serie}).dropna()
		if len(base) < min_amostras:
			continue

		base = base.sort_values("dth_recebido")
		tempo_inicial = base["dth_recebido"].iloc[0]
		tempos_horas = ((base["dth_recebido"] - tempo_inicial).dt.total_seconds() / 3600.0).tolist()
		valores = base["valor"].astype(float).tolist()
		ajuste = _regressao_linear(tempos_horas, valores)
		if ajuste is None:
			continue

		slope, intercepto, r2 = ajuste
		valor_atual = float(valores[-1])
		tempo_atual = float(tempos_horas[-1])
		limite_min, limite_max = limites.get(metrica, (None, None))
		limite_min = _to_float(limite_min)
		limite_max = _to_float(limite_max)
		limite_relevante, tipo_limite = _limite_relevante(valor_atual, slope, limite_min, limite_max)

		if limite_relevante is None or abs(slope) <= 1e-9:
			continue

		hora_cruzamento = (limite_relevante - valor_atual) / slope
		if hora_cruzamento < 0:
			continue

		horas_ate_limite = round(hora_cruzamento, 2)
		if horas_ate_limite > horizonte_max_horas:
			continue

		confianca = _confianca_projecao(len(base), r2)
		score = _score_previsao(horas_ate_limite, horizonte_max_horas, confianca)
		valor_1h = intercepto + slope * (tempo_atual + 1.0)
		valor_3h = intercepto + slope * (tempo_atual + 3.0)
		tendencia = _tendencia_from_slope(slope)
		nome = config.get("label", metrica)
		unidade = config.get("unidade", "")
		sufixo_unidade = f" {unidade}" if unidade else ""

		mensagem = (
			f"{nome} pode atingir o limite {tipo_limite} em {_formatar_horas(horas_ate_limite)} "
			f"se a tendência atual persistir."
		)

		previsoes.append(
			{
				"sensor": metrica,
				"nome": nome,
				"tendencia": tendencia,
				"valor_atual": round(valor_atual, 3),
				"unidade": unidade,
				"limite_tipo": tipo_limite,
				"limite_valor": round(limite_relevante, 3),
				"horas_ate_limite": horas_ate_limite,
				"valor_previsto_1h": round(valor_1h, 3),
				"valor_previsto_3h": round(valor_3h, 3),
				"slope_hora": round(slope, 4),
				"r2": round(r2, 3),
				"confianca": confianca,
				"score": score,
				"mensagem": mensagem + (f" Valor atual: {valor_atual:.3f}{sufixo_unidade}." if sufixo_unidade else f" Valor atual: {valor_atual:.3f}.")
			}
		)

	previsoes.sort(key=lambda item: (item["horas_ate_limite"], -item["score"]))
	if previsoes:
		principal = previsoes[0]
		score_geral = round(max(item["score"] for item in previsoes), 1)
		status = score_para_status(score_geral)
		resumo = principal["mensagem"]
	else:
		score_geral = 0.0
		status = "Sem previsão"
		resumo = "Nenhuma tendência confiável projetou cruzamento de limite dentro da janela analisada."

	return {
		"status": status,
		"score": score_geral,
		"resumo": resumo,
		"total_previsoes": len(previsoes),
		"previsoes": previsoes,
	}
