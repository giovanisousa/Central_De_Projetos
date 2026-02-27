#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script OTIMIZADO para sincronizar apenas FASES do banco Neon
=============================================================

Este script:
1. NÃO busca projetos do Zoho (economiza tempo e chamadas de API)
2. Sincroniza apenas as fases dos 39 projetos já existentes no banco
3. Renova o token Zoho automaticamente a cada 30 minutos
4. Reconecta ao banco a cada 10 projetos

Tempo estimado: ~10-15 minutos
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*80)
print("  SINCRONIZANDO APENAS FASES - Banco Neon")
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
print(f"  Este script vai sincronizar fases de TODOS os {projetos_atual} projetos")
print(f"  Tempo estimado: ~{projetos_atual * 2 / 60:.0f} minutos")
print(f"\n")

resposta = input("Deseja continuar? (s/n): ").strip().lower()
if resposta != 's':
    print("\n[CANCELADO] Sincronizacao cancelada pelo usuario.\n")
    exit(0)

print("\n[INICIANDO] Sincronizacao de fases em progresso...")
print("="*80 + "\n")

# Importar função
from sync_zoho import sync_all_phases_for_existing_projects

try:
    # Sincronizar APENAS fases
    sync_all_phases_for_existing_projects()
    
    # Estatísticas finais
    session = Session()
    fases_final = session.query(Fase).count()
    session.close()
    
    print("\n" + "="*80)
    print("[SUCESSO] Sincronizacao de fases concluida!")
    print("="*80)
    print(f"\n[RESULTADO FINAL]")
    print(f"  - Projetos: {projetos_atual} (inalterado)")
    print(f"  - Fases: {fases_atual} -> {fases_final} (+{fases_final - fases_atual})")
    print(f"  - Media final: {fases_final/projetos_atual:.1f} fases/projeto" if projetos_atual > 0 else "  - Media: N/A")
    print("\n" + "="*80 + "\n")
    
except Exception as e:
    print(f"\n[ERRO] Sincronizacao interrompida: {e}")
    print("\nVoce pode executar este script novamente para continuar.\n")
    import traceback
    traceback.print_exc()
