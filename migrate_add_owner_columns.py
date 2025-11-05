"""
Migration: Adicionar colunas normalizadas para owner, client e project name
Fase 1 da remoção gradual de full_data_json
Data: 2025-11-05
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_add_owner_columns():
    """
    Adiciona colunas normalizadas:
    - owner_zpuid: ID do dono (GP) do projeto
    - owner_name: Nome do dono (GP)
    - client_name: Nome do cliente
    - project_name: Nome do projeto
    """
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL não configurada no .env")
    
    # Ajustar URL se necessário (Railway usa postgres://, SQLAlchemy precisa postgresql://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    engine = create_engine(database_url)
    
    print("\n" + "="*70)
    print("🔧 MIGRATION: Adicionar Colunas Normalizadas de Owner/Client/Project")
    print("="*70)
    
    with engine.connect() as conn:
        try:
            # [1/5] Adicionar coluna owner_zpuid
            print("\n[1/5] 📝 Adicionando coluna owner_zpuid...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS owner_zpuid VARCHAR(50);
            """))
            conn.commit()
            print("✅ Coluna owner_zpuid adicionada")
            
            # [2/5] Adicionar coluna owner_name
            print("\n[2/5] 📝 Adicionando coluna owner_name...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS owner_name VARCHAR(255);
            """))
            conn.commit()
            print("✅ Coluna owner_name adicionada")
            
            # [3/5] Adicionar coluna client_name
            print("\n[3/5] 📝 Adicionando coluna client_name...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS client_name VARCHAR(255);
            """))
            conn.commit()
            print("✅ Coluna client_name adicionada")
            
            # [4/5] Adicionar coluna project_name
            print("\n[4/5] 📝 Adicionando coluna project_name...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS project_name VARCHAR(500);
            """))
            conn.commit()
            print("✅ Coluna project_name adicionada")
            
            # [5/5] Popular colunas a partir do full_data_json
            print("\n[5/5] 📊 Populando colunas a partir do full_data_json...")
            result = conn.execute(text("""
                UPDATE projects 
                SET 
                    owner_zpuid = (full_data_json::json->'owner'->>'zpuid'),
                    owner_name = (full_data_json::json->'owner'->>'name'),
                    client_name = COALESCE(
                        (full_data_json::json->'client_company'->>'name'),
                        (full_data_json::json->'client'->>'name'),
                        (full_data_json::json->>'client_name')
                    ),
                    project_name = (full_data_json::json->>'name')
                WHERE full_data_json IS NOT NULL 
                  AND owner_zpuid IS NULL;
            """))
            conn.commit()
            affected_rows = result.rowcount
            print(f"✅ {affected_rows} projetos atualizados")
            
            # [6/6] Criar índice em owner_zpuid para performance
            print("\n[6/6] 🚀 Criando índice em owner_zpuid...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_projects_owner_zpuid 
                ON projects(owner_zpuid);
            """))
            conn.commit()
            print("✅ Índice criado")
            
            # Verificação
            print("\n" + "="*70)
            print("📊 VERIFICAÇÃO")
            print("="*70)
            
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(owner_zpuid) as com_owner_zpuid,
                    COUNT(owner_name) as com_owner_name,
                    COUNT(client_name) as com_client_name,
                    COUNT(project_name) as com_project_name
                FROM projects;
            """))
            stats = result.fetchone()
            
            print(f"\nTotal de projetos: {stats[0]}")
            print(f"  - Com owner_zpuid: {stats[1]} ({stats[1]*100//stats[0] if stats[0] > 0 else 0}%)")
            print(f"  - Com owner_name: {stats[2]} ({stats[2]*100//stats[0] if stats[0] > 0 else 0}%)")
            print(f"  - Com client_name: {stats[3]} ({stats[3]*100//stats[0] if stats[0] > 0 else 0}%)")
            print(f"  - Com project_name: {stats[4]} ({stats[4]*100//stats[0] if stats[0] > 0 else 0}%)")
            
            print("\n" + "="*70)
            print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
            print("="*70)
            print("\n💡 Próximos passos:")
            print("  1. Atualizar database.py para incluir as novas colunas no modelo")
            print("  2. Atualizar upsert_project() para popular as colunas")
            print("  3. Substituir filtro GP em routes/api.py por owner_zpuid")
            print("\n")
            
        except Exception as e:
            conn.rollback()
            print(f"\n❌ ERRO durante migration: {e}")
            raise

if __name__ == '__main__':
    migrate_add_owner_columns()
