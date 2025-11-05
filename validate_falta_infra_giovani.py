"""
Validação da coluna 'Falta Liberar Servidor Infra' 
filtrando apenas projetos do proprietário Giovani.
"""

import os
import sys
import json

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Project
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils import determinar_coluna_projeto_from_db

# ZPUID do Giovani
GIOVANI_ZPUID = '2376502000000057291'

# IDs corretos fornecidos pelo usuário (projetos do Giovani)
CORRECT_IDS = [
    '2376502000006322069',
    '2376502000005824904',
    '2376502000005824705',
    '2376502000005726003',
    '2376502000005542081',
    '2376502000005235445',
    '2376502000004208431',
    '2376502000003549073'
]

def main():
    # Conectar ao banco usando URL externa
    db_url = input("Digite a URL do banco PostgreSQL (ex: postgresql://user:pass@host:port/db): ").strip()
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n" + "="*80)
    print("VALIDAÇÃO: Projetos do Giovani em 'Falta Liberar Servidor Infra'")
    print("="*80)
    
    # Buscar todos os projetos do banco
    projects = session.query(Project).all()
    
    # Filtrar projetos que aparecem na coluna E são do Giovani
    projects_in_column_giovani = []
    projects_in_column_willian = []
    
    for row in projects:
        coluna = determinar_coluna_projeto_from_db(row)
        if coluna == "Falta Liberar Servidor Infra":
            # Verificar proprietário
            if row.full_data_json:
                try:
                    data = json.loads(row.full_data_json)
                    owner = data.get('owner', {})
                    owner_zpuid = owner.get('zpuid', '')
                    owner_name = owner.get('name', 'N/A')
                    
                    if owner_zpuid == GIOVANI_ZPUID:
                        projects_in_column_giovani.append(row)
                    else:
                        projects_in_column_willian.append((row, owner_name))
                except:
                    # Se não conseguir parsear, adiciona como desconhecido
                    projects_in_column_giovani.append(row)
    
    print(f"\nTotal de projetos na coluna: {len(projects_in_column_giovani) + len(projects_in_column_willian)}")
    print(f"  - Projetos do Giovani: {len(projects_in_column_giovani)}")
    print(f"  - Projetos de outros proprietários: {len(projects_in_column_willian)}")
    
    # Separar projetos do Giovani em corretos e extras
    correct_projects = []
    extra_projects = []
    
    for row in projects_in_column_giovani:
        if str(row.id) in CORRECT_IDS:
            correct_projects.append(row)
        else:
            extra_projects.append(row)
    
    # Verificar IDs faltando
    found_ids = [str(row.id) for row in correct_projects]
    missing_ids = [id for id in CORRECT_IDS if id not in found_ids]
    
    # Mostrar projetos CORRETOS do Giovani
    print("\n" + "-"*80)
    print(f"PROJETOS CORRETOS DO GIOVANI ({len(correct_projects)}/{len(CORRECT_IDS)}):")
    print("-"*80)
    
    for i, row in enumerate(correct_projects, 1):
        tags_parsed = []
        if row.tags:
            try:
                tags_data = json.loads(row.tags)
                for tag in tags_data:
                    if isinstance(tag, dict):
                        tags_parsed.append(f"{tag.get('id')}")
            except:
                tags_parsed = [row.tags]
        
        print(f"\n{i}. {row.nome}")
        print(f"   Zoho ID: {row.id}")
        print(f"   Status: {row.status_atual}")
        print(f"   Tags: {', '.join(tags_parsed) if tags_parsed else 'Sem tags'}")
    
    # Mostrar projetos EXTRAS do Giovani
    if extra_projects:
        print("\n" + "="*80)
        print(f"PROJETOS EXTRAS DO GIOVANI ({len(extra_projects)}):")
        print("="*80)
        
        for i, row in enumerate(extra_projects, 1):
            tags_parsed = []
            if row.tags:
                try:
                    tags_data = json.loads(row.tags)
                    for tag in tags_data:
                        if isinstance(tag, dict):
                            tags_parsed.append(f"{tag.get('id')}")
                except:
                    tags_parsed = [row.tags]
            
            print(f"\n{i}. {row.nome}")
            print(f"   Zoho ID: {row.id}")
            print(f"   Status: {row.status_atual}")
            print(f"   Tags: {', '.join(tags_parsed) if tags_parsed else 'Sem tags'}")
    
    # Mostrar projetos de OUTROS proprietários
    if projects_in_column_willian:
        print("\n" + "="*80)
        print(f"PROJETOS DE OUTROS PROPRIETÁRIOS ({len(projects_in_column_willian)}):")
        print("="*80)
        
        for i, (row, owner_name) in enumerate(projects_in_column_willian, 1):
            print(f"\n{i}. {row.nome}")
            print(f"   Zoho ID: {row.id}")
            print(f"   Proprietário: {owner_name}")
            print(f"   Status: {row.status_atual}")
    
    # Mostrar IDs faltando
    if missing_ids:
        print("\n" + "="*80)
        print(f"IDs CORRETOS FALTANDO NO BANCO ({len(missing_ids)}):")
        print("="*80)
        for id in missing_ids:
            print(f"   - {id}")
    
    print("\n" + "="*80)
    print("RESUMO:")
    print("="*80)
    print(f"Projetos corretos do Giovani: {len(correct_projects)}/{len(CORRECT_IDS)}")
    print(f"Projetos extras do Giovani: {len(extra_projects)}")
    print(f"Projetos de outros proprietários: {len(projects_in_column_willian)}")
    print(f"Projetos corretos faltando: {len(missing_ids)}")
    
    session.close()

if __name__ == "__main__":
    main()
