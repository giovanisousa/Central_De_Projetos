#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Sincronização Completa com o Zoho Projects
=====================================================
Versão: 2.0 (corrigido importação synchronize_single_project)

Este script sincroniza TODOS os dados do Zoho para o banco de dados local:
- Projetos (informações básicas)
- Fases (milestones) de cada projeto
- Listas de tarefas
- Tarefas impeditivas

Uso:
    python sync_complete.py                    # Sincronização completa normal
    python sync_complete.py --force            # Força sincronização de todos os projetos
    python sync_complete.py --phases-only      # Sincroniza apenas as fases
    python sync_complete.py --project-id=XXX   # Sincroniza apenas um projeto específico
"""

import os
import sys
import time
from datetime import datetime

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(message):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80 + "\n")

def print_section(message):
    """Imprime seção formatada"""
    print(f"\n--- {message} ---")

def main():
    """Função principal de sincronização"""
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print_header(f"SINCRONIZAÇÃO COMPLETA - {timestamp}")
    
    # Processar argumentos
    force_sync = '--force' in sys.argv
    phases_only = '--phases-only' in sys.argv
    project_id = None
    
    for arg in sys.argv:
        if arg.startswith('--project-id='):
            project_id = arg.split('=')[1]
    
    # Importar módulos necessários
    try:
        from sync_zoho import synchronize_projects, sync_all_phases_for_existing_projects, synchronize_single_project
        from database import Session, Project, Fase, count_projects
        
        print("✓ Módulos carregados com sucesso")
    except Exception as e:
        print(f"✗ ERRO ao carregar módulos: {e}")
        sys.exit(1)
    
    # Estatísticas ANTES da sincronização
    print_section("Estatísticas ANTES da sincronização")
    session = Session()
    try:
        total_projects_antes = session.query(Project).count()
        total_fases_antes = session.query(Fase).count()
        print(f"  • Projetos no banco: {total_projects_antes}")
        print(f"  • Fases no banco: {total_fases_antes}")
    finally:
        session.close()
    
    # EXECUÇÃO DA SINCRONIZAÇÃO
    try:
        if project_id:
            # Sincronizar apenas um projeto específico
            print_section(f"Sincronizando projeto específico: {project_id}")
            from utils import obter_access_token
            access_token = obter_access_token()
            success = synchronize_single_project(project_id, access_token)
            if success:
                print(f"✓ Projeto {project_id} sincronizado com sucesso")
            else:
                print(f"✗ Falha ao sincronizar projeto {project_id}")
        
        elif phases_only:
            # Sincronizar apenas fases de projetos existentes
            print_section("Sincronizando APENAS FASES dos projetos existentes")
            sync_all_phases_for_existing_projects()
        
        else:
            # Sincronização completa
            print_section("Sincronizando projetos do Zoho")
            if force_sync:
                print("  MODO: Forçar sincronização de TODOS os projetos")
                # Temporariamente zera o last_sync_time para forçar sincronização completa
                from database import update_last_sync_time
                update_last_sync_time('2000-01-01T00:00:00Z')
            
            synchronize_projects()
            
            # Após sincronizar projetos, sincronizar fases de todos
            print_section("Sincronizando fases de todos os projetos")
            sync_all_phases_for_existing_projects()
    
    except Exception as e:
        print(f"\n✗ ERRO durante sincronização: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Estatísticas DEPOIS da sincronização
    print_section("Estatísticas DEPOIS da sincronização")
    session = Session()
    try:
        total_projects_depois = session.query(Project).count()
        total_fases_depois = session.query(Fase).count()
        print(f"  • Projetos no banco: {total_projects_depois} (Δ +{total_projects_depois - total_projects_antes})")
        print(f"  • Fases no banco: {total_fases_depois} (Δ +{total_fases_depois - total_fases_antes})")
        print(f"  • Média de fases por projeto: {total_fases_depois / total_projects_depois if total_projects_depois > 0 else 0:.1f}")
    finally:
        session.close()
    
    # Tempo total
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print_header(f"SINCRONIZAÇÃO CONCLUÍDA - Tempo total: {minutes}m {seconds}s")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
