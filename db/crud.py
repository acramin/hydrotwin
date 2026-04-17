from datetime import datetime, timedelta
import sqlite3

def insert_culturas():

    conn = sqlite3.connect("db\\hydroponic.db")
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
    conn = sqlite3.connect("db\\hydroponic.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome, dias_ciclo FROM cultura")
    dados = cursor.fetchall()
    
    conn.commit()
    conn.close()
    return dados

def inserir_filete(bancada_id, cultura_id, data_inicio):
    conn = sqlite3.connect("db\\hydroponic.db")
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
    conn = sqlite3.connect("db\\hydroponic.db")
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
    conn = sqlite3.connect("db\\hydroponic.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT b.id, b.nome, c.nome, f.data_plantio, f.prevista_colheita
        FROM filete f
        JOIN bancada b ON f.bancada_id = b.id
        JOIN cultura c ON b.cultura_id = c.id
    """)

    dados = cursor.fetchall()
    
    conn.commit()
    conn.close()
    return dados

# def insert_sensor_processado(bancada_id, dth_recebido, ph, ec, temp_agua, luminosidade):
#     conn = sqlite3.connect("db\\hydroponic.db")
#     cursor = conn.cursor()
    
#     cursor.execute("""
#         INSERT INTO sensor_processado (bancada_id, dth_recebido, ph, ec, temp_agua, luminosidade)
#         VALUES (?, ?, ?, ?, ?, ?)
#     """, (bancada_id, dth_recebido, ph, ec, temp_agua, luminosidade))
    
#     conn.commit()
#     conn.close()