import random
import time

from serial_reader import inserir_sensor_raw, parse_linha

while True:
    linha_fake = f"B{random.randint(1, 2)},{random.uniform(5.5,6.5)},{random.uniform(15,30)},{random.uniform(18,26)},{random.uniform(24,28)},{random.uniform(800,1200)},{random.uniform(0.5,1.5)},{random.uniform(40,60)},{random.uniform(50,70)}"
    print("Fake:", linha_fake)

    dados = parse_linha(linha_fake)

    if dados:
        inserir_sensor_raw(*dados)

    time.sleep(2)