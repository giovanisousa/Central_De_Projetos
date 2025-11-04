#!/usr/bin/env python3
"""
Script de sincronização local - usa conexão externa do Railway
"""
import os
import sys

# Forçar uso da URL externa do Railway (acessível de fora)
# IMPORTANTE: Você precisa pegar a URL externa do PostgreSQL no Railway Dashboard
# Vá em: PostgreSQL -> Connect -> External Connection URL

# Exemplo de formato:
# postgresql://postgres:senha@containers-us-west-xxx.railway.app:7777/railway

EXTERNAL_DATABASE_URL = input("Cole a URL EXTERNA do PostgreSQL do Railway Dashboard:\n> ").strip()

if not EXTERNAL_DATABASE_URL or 'railway.internal' in EXTERNAL_DATABASE_URL:
    print("\n❌ ERRO: Use a URL EXTERNA (External Connection), não a interna!")
    print("   A URL deve conter 'containers-us-west' ou 'railway.app', NÃO 'railway.internal'")
    print("\n📍 Onde encontrar:")
    print("   1. Acesse Railway Dashboard -> PostgreSQL")
    print("   2. Vá na aba 'Connect'")
    print("   3. Copie a 'External Connection URL' (não a interna!)")
    sys.exit(1)

# Sobrescrever a variável de ambiente
os.environ['SQLALCHEMY_DATABASE_URI'] = EXTERNAL_DATABASE_URL
os.environ['DATABASE_URL'] = EXTERNAL_DATABASE_URL

print(f"\n🔗 Usando conexão externa do Railway")
print(f"   Host: {EXTERNAL_DATABASE_URL.split('@')[1].split(':')[0] if '@' in EXTERNAL_DATABASE_URL else '???'}\n")

# Agora importa o sync_zoho que vai usar a conexão correta
try:
    print("📦 Importando módulos...")
    from sync_zoho import synchronize_projects
    
    print("\n🚀 Iniciando sincronização completa de projetos...\n")
    print("   Isso vai buscar TODOS os projetos do Zoho e atualizar o banco")
    print("   Incluindo atualização de status_id e tags\n")
    
    synchronize_projects()
    
    print("\n✅ ✅ ✅ Sincronização concluída com sucesso! ✅ ✅ ✅")
    print("\n📊 Agora execute no DBeaver para validar:")
    print("   SELECT id, status_id, status_atual FROM projects WHERE id = '2376502000002326783';")
    
except Exception as e:
    print(f"\n❌ Erro durante sincronização: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
