#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para LIMPAR o banco e fazer sincronização COMPLETA
==========================================================

Este script:
1. Limpa TODOS os dados do banco Neon
2. Executa sincronização completa do zero (sem filtro de data)
3. Busca TODOS os 112 projetos do Zoho

ATENÇÃO: Vai apagar todos os projetos/fases/listas/tarefas do banco!
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*80)
print("  ⚠️  LIMPEZA COMPLETA E RESSINCRONIZAÇÃO")
print("="*80 + "\n")

print("[AVISO] Este script vai APAGAR todos os dados do banco Neon e")
print("        sincronizar novamente do zero para buscar os 112 projetos.\n")

resposta = input("Tem certeza que deseja continuar? (s/n): ").strip().lower()
if resposta != 's':
    print("\n[CANCELADO] Operação cancelada pelo usuário.\n")
    exit(0)

print("\n[1/3] Limpando banco de dados...")

from database import Session, Project, Fase, ListaDeTarefas, Tarefa, engine, Base

session = Session()
try:
    # Deleta na ordem correta (por causa de foreign keys)
    print("  - Deletando tarefas...")
    session.query(Tarefa).delete()
    
    print("  - Deletando listas de tarefas...")
    session.query(ListaDeTarefas).delete()
    
    print("  - Deletando fases...")
    session.query(Fase).delete()
    
    print("  - Deletando projetos...")
    session.query(Project).delete()
    
    session.commit()
    print("  ✓ Banco limpo com sucesso!")
    
except Exception as e:
    session.rollback()
    print(f"  ✗ ERRO ao limpar banco: {e}")
    exit(1)
finally:
    session.close()

print("\n[2/3] Verificando estado do banco...")
session = Session()
try:
    total_projetos = session.query(Project).count()
    total_fases = session.query(Fase).count()
    print(f"  - Projetos: {total_projetos}")
    print(f"  - Fases: {total_fases}")
    
    if total_projetos > 0 or total_fases > 0:
        print("  ✗ ERRO: Banco não está vazio!")
        exit(1)
    
    print("  ✓ Banco vazio confirmado!")
    
finally:
    session.close()

print("\n[3/3] Iniciando sincronização COMPLETA do zero...")
print("Esta etapa vai buscar TODOS os projetos do Zoho (112 projetos esperados).\n")

from sync_zoho import synchronize_projects

try:
    synchronize_projects()
    print("\n[SUCESSO] Sincronização completa concluída!")
    
except KeyboardInterrupt:
    print("\n[AVISO] Sincronização interrompida pelo usuário.")
    print("Execute 'python sync_completa_resiliente.py' para continuar.\n")
    exit(0)
    
except Exception as e:
    print(f"\n[ERRO] Falha na sincronização: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Estatísticas finais
print("\n" + "="*80)
print("  RESULTADO DA SINCRONIZAÇÃO")
print("="*80 + "\n")

session = Session()
try:
    total_projetos_final = session.query(Project).count()
    total_fases_final = session.query(Fase).count()
    
    print(f"📊 Projetos sincronizados: {total_projetos_final}")
    print(f"📊 Fases sincronizadas: {total_fases_final}")
    
    if total_projetos_final < 100:
        print(f"\n⚠️  ATENÇÃO: Esperava-se ~112 projetos, mas foram sincronizados apenas {total_projetos_final}!")
        print("Verifique os filtros de proprietário e status.\n")
    else:
        print(f"\n✅ Sucesso! {total_projetos_final} projetos sincronizados.\n")
    
finally:
    session.close()

print("="*80 + "\n")
