from datetime import datetime
import random
import time
import sys
import threading
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.crud import processar_sensor as processar_sensor_db
from ingestion.serial_reader import inserir_sensor_raw, parse_linha

INTERVALO_GERACAO_S = 0.5
INTERVALO_PROCESSAMENTO_S = 10

controle_event = threading.Event()
thread_simulacao = None
thread_processamento = None
bancadas_ativas = set()
bancadas_lock = threading.Lock()


def registrar_bancada_ativa(bancada_id):
    with bancadas_lock:
        bancadas_ativas.add(bancada_id)


def _gerar_linha_fake(bancada_id):
    return (
        f"B{bancada_id}," # bancada_id
        f"{random.uniform(5.5, 6.5)}," # pH 
        f"{random.uniform(0.5, 2.0)}," # condutividade elétrica 
        f"{random.uniform(15, 30)}," # temperatura ambiente
        f"{random.uniform(10, 30)}," # temperatura água
        f"{random.uniform(8, 16)}," # luminosidade
        f"{random.uniform(800, 1200)}," # vazão
        f"{random.uniform(20, 30)}," # nivel tanque
        f"{random.uniform(50, 70)}" # umidade
    )


def _loop_simulacao():
    while not controle_event.is_set():
        for bancada_id in range(1, 3):
            if controle_event.is_set():
                break

            linha_fake = _gerar_linha_fake(bancada_id)

            try:
                dados = parse_linha(linha_fake)

                if dados:
                    inserir_sensor_raw(*dados)
                    registrar_bancada_ativa(dados[0])
                    print(f"{datetime.now()}: Leitura fake inserida para bancada {dados[0]}")
            except Exception as e:
                print("Erro ao processar linha fake:", e)

        controle_event.wait(INTERVALO_GERACAO_S)


def _loop_processamento():
    while not controle_event.is_set():
        if controle_event.wait(INTERVALO_PROCESSAMENTO_S):
            break

        with bancadas_lock:
            bancadas_para_processar = list(bancadas_ativas)

        for bancada_id in bancadas_para_processar:
            try:
                processar_sensor_db(
                    bancada_id,
                    janela_horaria="10s",
                    horas=INTERVALO_PROCESSAMENTO_S / 3600,
                )
                print(f"Processamento fake concluído para bancada {bancada_id}")
            except Exception as e:
                print(f"Erro ao processar bancada {bancada_id}: {e}")


def simular_dados():
    global thread_simulacao, thread_processamento

    if thread_simulacao and thread_simulacao.is_alive():
        return

    controle_event.clear()

    thread_simulacao = threading.Thread(target=_loop_simulacao, daemon=True)
    thread_processamento = threading.Thread(target=_loop_processamento, daemon=True)

    thread_simulacao.start()
    thread_processamento.start()


def parar_simulacao():
    controle_event.set()