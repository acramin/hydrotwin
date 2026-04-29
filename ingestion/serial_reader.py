import serial
import sqlite3
from datetime import datetime
import time
import threading
from queue import Queue

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.crud import processar_sensor as processar_sensor_db

# ================= CONFIG =================
PORTA = 'COM9'
BAUD_RATE = 9600
INTERVALO_PROCESSAMENTO_S = 10

# ================= ESTADO GLOBAL =================
fila_dados = Queue(maxsize=1000)

bancadas_ativas = set()
bancadas_lock = threading.Lock()

stop_event = threading.Event()

# ================= DB =================
def conectar_db():
    return sqlite3.connect("db\\hydroponic.db", check_same_thread=False)

def db_writer():
    conn = conectar_db()
    cursor = conn.cursor()

    print("DB Writer iniciado")

    while not stop_event.is_set():
        try:
            dados = fila_dados.get(timeout=1)

            cursor.execute("""
                INSERT INTO sensor_raw 
                (bancada_id, ph, ec, temperatura_ambiente, temperatura_agua, luminosidade, vazao, nivel_tanque, umidade, dth_recebido)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, dados)

            conn.commit()

            bancada_id = dados[0]
            with bancadas_lock:
                bancadas_ativas.add(bancada_id)

            print("Salvo no banco:", dados)

        except Exception as e:
            # Timeout da fila ou erro de banco
            continue

    conn.close()
    print("DB Writer encerrado")

# ================= PROCESSAMENTO =================
def loop_processamento_periodico():
    while not stop_event.is_set():
        time.sleep(INTERVALO_PROCESSAMENTO_S)

        with bancadas_lock:
            bancadas_para_processar = list(bancadas_ativas)

        if not bancadas_para_processar:
            print("Sem dados novos, pulando processamento")
            time.sleep(1)
            continue

        for bancada_id in bancadas_para_processar:
            try:
                processar_sensor_db(
                    bancada_id,
                    janela_horaria="10s",
                    horas=10 / 3600,
                )
                print(f"Processamento concluído para bancada {bancada_id}")
            except Exception as e:
                print(f"Erro ao processar bancada {bancada_id}: {e}")

        with bancadas_lock:
            bancadas_ativas.clear()

# ================= PARSER =================
def parse_linha(linha):
    try:
        partes = linha.strip().split(",")

        bancada_str = partes[0]  # B1
        ph = float(partes[1])
        ec = float(partes[2])
        temperatura_ambiente = float(partes[3])
        temperatura_agua = float(partes[4])
        luminosidade = float(partes[5])
        vazao = float(partes[6])
        nivel_tanque = float(partes[7])
        umidade = float(partes[8])

        dth_recebido = datetime.now()
        bancada_id = int(bancada_str.replace("B", ""))

        return (
            bancada_id, ph, ec,
            temperatura_ambiente, temperatura_agua,
            luminosidade, vazao,
            nivel_tanque, umidade,
            dth_recebido
        )

    except:
        return None

# ================= SERIAL READER =================
def serial_reader():
    print("Conectando na serial...")
    ser = serial.Serial(PORTA, BAUD_RATE)

    print("Serial Reader iniciado")

    while not stop_event.is_set():
        try:
            linha = ser.readline().decode('utf-8')
            print("Recebido:", linha.strip())
            
            if not linha.startswith("B") or linha.count(",") < 8:
                print("Ignorado (formato inválido/dados incompletos)")
                continue

            dados = parse_linha(linha)

            if dados:
                try:
                    fila_dados.put(dados, timeout=1)
                except:
                    print("Fila cheia! Perdendo dado!")

            else:
                print("Erro ao parsear")

        except Exception as e:
            print("Erro na serial:", e)

    ser.close()
    print("Serial Reader encerrado")

# ================= MAIN =================
def main():
    threads = []

    t_serial = threading.Thread(target=serial_reader, daemon=True)
    t_db = threading.Thread(target=db_writer, daemon=True)
    t_proc = threading.Thread(target=loop_processamento_periodico, daemon=True)

    threads.extend([t_serial, t_db, t_proc])

    for t in threads:
        t.start()

    print("Sistema iniciado")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando sistema...")
        stop_event.set()

        for t in threads:
            t.join(timeout=2)

if __name__ == "__main__":
    main()