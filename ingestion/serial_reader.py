import serial
import sqlite3
from datetime import datetime

import sys
from pathlib import Path

# ROOT_DIR = Path(__file__).resolve().parents[1]
# if str(ROOT_DIR) not in sys.path:
#     sys.path.insert(0, str(ROOT_DIR))

# from db.crud import processar_sensor

PORTA = '/dev/ttyUSB0'  # pode mudar depois para a porta certa do arduino
BAUD_RATE = 9600

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

    # # Mantem score/status e alertas sempre atualizados apos nova leitura bruta.
    # processar_sensor(bancada_id, janela_horaria="1min", horas=1/60)


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

    while True:
        try:
            linha = ser.readline().decode('utf-8')
            print("Recebido:", linha.strip())

            dados = parse_linha(linha)

            if dados:
                inserir_sensor_raw(*dados)
                print("Salvo no banco!")
            else:
                print("Erro ao parsear")

        except Exception as e:
            print("Erro:", e)

if __name__ == "__main__":
    main()