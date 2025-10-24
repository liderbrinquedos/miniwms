import sqlite3
import os
import csv
from datetime import datetime

def init_database():
    db_path = os.getenv('DATABASE_URL', 'sqlite:///warehouse.db').replace('sqlite:///', '')
    
    # Se o caminho for apenas um nome de arquivo, coloque no diretório data
    if '/' not in db_path or db_path.startswith('warehouse.db'):
        db_path = 'data/warehouse.db'
    
    # Garantir que o diretório existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabela de produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ref TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de localizações (estrutura atualizada)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cod TEXT UNIQUE NOT NULL,
            local TEXT NOT NULL,
            armazem TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de estoque
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            UNIQUE(location_id, product_id)
        )
    ''')
    
    # Tabela de movimentações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            type TEXT NOT NULL, -- 'entry' or 'exit'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Importar dados dos arquivos CSV
    import_from_csv(cursor)
    
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso!")

def import_from_csv(cursor):
    base_path = 'data/import'
    
    # Importar produtos
    products_csv = os.path.join(base_path, 'products.csv')
    if os.path.exists(products_csv):
        print("Importando produtos do CSV...")
        with open(products_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cursor.execute(
                    'INSERT OR IGNORE INTO products (ref, name) VALUES (?, ?)',
                    (row['ref'], row['name'])
                )
        print(f"Produtos importados de {products_csv}")
    else:
        print(f"Arquivo {products_csv} não encontrado, usando dados padrão")
        insert_default_products(cursor)
    
    # Importar localizações (formato atualizado)
    locations_csv = os.path.join(base_path, 'locations.csv')
    if os.path.exists(locations_csv):
        print("Importando localizações do CSV...")
        with open(locations_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cursor.execute(
                    'INSERT OR IGNORE INTO locations (cod, local, armazem) VALUES (?, ?, ?)',
                    (row['COD'], row['LOCAL'], row.get('ARMAZEM', 'LOG'))
                )
        print(f"Localizações importadas de {locations_csv}")
    else:
        print(f"Arquivo {locations_csv} não encontrado, usando dados padrão")
        insert_default_locations(cursor)

def insert_default_products(cursor):
    """Inserir produtos padrão se CSV não existir"""
    products = [
        ('P1001', 'CAR BOLA'),
        ('P1002', 'CAR CHORRO'),
        ('P1003', 'CAR TUCHO'),
        ('P1004', 'CAR MARGO'),
        ('P1005', 'CAR SETE'),
        ('P1006', 'CAR JOGO')
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO products (ref, name) VALUES (?, ?)',
        products
    )

def insert_default_locations(cursor):
    """Inserir localizações padrão se CSV não existir"""
    locations = [
        ('10000', 'A001C', 'LOG'),
        ('10001', 'A001D', 'LOG'),
        ('10002', 'A002C', 'LOG'),
        ('10003', 'A002D', 'LOG'),
        ('10004', 'A003C', 'LOG'),
        ('10005', 'A003D', 'LOG'),
        ('10006', 'A004A', 'LOG'),
        ('10007', 'A004B', 'LOG'),
        ('10008', 'A004C', 'LOG'),
        ('10009', 'A004D', 'LOG'),
        ('10010', 'B001A', 'LOG'),
        ('10011', 'B001B', 'LOG')
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO locations (cod, local, armazem) VALUES (?, ?, ?)',
        locations
    )

if __name__ == '__main__':
    init_database()