import random
import time
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ingestion.serial_reader import inserir_sensor_raw, parse_linha

while True:
    
    for b in range(1, 3):
    
        linha_fake = f"B{b},{random.uniform(5.5,6.5)},{random.uniform(0.5,1.5)},{random.uniform(15,30)},{random.uniform(18,26)},{random.uniform(24,28)},{random.uniform(800,1200)},{random.uniform(40,60)},{random.uniform(50,70)}"
        #print("Fake:", linha_fake)

        try:
            dados = parse_linha(linha_fake)

            if dados:
                inserir_sensor_raw(*dados)

        except Exception as e:
            print("Erro ao processar linha fake:", e)

    time.sleep(5)