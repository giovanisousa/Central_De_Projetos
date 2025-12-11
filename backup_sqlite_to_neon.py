#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Backup: SQLite Local → PostgreSQL Neon
=================================================

Este script copia TODOS os dados do banco SQLite local para o Neon PostgreSQL.

Processo:
1. Conecta no SQLite local (zoho_cache.db)
2. Conecta no PostgreSQL Neon
3. Copia todos os registros (projetos, fases, listas, tarefas)
4. Usa BULK INSERT para alta performance
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

print("\n" + "="*80)
print("  BACKUP: SQLite Local → PostgreSQL Neon")
print("="*80 + "\n")

# Configurar engines
SQLITE_URI = 'sqlite:///zoho_cache.db'
NEON_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')

if not NEON_URI or 'sqlite' in NEON_URI.lower():
    print("✗ ERRO: SQLALCHEMY_DATABASE_URI não configurada no .env!")
    print("Configure a conexão do Neon PostgreSQL primeiro.\n")
    sys.exit(1)

print(f"Origem:  {SQLITE_URI}")
print(f"Destino: {NEON_URI[:50]}...\n")

# Importar modelos
from database import Base, Project, Fase, ListaDeTarefas, Tarefa

# Criar engines
print("[1/5] Conectando aos bancos...")
sqlite_engine = create_engine(SQLITE_URI)
neon_engine = create_engine(NEON_URI, pool_pre_ping=True, pool_recycle=300)

SQLiteSession = sessionmaker(bind=sqlite_engine)
NeonSession = sessionmaker(bind=neon_engine)

sqlite_session = SQLiteSession()
neon_session = NeonSession()

# Verificar dados de origem
print("\n[2/5] Verificando dados do SQLite local...")
try:
    total_projetos_sqlite = sqlite_session.query(Project).count()
    total_fases_sqlite = sqlite_session.query(Fase).count()
    total_listas_sqlite = sqlite_session.query(ListaDeTarefas).count()
    total_tarefas_sqlite = sqlite_session.query(Tarefa).count()
    
    print(f"  - Projetos: {total_projetos_sqlite}")
    print(f"  - Fases: {total_fases_sqlite}")
    print(f"  - Listas: {total_listas_sqlite}")
    print(f"  - Tarefas: {total_tarefas_sqlite}")
    
    if total_projetos_sqlite == 0:
        print("\n✗ ERRO: Banco SQLite está vazio!")
        print("Execute 'python sync_local_completo.py' primeiro.\n")
        sys.exit(1)
        
except Exception as e:
    print(f"\n✗ ERRO ao acessar SQLite: {e}")
    sys.exit(1)

# Verificar dados de destino
print("\n[3/5] Verificando dados do Neon PostgreSQL...")
try:
    total_projetos_neon = neon_session.query(Project).count()
    total_fases_neon = neon_session.query(Fase).count()
    
    print(f"  - Projetos atuais: {total_projetos_neon}")
    print(f"  - Fases atuais: {total_fases_neon}")
    
    if total_projetos_neon > 0:
        print("\n⚠️  ATENÇÃO: O banco Neon já tem dados!")
        resposta = input("Deseja APAGAR tudo e substituir pelo backup? (s/n): ").strip().lower()
        
        if resposta != 's':
            print("\n[CANCELADO] Backup cancelado pelo usuário.\n")
            sys.exit(0)
        
        print("\n  Limpando banco Neon...")
        neon_session.query(Tarefa).delete()
        neon_session.query(ListaDeTarefas).delete()
        neon_session.query(Fase).delete()
        neon_session.query(Project).delete()
        neon_session.commit()
        print("  ✓ Banco Neon limpo!")
        
except Exception as e:
    print(f"\n✗ ERRO ao acessar Neon: {e}")
    neon_session.rollback()
    sys.exit(1)

# COPIAR DADOS
print("\n[4/5] Copiando dados do SQLite para o Neon...")

try:
    # 1. PROJETOS
    print("\n  [1/4] Copiando projetos...")
    projetos = sqlite_session.query(Project).all()
    for i, projeto in enumerate(projetos, 1):
        if i % 10 == 0:
            print(f"    - {i}/{total_projetos_sqlite} projetos...")
        
        # Criar dicionário com todos os atributos que existem no objeto
        projeto_dict = {}
        for column in Project.__table__.columns:
            column_name = column.name
            projeto_dict[column_name] = getattr(projeto, column_name, None)
        
        # Usar merge que faz upsert automático
        neon_session.merge(Project(**projeto_dict))
    
    neon_session.commit()
    print(f"  ✓ {total_projetos_sqlite} projetos copiados!")
    
    # 2. FASES
    print("\n  [2/4] Copiando fases...")
    fases = sqlite_session.query(Fase).all()
    for i, fase in enumerate(fases, 1):
        if i % 50 == 0:
            print(f"    - {i}/{total_fases_sqlite} fases...")
        
        # Copiar todos os atributos dinamicamente
        fase_dict = {}
        for column in Fase.__table__.columns:
            fase_dict[column.name] = getattr(fase, column.name, None)
        
        neon_session.merge(Fase(**fase_dict))
    
    neon_session.commit()
    print(f"  ✓ {total_fases_sqlite} fases copiadas!")
    
    # 3. LISTAS DE TAREFAS
    print("\n  [3/4] Copiando listas de tarefas...")
    listas = sqlite_session.query(ListaDeTarefas).all()
    for i, lista in enumerate(listas, 1):
        if i % 50 == 0:
            print(f"    - {i}/{total_listas_sqlite} listas...")
        
        # Copiar todos os atributos dinamicamente
        lista_dict = {}
        for column in ListaDeTarefas.__table__.columns:
            lista_dict[column.name] = getattr(lista, column.name, None)
        
        neon_session.merge(ListaDeTarefas(**lista_dict))
    
    neon_session.commit()
    print(f"  ✓ {total_listas_sqlite} listas copiadas!")
    
    # 4. TAREFAS
    print("\n  [4/4] Copiando tarefas...")
    tarefas = sqlite_session.query(Tarefa).all()
    for i, tarefa in enumerate(tarefas, 1):
        if i % 100 == 0:
            print(f"    - {i}/{total_tarefas_sqlite} tarefas...")
        
        # Copiar todos os atributos dinamicamente
        tarefa_dict = {}
        for column in Tarefa.__table__.columns:
            tarefa_dict[column.name] = getattr(tarefa, column.name, None)
        
        neon_session.merge(Tarefa(**tarefa_dict))
    
    neon_session.commit()
    print(f"  ✓ {total_tarefas_sqlite} tarefas copiadas!")
    
except Exception as e:
    print(f"\n✗ ERRO durante cópia: {e}")
    neon_session.rollback()
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    sqlite_session.close()

# VERIFICAR RESULTADO
print("\n[5/5] Verificando resultado no Neon...")
try:
    total_projetos_final = neon_session.query(Project).count()
    total_fases_final = neon_session.query(Fase).count()
    total_listas_final = neon_session.query(ListaDeTarefas).count()
    total_tarefas_final = neon_session.query(Tarefa).count()
finally:
    neon_session.close()

print("\n" + "="*80)
print("  RESULTADO DO BACKUP")
print("="*80 + "\n")

print("📊 Dados copiados para o Neon PostgreSQL:")
print(f"  - Projetos: {total_projetos_final}")
print(f"  - Fases: {total_fases_final}")
print(f"  - Listas: {total_listas_final}")
print(f"  - Tarefas: {total_tarefas_final}")

if total_projetos_final == total_projetos_sqlite:
    print("\n✅ BACKUP COMPLETO COM SUCESSO!")
    print("\nAgora você pode fazer deploy no Render.")
    print("O banco Neon está 100% sincronizado!\n")
else:
    print("\n⚠️  ATENÇÃO: Alguns registros podem não ter sido copiados.")
    print(f"Esperado: {total_projetos_sqlite} projetos")
    print(f"Copiado: {total_projetos_final} projetos\n")

print("="*80 + "\n")
