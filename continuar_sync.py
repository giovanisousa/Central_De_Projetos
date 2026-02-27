#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para CONTINUAR a sincronização do banco Neon
====================================================

Use este script se a sincronização foi interrompida por erro de conexão.
Ele vai sincronizar apenas o que ainda falta.

IMPORTANTE: O script usa last_modified_time, então só buscará:
- Projetos novos desde a última sincronização
- Projetos modificados desde a última sincronização
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*80)
print("  CONTINUANDO SINCRONIZACAO - Banco Neon")
print("="*80 + "\n")

# Verificar estado atual
from database import Session, Project, Fase

session = Session()
projetos_atual = session.query(Project).count()
fases_atual = session.query(Fase).count()
session.close()

print(f"[ESTADO ATUAL]")
print(f"  - Projetos no banco: {projetos_atual}")
print(f"  - Fases no banco: {fases_atual}")
print(f"  - Media: {fases_atual/projetos_atual:.1f} fases/projeto" if projetos_atual > 0 else "  - Media: N/A")

print(f"\n[ACAO]")
print(f"  Este script vai:")
print(f"  1. Buscar projetos novos/modificados do Zoho")
print(f"  2. Sincronizar fases de TODOS os projetos no banco")
print(f"\n")

resposta = input("Deseja continuar? (s/n): ").strip().lower()
if resposta != 's':
    print("\n[CANCELADO] Sincronizacao cancelada pelo usuario.\n")
    exit(0)

print("\n[INICIANDO] Sincronizacao em progresso...")
print("="*80 + "\n")

# Importar funções
from sync_zoho import synchronize_projects, sync_all_phases_for_existing_projects

try:
    # ETAPA 1: Buscar novos projetos
    print("\n[ETAPA 1/2] Sincronizando projetos novos/modificados...\n")
    synchronize_projects()
    
    # ETAPA 2: Sincronizar fases de todos
    print("\n[ETAPA 2/2] Sincronizando fases de todos os projetos...\n")
    sync_all_phases_for_existing_projects()
    
    # Estatísticas finais
    session = Session()
    projetos_final = session.query(Project).count()
    fases_final = session.query(Fase).count()
    session.close()
    
    print("\n" + "="*80)
    print("[SUCESSO] Sincronizacao concluida!")
    print("="*80)
    print(f"\n[RESULTADO FINAL]")
    print(f"  - Projetos: {projetos_atual} -> {projetos_final} (+{projetos_final - projetos_atual})")
    print(f"  - Fases: {fases_atual} -> {fases_final} (+{fases_final - fases_atual})")
    print(f"  - Media final: {fases_final/projetos_final:.1f} fases/projeto" if projetos_final > 0 else "  - Media: N/A")
    print("\n" + "="*80 + "\n")
    
except Exception as e:
    print(f"\n[ERRO] Sincronizacao interrompida: {e}")
    print("\nVoce pode executar este script novamente para continuar.\n")
    import traceback
    traceback.print_exc()
