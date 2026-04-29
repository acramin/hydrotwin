DEFAULT_LIMITES = {
    "ph": (5.5, 6.8),
    "ec": (0.8, 1.8),
    "temperatura_ambiente": (18.0, 26.0),
    "temperatura_agua": (10.0, 30.0),
    "luminosidade": (12.0, None),
    "vazao": (None, None),
    "nivel_tanque": (20.0, 30.0),
    "umidade": (45.0, 75.0),
}

ROTULO_METRICA = {
    "ph": "pH",
    "ec": "EC",
    "temperatura_ambiente": "Temperatura ambiente",
    "temperatura_agua": "Temperatura da agua",
    "luminosidade": "Luminosidade",
    "vazao": "Vazao",
    "nivel_tanque": "Nivel do tanque",
    "umidade": "Umidade",
}

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

TIPOS_ALERTA_RISCO = ("RISCO_ATENCAO", "RISCO_CRITICO")