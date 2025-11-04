#!/usr/bin/env python3
"""
Script para sincronização completa de todos os projetos do Zoho
Atualiza status_id, tags e full_data_json no banco de dados
"""
import os
import sys

# Usar conexão externa do Railway
EXTERNAL_DATABASE_URL = input("Cole a URL EXTERNA do PostgreSQL:\n> ").strip()
os.environ['SQLALCHEMY_DATABASE_URI'] = EXTERNAL_DATABASE_URL
os.environ['DATABASE_URL'] = EXTERNAL_DATABASE_URL

print("\n🚀 Iniciando sincronização completa de projetos...\n")

try:
    from sync_zoho import synchronize_projects
    
    print("📡 Sincronizando TODOS os projetos do Zoho...")
    print("   Isso vai atualizar:")
    print("   - status_id (nova coluna)")
    print("   - tags (formato JSON correto)")
    print("   - full_data_json (dados atualizados)")
    print("   - Todos os outros campos\n")
    
    synchronize_projects()
    
    print("\n✅ ✅ ✅ Sincronização concluída! ✅ ✅ ✅")
    print("\n📊 Próximos passos:")
    print("   1. Teste o Kanban na aplicação")
    print("   2. Verifique se o projeto 2376502000002326783 aparece em 'Em Operação Assistida'")
    print("   3. Valide que outros projetos também estão nas colunas corretas")
    
except Exception as e:
    print(f"\n❌ Erro durante sincronização: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
