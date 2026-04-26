from __future__ import annotations

import pandas as pd

from core.classificar import score_para_status

from default import METRICAS_CONFIG


MIN_AMOSTRAS_OPERACIONAL = 12
PESO_CONSISTENCIA = 0.4
PESO_FORCA = 0.3
PESO_ESTABILIDADE = 0.2
PESO_AMOSTRAS = 0.1


def _tendencia_from_slope(slope, tolerancia=1e-6):
	if slope > tolerancia:
		return "Subindo"
	if slope < -tolerancia:
		return "Descendo"
	return "Estável"


def _suavizar_serie(serie):
	n = len(serie)
	if n < 3:
		return serie

	span = max(3, min(8, n // 6 if n >= 12 else 3))
	return serie.ewm(span=span, adjust=False).mean()


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


def _consistencia_direcional(deltas, direcao, tolerancia):
	if not deltas:
		return 0.0

	sinais_validos = []
	for delta in deltas:
		if abs(delta) <= tolerancia:
			continue
		sinais_validos.append(1 if delta > 0 else -1)

	if not sinais_validos or direcao == 0:
		return 0.0

	mesma_direcao = sum(1 for sinal in sinais_validos if sinal == direcao)
	return round((mesma_direcao / len(sinais_validos)) * 100, 1)


def _forca_tendencia(slope, valores_suavizados):
	media = float(valores_suavizados.mean()) if len(valores_suavizados) else 0.0
	desvio = float(valores_suavizados.std(ddof=0)) if len(valores_suavizados) > 1 else 0.0
	escala = max(abs(media), desvio, 1e-6)
	forca = min(100.0, abs(slope) / escala * 100.0)
	return round(forca, 1)


def _estabilidade(deltas, valores_suavizados):
	if len(deltas) < 2:
		return 100.0

	media = float(valores_suavizados.mean()) if len(valores_suavizados) else 0.0
	volatilidade = float(pd.Series(deltas).std(ddof=0)) if len(deltas) > 1 else 0.0
	base = max(abs(media), 1e-6)
	indice = min(1.0, volatilidade / base)
	return round(max(0.0, 100.0 - (indice * 100.0)), 1)


def _score_operacional(consistencia, forca, estabilidade, qtd_amostras):
	fator_amostras = min(100.0, (qtd_amostras / float(MIN_AMOSTRAS_OPERACIONAL)) * 100.0)
	score = (
		PESO_CONSISTENCIA * consistencia
		+ PESO_FORCA * forca
		+ PESO_ESTABILIDADE * estabilidade
		+ PESO_AMOSTRAS * fator_amostras
	)
	return round(min(100.0, score), 1)


def prever_estado(df, limites=None, min_amostras=MIN_AMOSTRAS_OPERACIONAL, horizonte_max_horas=24, janela_pontos=120):
	if df is None or df.empty:
		return {
			"status": "Sem dados",
			"score": 0.0,
			"resumo": "Sem dados suficientes para prever o comportamento.",
			"total_previsoes": 0,
			"previsoes": [],
		}

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
		n_amostras = len(base)
		if n_amostras < max(min_amostras, MIN_AMOSTRAS_OPERACIONAL):
			continue

		base = base.sort_values("dth_recebido")
		base["suavizado"] = _suavizar_serie(base["valor"])
		valores_suavizados = base["suavizado"].astype(float).tolist()
		if len(valores_suavizados) < 2:
			continue

		tempo_inicial = base["dth_recebido"].iloc[0]
		tempos_horas = ((base["dth_recebido"] - tempo_inicial).dt.total_seconds() / 3600.0).tolist()
		ajuste = _regressao_linear(tempos_horas, valores_suavizados)
		if ajuste is None:
			continue

		slope, intercepto, r2 = ajuste
		if abs(slope) <= 1e-9 and r2 < 0.1:
			continue

		valor_atual = float(base["valor"].iloc[-1])
		valor_suavizado_atual = float(valores_suavizados[-1])
		deltas = base["suavizado"].diff().dropna().tolist()
		epsilon = max(1e-6, float(pd.Series(deltas).std(ddof=0)) * 0.15 if len(deltas) > 1 else 1e-6)
		direcao = 1 if slope > epsilon else (-1 if slope < -epsilon else 0)
		consistencia = _consistencia_direcional(deltas, direcao, epsilon)
		forca = _forca_tendencia(slope, base["suavizado"])
		estabilidade = _estabilidade(deltas, base["suavizado"])
		confianca = round(min(100.0, 0.6 * consistencia + 0.4 * estabilidade), 1)
		score = _score_operacional(consistencia, forca, estabilidade, n_amostras)
		tendencia = _tendencia_from_slope(slope)
		nome = config.get("label", metrica)
		unidade = config.get("unidade", "")
		sufixo_unidade = f" {unidade}" if unidade else ""

		mensagem = (
			f"{nome} em tendência de {tendencia.lower()} com base em série suavizada. "
			f"Consistência: {consistencia:.1f}%, força: {forca:.1f}%, estabilidade: {estabilidade:.1f}%.")

		previsoes.append(
			{
				"sensor": metrica,
				"nome": nome,
				"tendencia": tendencia,
				"valor_atual": round(valor_atual, 3),
				"valor_suavizado": round(valor_suavizado_atual, 3),
				"unidade": unidade,
				"n_amostras": n_amostras,
				"slope_hora": round(slope, 4),
				"r2": round(r2, 3),
				"consistencia": consistencia,
				"forca": forca,
				"estabilidade": estabilidade,
				"confianca": confianca,
				"score": score,
				"mensagem": mensagem
				+ (
					f" Valor atual: {valor_atual:.3f}{sufixo_unidade}."
					if sufixo_unidade
					else f" Valor atual: {valor_atual:.3f}."
				),
			}
		)

	previsoes.sort(key=lambda item: (-item["score"], -item["consistencia"], -abs(item["slope_hora"])))
	if previsoes:
		principal = previsoes[0]
		score_geral = round(max(item["score"] for item in previsoes), 1)
		status = score_para_status(score_geral)
		resumo = principal["mensagem"]
	else:
		score_geral = 0.0
		status = "Sem previsão"
		resumo = (
			"Nenhuma tendência operacional confiável foi encontrada "
			"na janela analisada."
		)

	return {
		"status": status,
		"score": score_geral,
		"resumo": resumo,
		"total_previsoes": len(previsoes),
		"previsoes": previsoes,
	}
