"""
Script para adicionar as colunas normalizadas (FASE 1) no banco SQLite local.
Executa as mesmas migrations que já existem no PostgreSQL de produção.
"""
import sqlite3
import os

DB_PATH = 'zoho_cache.db'

def migrate_database():
    """Adiciona as colunas da FASE 1 no banco local SQLite"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco de dados não encontrado: {DB_PATH}")
        print("Execute 'python app.py' primeiro para criar o banco.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Lista de colunas a adicionar (FASE 1)
    columns_to_add = [
        ('status_id', 'TEXT'),
        ('owner_zpuid', 'TEXT'),
        ('owner_name', 'TEXT'),
        ('client_name', 'TEXT'),
        ('project_name', 'TEXT'),
    ]
    
    print("🔧 Iniciando migração do banco local...")
    
    for column_name, column_type in columns_to_add:
        try:
            # Tenta adicionar a coluna
            cursor.execute(f'ALTER TABLE projects ADD COLUMN {column_name} {column_type}')
            print(f"✅ Coluna adicionada: {column_name}")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print(f"⚠️  Coluna já existe: {column_name}")
            else:
                print(f"❌ Erro ao adicionar {column_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Migração concluída!")
    print("\nAgora execute 'python app.py' para testar.")

if __name__ == '__main__':
    migrate_database()
