import sys
from pathlib import Path
import os
import time
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

"""
Liberar acesso de admin
Cadastra bancadas e filetes automaticamente
Gerar banco a parte para não impactar o banco real
Ligar o simulador
Para o simulador após um tempo
"""

from db.crud import inserir_bancada, inserir_filete, ensure_default_admin, insert_culturas
from db.init_db import drop_tables, create_tables
from simulator.simulator_port import simular_dados, parar_simulacao
from others.env import is_development_mode
    
if __name__ == "__main__":
    print("Iniciando teste...")
    
    if is_development_mode():
        drop_tables()
        create_tables()
        ensure_default_admin()
        insert_culturas()
        
        print("Banco de dados criado e configurado com sucesso!")
        print("Usuário admin já está disponível (admin/admin123)")
        
        # Criar bancadas
        bancada_id1 = inserir_bancada("Bancada 1")
        bancada_id2 = inserir_bancada("Bancada 2")
        
        print(f"✓ Bancada 1 criada (ID: {bancada_id1})")
        print(f"✓ Bancada 2 criada (ID: {bancada_id2})")
        
        # Criar filetes
        inserir_filete(bancada_id1, 1, "2024-01-01")
        inserir_filete(bancada_id1, 1, "2024-01-15")
        inserir_filete(bancada_id2, 3, "2024-01-10")
        inserir_filete(bancada_id2, 3, "2024-01-20")
        
        print("✓ Filetes de teste criados com sucesso!")
        
        simular_dados()
        print("\n🚀 Simulação de dados iniciada!")
        print("   Deixe rodando por um tempo para gerar dados no banco (90 segundos)...")
        print("   Você pode acessar o Streamlit em outra aba do navegador.")
        time.sleep(90)  # Deixar o simulador rodando por um tempo para gerar dados
        parar_simulacao()
        print("\n✓ Simulação de dados parada. Teste concluído!")
        
    else:
        print("Simulação de dados está desativada em modo de produção. Para testar a simulação, altere o modo para DEVELOPMENT no arquivo .env.")
        
    sys.exit(0)