import serial
from datetime import datetime
import random
import time
import threading

PORTA = 'COM10'
BAUD_RATE = 9600
INTERVALO_GERACAO_S = 0.5

controle_event = threading.Event()
thread_simulacao = None

# estado físico das bancadas
estado_bancadas = {}
estado_lock = threading.Lock()


def _inicializar_estado(bancada_id):
    return {
        "ph": random.uniform(5.8, 6.2),
        "ec": random.uniform(1.0, 1.5),
        "temp_ar": random.uniform(20, 26),
        "temp_agua": random.uniform(18, 24),
        "luz": random.uniform(10, 14),   # ajustado (antes tava 10–14)
        "vazao": random.uniform(900, 1100),
        "nivel": random.uniform(24, 28),
        "umidade": random.uniform(55, 65),
        "bomba_ligada": True
    }


def _atualizar_estado(estado):
    def drift(valor, variacao, minimo, maximo):
        valor += random.uniform(-variacao, variacao)
        return max(min(valor, maximo), minimo)

    estado["ph"] = drift(estado["ph"], 0.02, 5.5, 6.5)
    estado["ec"] = drift(estado["ec"], 0.05, 0.5, 2.5)
    estado["temp_ar"] = drift(estado["temp_ar"], 0.2, 15, 30)

    estado["temp_agua"] += (estado["temp_ar"] - estado["temp_agua"]) * 0.05

    estado["luz"] = drift(estado["luz"], 0.5, 8, 16)
    estado["umidade"] = drift(estado["umidade"], 0.5, 40, 90)

    # falha ocasional da bomba
    if random.random() < 0.001:
        estado["bomba_ligada"] = not estado["bomba_ligada"]

    if estado["bomba_ligada"]:
        estado["vazao"] = drift(estado["vazao"], 50, 800, 1200)
        estado["nivel"] = drift(estado["nivel"], 0.1, 20, 30)
    else:
        estado["vazao"] = 0
        estado["nivel"] -= random.uniform(0.05, 0.2)

    return estado


def _gerar_linha_serial(bancada_id):
    with estado_lock:
        if bancada_id not in estado_bancadas:
            estado_bancadas[bancada_id] = _inicializar_estado(bancada_id)

        estado = _atualizar_estado(estado_bancadas[bancada_id])

    # FORMATO EXATO do seu serial_reader + \n obrigatório
    return (
        f"B{bancada_id},"
        f"{estado['ph']:.2f},"
        f"{estado['ec']:.2f},"
        f"{estado['temp_ar']:.2f},"
        f"{estado['temp_agua']:.2f},"
        f"{estado['luz']:.2f},"
        f"{estado['vazao']:.2f},"
        f"{estado['nivel']:.2f},"
        f"{estado['umidade']:.2f}\n"
    )


def _loop_simulacao():
    print(f"Simulador conectando na {PORTA}...")

    ser = serial.Serial(PORTA, BAUD_RATE)

    try:
        while not controle_event.is_set():
            for bancada_id in range(1, 3):
                if controle_event.is_set():
                    break

                linha = _gerar_linha_serial(bancada_id)

                try:
                    ser.write(linha.encode('utf-8'))
                    print(f"{datetime.now()} | Enviado: {linha.strip()}")
                except Exception as e:
                    print("Erro ao escrever na serial:", e)

            controle_event.wait(INTERVALO_GERACAO_S)

    finally:
        ser.close()
        print("Simulador encerrado")


def simular_dados():
    global thread_simulacao

    if thread_simulacao and thread_simulacao.is_alive():
        return

    controle_event.clear()

    thread_simulacao = threading.Thread(
        target=_loop_simulacao,
        daemon=True
    )
    thread_simulacao.start()


def parar_simulacao():
    controle_event.set()


if __name__ == "__main__":
    simular_dados()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        parar_simulacao()