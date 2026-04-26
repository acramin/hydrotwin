from datetime import datetime, timedelta, date
from pathlib import Path
import sqlite3
import pandas as pd
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.classificar import calcular_risco_estatistico, score_para_status, DEFAULT_LIMITES

DB_PATH = Path(__file__).resolve().with_name("hydroponic.db")

TIPOS_ALERTA_RISCO = ("RISCO_ATENCAO", "RISCO_CRITICO")

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

def _connect():
    return sqlite3.connect(DB_PATH)


def _query_dataframe(query, params=None):
    conn = _connect()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def _valor_cultura(cursor, bancada_id):
    cursor.execute(
        """
        SELECT c.id, c.nome, c.ph_min, c.ph_max, c.ec_min, c.ec_max,
               c.temp_agua_min, c.temp_agua_max, c.luminosidade_min, c.dias_ciclo
        FROM bancada b
        LEFT JOIN cultura c ON c.id = b.cultura_id
        WHERE b.id = ?
        """,
        (bancada_id,),
    )
    linha = cursor.fetchone()

    if not linha or linha[0] is None:
        return {}

    return {
        "id": linha[0],
        "nome": linha[1],
        "ph_min": linha[2],
        "ph_max": linha[3],
        "ec_min": linha[4],
        "ec_max": linha[5],
        "temp_agua_min": linha[6],
        "temp_agua_max": linha[7],
        "luminosidade_min": linha[8],
        "dias_ciclo": linha[9],
    }


def _estatisticas_dataframe(df):
    metricas = [
        "ph",
        "ec",
        "temperatura_ambiente",
        "temperatura_agua",
        "luminosidade",
        "vazao",
        "nivel_tanque",
        "umidade",
    ]

    estatisticas = {}

    for metrica in metricas:
        serie = pd.to_numeric(df.get(metrica), errors="coerce").dropna()

        estatisticas[f"{metrica}_count"] = int(serie.count())
        estatisticas[f"{metrica}_min"] = None if serie.empty else float(serie.min())
        estatisticas[f"{metrica}_max"] = None if serie.empty else float(serie.max())
        estatisticas[f"{metrica}_mean"] = None if serie.empty else float(serie.mean())
        estatisticas[f"{metrica}_std"] = 0.0 if serie.empty else float(serie.std(ddof=0))

    return estatisticas


def _ultimos_status_por_bancada():
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sp.bancada_id, b.nome, sp.score, sp.janela_horaria, sp.dth_calculado
            FROM sensor_proc sp
            JOIN bancada b ON b.id = sp.bancada_id
            WHERE sp.id IN (
                SELECT MAX(id)
                FROM sensor_proc
                GROUP BY bancada_id
            )
            ORDER BY b.nome
            """
        )
        return cursor.fetchall()
    finally:
        conn.close()


def _resumir_maior_contribuicao(detalhes):
    if not detalhes:
        return None

    metrica, risco = max(detalhes.items(), key=lambda item: item[1])
    nome = ROTULO_METRICA.get(metrica, metrica)
    return metrica, nome, risco


def _valor_limite_cultura(cultura, metrica, tipo):
    chave = f"{metrica}_{tipo}"
    if chave in cultura:
        return cultura.get(chave)

    aliases = {
        "temperatura_agua": "temp_agua",
    }

    alias = aliases.get(metrica)
    if alias:
        return cultura.get(f"{alias}_{tipo}")

    return None


def _resolver_limites(cultura, metrica):
    limite_min = _valor_limite_cultura(cultura, metrica, "min")
    limite_max = _valor_limite_cultura(cultura, metrica, "max")

    if limite_min is None and limite_max is None:
        limite_min, limite_max = DEFAULT_LIMITES.get(metrica, (None, None))

    return limite_min, limite_max


def get_limites_bancada(bancada_id):
    conn = _connect()
    try:
        cursor = conn.cursor()
        cultura = _valor_cultura(cursor, bancada_id)

        limites = {}
        for metrica in DEFAULT_LIMITES:
            limites[metrica] = _resolver_limites(cultura, metrica)

        return limites
    finally:
        conn.close()


def _explicacao_da_metrica(metrica, estatisticas, cultura):
    media = estatisticas.get(f"{metrica}_mean")
    limite_min, limite_max = _resolver_limites(cultura or {}, metrica)
    nome = ROTULO_METRICA.get(metrica, metrica)

    if media is None:
        return f"{nome} apresentou comportamento de risco na ultima janela analisada."

    if limite_min is not None and media < limite_min:
        return (
            f"{nome} esta abaixo do limite mínimo ({limite_min:.2f}) "
            f"com media atual de {media:.2f}."
        )

    if limite_max is not None and media > limite_max:
        return (
            f"{nome} esta acima do limite máximo ({limite_max:.2f}) "
            f"com média atual de {media:.2f}."
        )

    if limite_min is not None and limite_max is not None:
        return (
            f"{nome} esta dentro da faixa recomendada ({limite_min:.2f} a {limite_max:.2f}), "
            "mas com variação/proximidade de limite que aumentou o risco."
        )

    if limite_min is not None:
        return (
            f"{nome} esta proximo do limite mínimo recomendado ({limite_min:.2f}), "
            f"com média atual de {media:.2f}."
        )

    if limite_max is not None:
        return (
            f"{nome} esta proximo do limite máximo recomendado ({limite_max:.2f}), "
            f"com média atual de {media:.2f}."
        )

    return f"{nome} apresentou comportamento de risco na ultima janela analisada."


def _resumo_contribuicoes(detalhes, ignorar_metrica=None, limite_itens=3):
    if not detalhes:
        return None

    ordenadas = sorted(detalhes.items(), key=lambda item: item[1], reverse=True)
    filtradas = [item for item in ordenadas if item[0] != ignorar_metrica]

    if not filtradas:
        return None

    partes = []
    for metrica, percentual in filtradas[:limite_itens]:
        nome = ROTULO_METRICA.get(metrica, metrica)
        partes.append(f"{nome}: {percentual:.1f}%")

    return "; ".join(partes)


def _mensagem_alerta_risco(status, detalhes, estatisticas, cultura):
    principal = _resumir_maior_contribuicao(detalhes)
    if principal is None:
        return None, None

    metrica_principal, nome_principal, percentual_principal = principal
    explicacao = _explicacao_da_metrica(metrica_principal, estatisticas, cultura)
    demais = _resumo_contribuicoes(detalhes, ignorar_metrica=metrica_principal)

    if status == "Crítico":
        mensagem = (
            f"Risco critico detectado em {nome_principal} "
            f"(contribuicao de {percentual_principal:.1f}%). {explicacao}"
        )
        if demais:
            mensagem = f"{mensagem} Demais contribuicoes: {demais}."
        return "RISCO_CRITICO", mensagem

    if status == "Atenção":
        mensagem = (
            f"Atencao necessaria em {nome_principal} "
            f"(contribuicao de {percentual_principal:.1f}%). {explicacao}"
        )
        if demais:
            mensagem = f"{mensagem} Demais contribuicoes: {demais}."
        return "RISCO_ATENCAO", mensagem

    return None, None


def _sincronizar_alerta_risco(cursor, bancada_id, status, detalhes, estatisticas, cultura):
    novo_tipo, nova_mensagem = _mensagem_alerta_risco(status, detalhes, estatisticas, cultura)

    cursor.execute(
        """
        SELECT id, tipo, mensagem
        FROM alerta
        WHERE bancada_id = ?
          AND dth_resolvido IS NULL
          AND tipo IN (?, ?)
        ORDER BY dth_criado DESC, id DESC
        """,
        (bancada_id, TIPOS_ALERTA_RISCO[0], TIPOS_ALERTA_RISCO[1]),
    )
    abertos = cursor.fetchall()

    if novo_tipo is None:
        if abertos:
            cursor.execute(
                """
                UPDATE alerta
                SET dth_resolvido = CURRENT_TIMESTAMP
                WHERE bancada_id = ?
                  AND dth_resolvido IS NULL
                  AND tipo IN (?, ?)
                """,
                (bancada_id, TIPOS_ALERTA_RISCO[0], TIPOS_ALERTA_RISCO[1]),
            )
        return

    alerta_mesmo_tipo = next((a for a in abertos if a[1] == novo_tipo), None)

    if alerta_mesmo_tipo:
        alerta_id, _, mensagem_atual = alerta_mesmo_tipo

        if mensagem_atual != nova_mensagem:
            cursor.execute(
                "UPDATE alerta SET mensagem = ? WHERE id = ?",
                (nova_mensagem, alerta_id),
            )

        for alerta_id, tipo, _ in abertos:
            if tipo != novo_tipo:
                cursor.execute(
                    "UPDATE alerta SET dth_resolvido = CURRENT_TIMESTAMP WHERE id = ?",
                    (alerta_id,),
                )
        return

    if abertos:
        cursor.execute(
            """
            UPDATE alerta
            SET dth_resolvido = CURRENT_TIMESTAMP
            WHERE bancada_id = ?
              AND dth_resolvido IS NULL
              AND tipo IN (?, ?)
            """,
            (bancada_id, TIPOS_ALERTA_RISCO[0], TIPOS_ALERTA_RISCO[1]),
        )

    cursor.execute(
        """
        INSERT INTO alerta (bancada_id, tipo, mensagem)
        VALUES (?, ?, ?)
        """,
        (bancada_id, novo_tipo, nova_mensagem),
    )


def insert_culturas():

    conn = _connect()
    cursor = conn.cursor()

    culturas = [
        ('Alface', 5.5, 6.5, 0.8, 1.2, 20.0, 24.0, 12.0, 50),
        ('Agrião', 6.0, 6.8, 1.2, 1.8, None, None, None, None),
        ('Rúcula', 5.5, 6.5, 1.2, 1.8, 15.0, 25.0, 12.0, 35),
        ('Espinafre', 5.5, 6.6, 1.2, 1.8, None, None, None, None),
        ('Couve', 6.0, 7.5, 1.2, 2.0, None, None, None, None),
        ('Acelga', 6.0, 6.5, 1.2, 1.8, None, None, None, None),
        ('Escarola', 5.5, 6.5, 1.2, 1.8, None, None, None, None),
        ('Cebolinha', 6.0, 7.0, 1.4, 1.8, None, None, None, None),
        ('Manjericão', 5.5, 6.5, 1.0, 1.6, None, None, None, None),
        ('Coentro', 6.0, 6.7, 1.2, 1.8, None, None, None, None),
        ('Hortelã', 5.5, 6.5, 1.4, 1.8, None, None, None, None),
        ('Orégano', 6.0, 7.0, 1.2, 2.0, None, None, None, None),
        ('Alecrim', 5.5, 6.0, 1.0, 1.6, None, None, None, None),
        ('Tomilho', 5.5, 6.5, 0.8, 1.5, None, None, None, None),
        ('Salvia', 5.5, 6.5, 1.0, 1.6, None, None, None, None),
        ('Cereja', 5.5, 6.5, 2.0, 3.5, None, None, None, None),
        ('Morango', 5.5, 6.2, 1.0, 1.4, None, None, None, None),
        ('Pimentão', 5.5, 6.5, 1.8, 2.5, None, None, None, None),
        ('Pepino', 5.5, 6.5, 1.7, 2.5, None, None, None, None)
    ]

    for cultura in culturas:
        cursor.execute("""
        INSERT OR IGNORE INTO cultura (nome, ph_min, ph_max, ec_min, ec_max, temp_agua_min, temp_agua_max, luminosidade_min, dias_ciclo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, cultura)
        
    conn.commit()
    conn.close()


def get_culturas():
    conn = _connect()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome, dias_ciclo FROM cultura")
    dados = cursor.fetchall()
    
    conn.commit()
    conn.close()
    return dados


def inserir_filete(bancada_id, cultura_id, data_inicio):
    conn = _connect()
    cursor = conn.cursor()
    
    # pegar ciclo da cultura
    cursor.execute("SELECT dias_ciclo FROM cultura WHERE id = ?", (cultura_id,))
    ciclo = cursor.fetchone()[0]
    
    if ciclo is None:
        ciclo = 45  # valor padrão caso não esteja definido

    data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
    colheita = data_inicio_dt + timedelta(days=ciclo)

    cursor.execute("""
        INSERT INTO filete (bancada_id, data_plantio, prevista_colheita)
        VALUES (?, ?, ?)
    """, (bancada_id, data_inicio, colheita.strftime("%Y-%m-%d")))
    
    conn.commit()
    conn.close()


def inserir_bancada(nome, cultura_id):
    conn = _connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO bancada (nome, cultura_id)
        VALUES (?, ?)
    """, (nome, cultura_id))
    
    # print("Bancada inserida, agora pegando ID...")
    cursor.execute("SELECT last_insert_rowid()")
    bancada_id = cursor.fetchone()[0]
    # print(f"ID da bancada: {bancada_id}")

    conn.commit()
    conn.close()
    return bancada_id


def get_bancadas():
    conn = _connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT b.id, b.nome, c.nome, f.data_plantio, f.prevista_colheita
        FROM bancada b
        LEFT JOIN cultura c ON b.cultura_id = c.id
        LEFT JOIN (
            SELECT f1.*
            FROM filete f1
            INNER JOIN (
                SELECT bancada_id, MAX(id) AS max_id
                FROM filete
                GROUP BY bancada_id
            ) ultimo ON ultimo.max_id = f1.id
        ) f ON f.bancada_id = b.id
        ORDER BY b.id
    """)

    dados = cursor.fetchall()
    
    conn.commit()
    conn.close()
    return dados


def get_raw_recent(bancada_id=None, horas=24):
    filtro_bancada = ""
    params = [(datetime.now() - timedelta(hours=horas)).strftime("%Y-%m-%d %H:%M:%S")]

    if bancada_id is not None:
        filtro_bancada = " AND bancada_id = ?"
        params.append(bancada_id)

    query = f"""
        SELECT *
        FROM sensor_raw
        WHERE dth_recebido >= ?{filtro_bancada}
        ORDER BY dth_recebido ASC
    """

    return _query_dataframe(query, params=params)


def get_sensor_proc_ultimo(bancada_id):
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, bancada_id, janela_horaria, ph_min, ph_max, ph_mean,
                   ec_min, ec_max, ec_mean, temperatura_ambiente_min,
                   temperatura_ambiente_max, temperatura_ambiente_mean,
                   temperatura_agua_min, temperatura_agua_max, temperatura_agua_mean,
                   luminosidade_min, luminosidade_max, luminosidade_mean,
                   vazao_min, vazao_max, vazao_mean,
                   nivel_tanque_min, nivel_tanque_max, nivel_tanque_mean,
                   umidade_min, umidade_max, umidade_mean,
                   score, n_amostras, dth_calculado
            FROM sensor_proc
            WHERE bancada_id = ?
            ORDER BY dth_calculado DESC, id DESC
            LIMIT 1
            """,
            (bancada_id,),
        )
        linha = cursor.fetchone()
        if linha is None:
            return None

        colunas = [
            "id",
            "bancada_id",
            "janela_horaria",
            "ph_min",
            "ph_max",
            "ph_mean",
            "ec_min",
            "ec_max",
            "ec_mean",
            "temperatura_ambiente_min",
            "temperatura_ambiente_max",
            "temperatura_ambiente_mean",
            "temperatura_agua_min",
            "temperatura_agua_max",
            "temperatura_agua_mean",
            "luminosidade_min",
            "luminosidade_max",
            "luminosidade_mean",
            "vazao_min",
            "vazao_max",
            "vazao_mean",
            "nivel_tanque_min",
            "nivel_tanque_max",
            "nivel_tanque_mean",
            "umidade_min",
            "umidade_max",
            "umidade_mean",
            "score",
            "n_amostras",
            "dth_calculado",
        ]
        dados = dict(zip(colunas, linha))
        dados["status"] = score_para_status(dados["score"])
        return dados
    finally:
        conn.close()


def get_alertas_ativos(bancada_id=None):
    conn = _connect()
    try:
        cursor = conn.cursor()

        filtro_bancada = ""
        params = []

        if bancada_id is not None:
            filtro_bancada = " AND a.bancada_id = ?"
            params.append(bancada_id)

        cursor.execute(
            f"""
            SELECT a.id, a.bancada_id, b.nome, a.tipo, a.mensagem, a.dth_criado
            FROM alerta a
            JOIN bancada b ON b.id = a.bancada_id
            WHERE a.dth_resolvido IS NULL{filtro_bancada}
            ORDER BY a.dth_criado DESC, a.id DESC
            """,
            params,
        )

        colunas = ["id", "bancada_id", "bancada_nome", "tipo", "mensagem", "dth_criado"]
        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    finally:
        conn.close()


def processar_sensor(bancada_id, janela_horaria="24h", horas=24):
    conn = _connect()
    try:
        cursor = conn.cursor()
        df = get_raw_recent(bancada_id=bancada_id, horas=horas)

        if df.empty:
            return None

        cultura = _valor_cultura(cursor, bancada_id)
        estatisticas = _estatisticas_dataframe(df)
        risco = calcular_risco_estatistico(estatisticas, cultura)
        n_amostras = int(df.shape[0])

        cursor.execute(
            """
            INSERT INTO sensor_proc (
                bancada_id, janela_horaria,
                ph_min, ph_max, ph_mean,
                ec_min, ec_max, ec_mean,
                temperatura_ambiente_min, temperatura_ambiente_max, temperatura_ambiente_mean,
                temperatura_agua_min, temperatura_agua_max, temperatura_agua_mean,
                luminosidade_min, luminosidade_max, luminosidade_mean,
                vazao_min, vazao_max, vazao_mean,
                nivel_tanque_min, nivel_tanque_max, nivel_tanque_mean,
                umidade_min, umidade_max, umidade_mean,
                score, n_amostras
            ) VALUES (
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?
            )
            """,
            (
                bancada_id,
                janela_horaria,
                estatisticas["ph_min"],
                estatisticas["ph_max"],
                estatisticas["ph_mean"],
                estatisticas["ec_min"],
                estatisticas["ec_max"],
                estatisticas["ec_mean"],
                estatisticas["temperatura_ambiente_min"],
                estatisticas["temperatura_ambiente_max"],
                estatisticas["temperatura_ambiente_mean"],
                estatisticas["temperatura_agua_min"],
                estatisticas["temperatura_agua_max"],
                estatisticas["temperatura_agua_mean"],
                estatisticas["luminosidade_min"],
                estatisticas["luminosidade_max"],
                estatisticas["luminosidade_mean"],
                estatisticas["vazao_min"],
                estatisticas["vazao_max"],
                estatisticas["vazao_mean"],
                estatisticas["nivel_tanque_min"],
                estatisticas["nivel_tanque_max"],
                estatisticas["nivel_tanque_mean"],
                estatisticas["umidade_min"],
                estatisticas["umidade_max"],
                estatisticas["umidade_mean"],
                risco["score"],
                n_amostras,
            ),
        )

        _sincronizar_alerta_risco(
            cursor,
            bancada_id=bancada_id,
            status=risco["status"],
            detalhes=risco.get("detalhes", {}),
            estatisticas=estatisticas,
            cultura=cultura,
        )

        conn.commit()
        return {
            "score": risco["score"],
            "status": risco["status"],
            "detalhes": risco["detalhes"],
            "n_amostras": n_amostras,
            "janela_horaria": janela_horaria,
        }
    finally:
        conn.close()


def get_proc_recent(bancada_id, horas=24):
    conn = _connect()
    dth_calculado = [(datetime.now() - timedelta(hours=horas)).strftime("%Y-%m-%d %H:%M:%S")]
    
    #print(f"Buscando leitura processada para bancada_id={bancada_id} nas últimas {horas} horas (dth_calculado >= {dth_calculado[0]})")
    
    try:
        cursor = conn.cursor()
        cursor.execute
        ("""
            SELECT score 
            FROM sensor_proc 
            WHERE bancada_id = ? 
            AND dth_calculado >= ?
        """), (bancada_id, dth_calculado[0])
        
        linha = cursor.fetchone()
        #print("Linha encontrada:", linha)
        conn.commit()
        return {
            "status" : score_para_status(linha['score']),
            "score": linha['score']
        }
    finally:
        conn.close()
