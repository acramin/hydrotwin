import serial
import sqlite3
from datetime import datetime
import time
import threading

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.crud import processar_sensor as processar_sensor_db

PORTA = '/dev/ttyUSB0'  # pode mudar depois para a porta certa do arduino
BAUD_RATE = 9600
INTERVALO_PROCESSAMENTO_S = 10

bancadas_ativas = set()
bancadas_lock = threading.Lock()
stop_event = threading.Event()

def conectar_db():
    return sqlite3.connect("db\\hydroponic.db")

def inserir_sensor_raw(bancada_id, ph, ec, temperatura_ambiente, temperatura_agua, luminosidade, vazao, nivel_tanque, umidade, dth_recebido):
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sensor_raw (bancada_id, ph, ec, temperatura_ambiente, temperatura_agua, luminosidade, vazao, nivel_tanque, umidade, dth_recebido)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (bancada_id, ph, ec, temperatura_ambiente, temperatura_agua, luminosidade, vazao, nivel_tanque, umidade, dth_recebido))

    #print("Dados inseridos no banco:", bancada_id, ph, ec, temperatura_ambiente, temperatura_agua, luminosidade, vazao, nivel_tanque, umidade, dth_recebido)
    error = cursor.execute("SELECT changes()").fetchone()[0]
    if error == 0:
        print("Erro ao inserir dados no banco!")
    else:
        print("Dados inseridos com sucesso!")

    conn.commit()
    conn.close()


def registrar_bancada_ativa(bancada_id):
    with bancadas_lock:
        bancadas_ativas.add(bancada_id)


def loop_processamento_periodico():
    while not stop_event.is_set():
        time.sleep(INTERVALO_PROCESSAMENTO_S)

        with bancadas_lock:
            bancadas_para_processar = list(bancadas_ativas)

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

        return bancada_id, ph, ec, temperatura_ambiente, temperatura_agua, luminosidade, vazao, nivel_tanque, umidade, dth_recebido

    except:
        return None

def main():
    print("Conectando na serial...")
    ser = serial.Serial(PORTA, BAUD_RATE)

    thread_processamento = threading.Thread(
        target=loop_processamento_periodico,
        daemon=True,
    )
    thread_processamento.start()
    print(f"Processamento periodico iniciado (a cada {INTERVALO_PROCESSAMENTO_S}s)")

    try:
        while True:
            try:
                linha = ser.readline().decode('utf-8')
                print("Recebido:", linha.strip())

                dados = parse_linha(linha)

                if dados:
                    inserir_sensor_raw(*dados)
                    registrar_bancada_ativa(dados[0])
                    print("Salvo no banco!")
                else:
                    print("Erro ao parsear")

            except Exception as e:
                print("Erro:", e)
    finally:
        stop_event.set()
        ser.close()

if __name__ == "__main__":
    main()