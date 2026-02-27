#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Sincronização COMPLETA no Banco LOCAL (SQLite)
=========================================================

Este script:
1. Usa banco SQLite LOCAL (zoho_cache.db) - SEM problemas de timeout
2. Sincroniza TODOS os 112 projetos do Zoho
3. Sincroniza fases, listas e tarefas
4. Depois você sobe o backup para o Neon

VANTAGENS:
- Sem timeout SSL do Neon
- Muito mais rápido
- Pode interromper e retomar
- Sem limite de tempo de operação
"""

import os
import sys
from dotenv import load_dotenv

# Força uso do banco LOCAL (SQLite)
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zoho_cache.db'

load_dotenv()

print("\n" + "="*80)
print("  SINCRONIZAÇÃO COMPLETA - Banco LOCAL (SQLite)")
print("="*80 + "\n")

print("✓ Usando banco LOCAL: zoho_cache.db")
print("✓ Sem timeout de conexão")
print("✓ Sincronização rápida e confiável\n")

from database import Session, Project, Fase, engine
from sync_zoho import synchronize_projects

# Verificar estado inicial
print("[1/4] Verificando estado inicial do banco local...")
session = Session()
try:
    total_projetos_inicial = session.query(Project).count()
    total_fases_inicial = session.query(Fase).count()
    print(f"  - Projetos atuais: {total_projetos_inicial}")
    print(f"  - Fases atuais: {total_fases_inicial}")
finally:
    session.close()

# Limpar banco se necessário
if total_projetos_inicial > 0:
    print("\n[AVISO] O banco local já tem dados.")
    resposta = input("Deseja limpar e sincronizar do zero? (s/n): ").strip().lower()
    
    if resposta == 's':
        print("\n[2/4] Limpando banco local...")
        from database import Fase, ListaDeTarefas, Tarefa
        
        session = Session()
        try:
            session.query(Tarefa).delete()
            session.query(ListaDeTarefas).delete()
            session.query(Fase).delete()
            session.query(Project).delete()
            session.commit()
            print("  ✓ Banco limpo!")
        except Exception as e:
            session.rollback()
            print(f"  ✗ ERRO ao limpar: {e}")
            sys.exit(1)
        finally:
            session.close()
    else:
        print("\n[2/4] Mantendo dados existentes. Sincronização incremental...")
else:
    print("\n[2/4] Banco local vazio. Iniciando sincronização completa...")

# SINCRONIZAR PROJETOS
print("\n[3/4] Sincronizando PROJETOS do Zoho...")
print("Esta etapa busca todos os 112 projetos esperados.\n")

try:
    synchronize_projects()
    print("\n✓ Projetos sincronizados com sucesso!")
except KeyboardInterrupt:
    print("\n[AVISO] Sincronização interrompida.")
    print("Execute este script novamente para continuar.\n")
    sys.exit(0)
except Exception as e:
    print(f"\n✗ ERRO na sincronização: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Verificar resultado
print("\n[4/4] Verificando resultado...")
session = Session()
try:
    total_projetos_final = session.query(Project).count()
    total_fases_final = session.query(Fase).count()
finally:
    session.close()

print("\n" + "="*80)
print("  RESULTADO DA SINCRONIZAÇÃO LOCAL")
print("="*80 + "\n")

print(f"📊 Projetos sincronizados: {total_projetos_final}")
print(f"📊 Fases sincronizadas: {total_fases_final}")

if total_projetos_final < 100:
    print(f"\n⚠️  ATENÇÃO: Esperava-se ~112 projetos, mas foram sincronizados apenas {total_projetos_final}!")
    print("Você pode executar este script novamente para buscar mais projetos.\n")
else:
    print(f"\n✅ SUCESSO! {total_projetos_final} projetos sincronizados localmente.")
    print("\n" + "="*80)
    print("  PRÓXIMO PASSO: Fazer Backup para o Neon")
    print("="*80 + "\n")
    print("Execute o script de backup:")
    print("  python backup_sqlite_to_neon.py\n")

print("Arquivo do banco local: zoho_cache.db")
print("Tamanho: ", end="")
try:
    import os
    size_mb = os.path.getsize('zoho_cache.db') / (1024 * 1024)
    print(f"{size_mb:.2f} MB")
except:
    print("(não disponível)")

print("\n" + "="*80 + "\n")
