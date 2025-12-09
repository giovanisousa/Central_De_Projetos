#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para Popular Banco Neon - Primeira Sincronização
========================================================

Este script deve ser executado LOCALMENTE para fazer a primeira
sincronização do Zoho para o banco de dados Neon (PostgreSQL).

ANTES DE EXECUTAR:
1. Configure o arquivo .env com as variáveis:
   - DATABASE_URL (string de conexão do Neon)
   - ZOHO_CLIENT_ID
   - ZOHO_CLIENT_SECRET
   - ZOHO_REFRESH_TOKEN

2. Execute:
   python popular_banco.py

O script irá:
1. Conectar no banco Neon
2. Criar/verificar tabelas (schema)
3. Buscar todos os projetos do Zoho
4. Sincronizar fases de cada projeto
5. Pode levar 10-15 minutos para completar

IMPORTANTE: Este script usa a mesma lógica do sync_complete.py
"""

import os
import sys
from datetime import datetime

# Carregar variáveis do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Arquivo .env carregado")
except ImportError:
    print("⚠️  python-dotenv não instalado. Usando variáveis de ambiente do sistema")

# Verificar variáveis essenciais
required_vars = [
    'DATABASE_URL',
    'ZOHO_CLIENT_ID', 
    'ZOHO_CLIENT_SECRET',
    'ZOHO_REFRESH_TOKEN'
]

missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    print("\n❌ ERRO: Variáveis de ambiente faltando:")
    for var in missing_vars:
        print(f"   - {var}")
    print("\nConfigure o arquivo .env com todas as variáveis necessárias!")
    sys.exit(1)

print("\n" + "="*80)
print("  POPULANDO BANCO NEON - PRIMEIRA SINCRONIZAÇÃO")
print(f"  Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

# Verificar conexão com banco
try:
    from database import Session, Project, Fase
    print("✅ Módulo database importado")
    
    session = Session()
    projetos_antes = session.query(Project).count()
    fases_antes = session.query(Fase).count()
    session.close()
    
    print(f"📊 Estado atual do banco:")
    print(f"   - Projetos: {projetos_antes}")
    print(f"   - Fases: {fases_antes}")
    
except Exception as e:
    print(f"\n❌ ERRO ao conectar no banco: {e}")
    print("\nVerifique se DATABASE_URL está correto no .env")
    sys.exit(1)

# Importar funções de sincronização
try:
    from sync_zoho import synchronize_projects, sync_all_phases_for_existing_projects
    print("✅ Módulos de sincronização importados\n")
except Exception as e:
    print(f"\n❌ ERRO ao importar sync_zoho: {e}")
    sys.exit(1)

# ETAPA 1: Sincronizar projetos do Zoho
print("\n" + "="*80)
print("📥 ETAPA 1/2: SINCRONIZANDO PROJETOS DO ZOHO")
print("="*80)

try:
    synchronize_projects()
    print("\n✅ Projetos sincronizados com sucesso!")
except Exception as e:
    print(f"\n❌ ERRO na sincronização de projetos: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Verificar quantos projetos foram inseridos
try:
    session = Session()
    projetos_depois = session.query(Project).count()
    session.close()
    projetos_novos = projetos_depois - projetos_antes
    
    print(f"\n📊 Projetos inseridos: {projetos_novos}")
    print(f"   Total no banco: {projetos_depois}")
except Exception as e:
    print(f"⚠️  Não foi possível contar projetos: {e}")

# ETAPA 2: Sincronizar fases de todos os projetos
print("\n" + "="*80)
print("📊 ETAPA 2/2: SINCRONIZANDO FASES DE TODOS OS PROJETOS")
print("="*80)
print("⏱️  Esta etapa pode levar 10-15 minutos...")
print("⚠️  Zoho API Rate Limit: 100 req/2min - usando delay de 2s entre projetos\n")

try:
    sync_all_phases_for_existing_projects()
    print("\n✅ Fases sincronizadas com sucesso!")
except Exception as e:
    print(f"\n❌ ERRO na sincronização de fases: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Estatísticas finais
try:
    session = Session()
    projetos_final = session.query(Project).count()
    fases_final = session.query(Fase).count()
    session.close()
    
    fases_novas = fases_final - fases_antes
    media_fases = fases_final / projetos_final if projetos_final > 0 else 0
    
    print("\n" + "="*80)
    print("✅ SINCRONIZAÇÃO COMPLETA CONCLUÍDA!")
    print("="*80)
    print(f"\n📊 Estatísticas finais:")
    print(f"   - Projetos no banco: {projetos_final} (novos: {projetos_novos})")
    print(f"   - Fases no banco: {fases_final} (novas: {fases_novas})")
    print(f"   - Média de fases por projeto: {media_fases:.1f}")
    print(f"\n🎉 Banco Neon populado com sucesso!")
    print(f"⏱️  Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"\n⚠️  Erro ao gerar estatísticas finais: {e}")

print("✅ Script finalizado com sucesso!")
print("\nPróximos passos:")
print("1. Verifique os dados no banco Neon")
print("2. Faça deploy no Render")
print("3. Sincronizações futuras serão via GitHub Actions\n")
