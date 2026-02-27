#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script COMPLETO de sincronização resiliente - Primeira vez
===========================================================

Este script sincroniza TUDO do Zoho para o banco Neon:
1. PROJETOS (com fila resiliente)
2. FASES de cada projeto
3. LISTAS de tarefas
4. TAREFAS

Com sistema de fila para retomar em caso de falha.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*80)
print("  SINCRONIZACAO COMPLETA RESILIENTE - Primeira Vez")
print("  Zoho → Neon PostgreSQL")
print("="*80 + "\n")

# Verificar variáveis obrigatórias
required_vars = ['SQLALCHEMY_DATABASE_URI', 'ZOHO_CLIENT_ID', 'ZOHO_CLIENT_SECRET', 'ZOHO_REFRESH_TOKEN']
missing = [v for v in required_vars if not os.environ.get(v)]
if missing:
    print(f"[ERRO] Variaveis faltando: {', '.join(missing)}")
    print("Configure o arquivo .env antes de continuar!\n")
    exit(1)

print("[OK] Variaveis de ambiente configuradas")
print(f"[INFO] Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Importar funções
from sync_zoho import synchronize_projects
from database import Session, Project, Fase

# ETAPA 1: Sincronizar projetos do Zoho
print("\n" + "="*80)
print("[ETAPA 1/2] SINCRONIZANDO PROJETOS DO ZOHO")
print("="*80)
print("Esta etapa busca projetos da API do Zoho e salva no banco Neon.")
print("Pode levar ~5-10 minutos dependendo da quantidade de projetos.\n")

try:
    synchronize_projects()
    print("\n[OK] Projetos sincronizados!")
except KeyboardInterrupt:
    print("\n[AVISO] Sincronizacao de projetos interrompida pelo usuario")
    print("Execute este script novamente para continuar.\n")
    exit(0)
except Exception as e:
    print(f"\n[ERRO] Falha na sincronizacao de projetos: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Verificar projetos inseridos
session = Session()
try:
    total_projetos = session.query(Project).count()
    total_fases = session.query(Fase).count()
finally:
    try:
        session.close()
    except:
        pass

print(f"\n[STATUS ATUAL]")
print(f"  - Projetos no banco: {total_projetos}")
print(f"  - Fases no banco: {total_fases}")

if total_projetos == 0:
    print("\n[AVISO] Nenhum projeto foi sincronizado!")
    print("Verifique os filtros (proprietarios, status) e tente novamente.\n")
    exit(0)

# ETAPA 2: Sincronizar fases, listas e tarefas
print("\n" + "="*80)
print("[ETAPA 2/2] SINCRONIZANDO FASES, LISTAS E TAREFAS")
print("="*80)
print(f"Esta etapa processa {total_projetos} projetos.")
print("Pode levar ~20-30 minutos. Sistema resiliente permite retomar.\n")

resposta = input("Continuar com sincronizacao de fases? (s/n): ").strip().lower()
if resposta != 's':
    print("\n[CANCELADO] Sincronizacao de fases cancelada.")
    print("Voce pode rodar este script novamente para continuar.\n")
    exit(0)

# Criar arquivo de fila para fases
from sync_zoho import sync_all_phases_for_existing_projects

try:
    sync_all_phases_for_existing_projects()
    print("\n[OK] Fases sincronizadas!")
except KeyboardInterrupt:
    print("\n[AVISO] Sincronizacao de fases interrompida pelo usuario")
    print("Execute este script novamente para retomar de onde parou.\n")
    exit(0)
except Exception as e:
    print(f"\n[ERRO] Falha na sincronizacao de fases: {e}")
    import traceback
    traceback.print_exc()
    print("\nVoce pode executar este script novamente para retomar.\n")
    exit(1)

# Estatísticas finais
session = Session()
try:
    total_projetos_final = session.query(Project).count()
    total_fases_final = session.query(Fase).count()
finally:
    try:
        session.close()
    except:
        pass

print("\n" + "="*80)
print("[SUCESSO] SINCRONIZACAO COMPLETA CONCLUIDA!")
print("="*80)
print(f"\n[ESTATISTICAS FINAIS]")
print(f"  - Projetos: {total_projetos_final}")
print(f"  - Fases: {total_fases_final}")
print(f"  - Media: {total_fases_final/total_projetos_final:.1f} fases/projeto" if total_projetos_final > 0 else "")
print(f"\n[INFO] Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

print("[PROXIMO PASSO]")
print("Agora voce pode fazer deploy no Render!")
print("O banco Neon esta populado e pronto para uso.\n")
