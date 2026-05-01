# Cria estrutura do banco de dados
import os
from pathlib import Path
import sqlite3
import sys
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.crud import insert_culturas, ensure_default_admin
from others.env import get_env_mode, is_production_mode, get_db_name, is_development_mode

# Caminho do banco de dados (padronizado pelo env)
DB_PATH = ROOT_DIR / "db" / get_db_name()
print(f"Usando banco de dados em: {DB_PATH}")

def conectar_db():
    return sqlite3.connect(str(DB_PATH))

# Deleta tudo
def drop_tables():
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS sensor_raw;")
    cursor.execute("DROP TABLE IF EXISTS filete;")
    cursor.execute("DROP TABLE IF EXISTS bancada;")
    cursor.execute("DROP TABLE IF EXISTS cultura;")
    cursor.execute("DROP TABLE IF EXISTS sensor_proc;")
    cursor.execute("DROP TABLE IF EXISTS alerta;")
    cursor.execute("DROP TABLE IF EXISTS usuario;")
    
    conn.commit()
    conn.close()

# Cria todas tabelas e indexes
def create_tables():
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Tabela de bancada
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bancada (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL
    );
    """)

    # Tabela de filete
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS filete (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bancada_id INTEGER NOT NULL,
        cultura_id INTEGER NOT NULL,
        data_plantio DATE NOT NULL,
        prevista_colheita DATE NOT NULL,
        FOREIGN KEY (bancada_id) REFERENCES bancada(id),
        FOREIGN KEY (cultura_id) REFERENCES cultura(id)
    );
    """)

    # cria tabela cultura
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cultura (
        id INTEGER PRIMARY KEY,
        nome TEXT UNIQUE,
        ph_min REAL,
        ph_max REAL,
        ec_min REAL,
        ec_max REAL,
        temp_agua_min REAL,
        temp_agua_max REAL,
        luminosidade_min REAL,
        dias_ciclo INTEGER
    )
    """)

    # Tabela de senor_raw
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_raw (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bancada_id INTEGER NOT NULL,
        ph REAL,
        ec REAL,
        temperatura_ambiente REAL,
        temperatura_agua REAL,
        luminosidade REAL,
        vazao REAL,
        nivel_tanque REAL,
        umidade REAL,
        dth_recebido DATETIME DEFAULT (datetime('now', '-3 hours')),
        FOREIGN KEY (bancada_id) REFERENCES bancada(id)
    );
    """)
    
    # Cria tabela de leitura processada
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_proc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bancada_id INTEGER NOT NULL,
        janela_horaria TEXT,
        ph_min REAL,
        ph_max REAL,
        ph_mean REAL,
        ec_min REAL,
        ec_max REAL,
        ec_mean REAL,
        temperatura_ambiente_min REAL,
        temperatura_ambiente_max REAL,
        temperatura_ambiente_mean REAL,
        temperatura_agua_min REAL,
        temperatura_agua_max REAL,
        temperatura_agua_mean REAL,
        luminosidade_min REAL,
        luminosidade_max REAL,
        luminosidade_mean REAL,
        vazao_min REAL,
        vazao_max REAL,
        vazao_mean REAL,
        nivel_tanque_min REAL,
        nivel_tanque_max REAL,
        nivel_tanque_mean REAL,
        umidade_min REAL,
        umidade_max REAL,
        umidade_mean REAL,
        score REAL,
        anomalia_score REAL,
        anomalia_status TEXT,
        tendencia_score REAL,
        tendencia_status TEXT,
        consolidado_score REAL,
        consolidado_status TEXT,
        consolidado_motivo TEXT,
        n_amostras INTEGER,
        dth_calculado DATETIME DEFAULT (datetime('now', '-3 hours')),
        FOREIGN KEY (bancada_id) REFERENCES bancada(id)
    );
    """)
    
    # Cria tabela de alertas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bancada_id INTEGER NOT NULL,
        tipo TEXT,
        mensagem TEXT,
        dth_criado DATETIME DEFAULT (datetime('now', '-3 hours')),
        dth_resolvido DATETIME,
        FOREIGN KEY (bancada_id) REFERENCES bancada(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'viewer')),
        created_at DATETIME DEFAULT (datetime('now', '-3 hours'))
    );
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_bancada_tempo ON sensor_raw(bancada_id, dth_recebido);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_tempo ON sensor_raw(dth_recebido);")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_bancada_janela_tempo ON sensor_proc(bancada_id, janela_horaria, dth_calculado);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_tempo_janela ON sensor_proc(janela_horaria, dth_calculado);")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_filete_bancada ON filete(bancada_id);")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerta_bancada_criado ON alerta(bancada_id, dth_criado);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerta_bancada_aberto ON alerta(dth_criado, dth_resolvido);")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    env_mode = get_env_mode()

    if is_production_mode() and DB_PATH.exists():
        print("Modo de produção detectado. O banco de dados não será reinicializado para evitar perda de dados.")
        sys.exit(0)

    elif is_development_mode() or (is_production_mode() and not DB_PATH.exists()): 
        drop_tables()
        print("Tabelas deletadas (se existiam).")
        create_tables()
        print("Banco criado com sucesso!")
        ensure_default_admin()
        print("Usuário admin garantido!")
        insert_culturas()
        print("Culturas inseridas!")
