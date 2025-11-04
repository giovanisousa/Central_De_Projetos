#!/usr/bin/env python3
"""
Script de migração do banco de dados
Adiciona e popula a coluna status_id na tabela projects
"""
import os
import sys
from sqlalchemy import create_engine, text

def main():
    # Priorizar SQLALCHEMY_DATABASE_URI que tem os valores reais no Railway
    database_url = os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ Erro: Variáveis de conexão PostgreSQL não encontradas")
        print("   Esperado: SQLALCHEMY_DATABASE_URI ou DATABASE_URL")
        sys.exit(1)
    
    # Verificar se ainda tem placeholders
    if 'host:port' in database_url or '${' in database_url:
        print("❌ Erro: DATABASE_URL contém placeholders não resolvidos")
        print(f"   URL: {database_url}")
        sys.exit(1)
    
    print(f"🔗 Conectando ao banco de dados...")
    # Extrair informações seguras para mostrar
    if '@' in database_url:
        parts = database_url.split('@')
        host_db = parts[1] if len(parts) > 1 else '***'
        print(f"   Servidor: {host_db}")
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # 1. Adicionar coluna status_id
            print("\n[1/5] 📊 Adicionando coluna status_id...")
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS status_id VARCHAR;"))
            conn.commit()
            print("✅ Coluna status_id adicionada com sucesso!")
            
            # 2. Popular status_id
            print("\n[2/5] 📝 Populando status_id a partir do full_data_json...")
            result = conn.execute(text("""
                UPDATE projects 
                SET status_id = (full_data_json::json->'status'->>'id') 
                WHERE full_data_json IS NOT NULL 
                  AND (status_id IS NULL OR status_id = '');
            """))
            conn.commit()
            print(f"✅ {result.rowcount} projetos atualizados com status_id!")
            
            # 3. Popular tags
            print("\n[3/5] 🏷️  Populando tags a partir do full_data_json...")
            result = conn.execute(text("""
                UPDATE projects 
                SET tags = (full_data_json::json->'tags')::text 
                WHERE (tags IS NULL OR trim(tags) = '') 
                  AND full_data_json IS NOT NULL;
            """))
            conn.commit()
            print(f"✅ {result.rowcount} projetos atualizados com tags!")
            
            # 4. Verificar projeto específico
            print("\n[4/5] 🔍 Verificando projeto 2376502000002326783...")
            result = conn.execute(text("""
                SELECT id, status_id, status_atual, substring(tags, 1, 100) as tags 
                FROM projects 
                WHERE id = '2376502000002326783';
            """))
            row = result.fetchone()
            if row:
                print(f"   ID: {row[0]}")
                print(f"   Status ID: {row[1]}")
                print(f"   Status Atual: {row[2]}")
                print(f"   Tags: {row[3]}")
            else:
                print("   ⚠️  Projeto não encontrado")
            
            # 5. Estatísticas gerais
            print("\n[5/5] 📊 Estatísticas gerais...")
            result = conn.execute(text("""
                SELECT 
                  COUNT(*) FILTER (WHERE status_id IS NULL OR status_id = '') as sem_status_id,
                  COUNT(*) FILTER (WHERE tags IS NULL OR trim(tags) = '') as sem_tags,
                  COUNT(*) as total
                FROM projects;
            """))
            row = result.fetchone()
            print(f"   Total de projetos: {row[2]}")
            print(f"   Sem status_id: {row[0]}")
            print(f"   Sem tags: {row[1]}")
            print(f"   Com status_id: {row[2] - row[0]}")
            
            print("\n✅ ✅ ✅ Migração concluída com sucesso! ✅ ✅ ✅")
            
    except Exception as e:
        print(f"\n❌ Erro durante a migração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == '__main__':
    main()
