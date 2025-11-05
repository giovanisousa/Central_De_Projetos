"""
Script para identificar quais projetos em 'Falta Liberar Servidor Infra' 
são os 8 corretos e quais são os 6 extras.
"""

import os
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# IDs corretos fornecidos pelo usuário
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

# Adicionar o diretório raiz ao path para importar módulos locais
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adicionar o diretório raiz ao path para importar módulos locais
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import determinar_coluna_projeto_from_db
from database import Project

def main():
    # Conectar ao banco usando URL externa
    db_url = input("Digite a URL do banco PostgreSQL (ex: postgresql://user:pass@host:port/db): ").strip()
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n" + "="*80)
    print("ANÁLISE: Projetos em 'Falta Liberar Servidor Infra'")
    print("="*80)
    
    # Buscar todos os projetos do banco usando ORM
    projects = session.query(Project).order_by(Project.nome).all()
    
    # Filtrar projetos que aparecem na coluna
    projects_in_column = []
    for row in projects:
        coluna = determinar_coluna_projeto_from_db(row)
        if coluna == "Falta Liberar Servidor Infra":
            projects_in_column.append(row)
    
    print(f"\nTotal de projetos no banco nesta coluna: {len(projects_in_column)}")
    print(f"Total de projetos corretos esperados: {len(CORRECT_IDS)}")
    print(f"Diferença (extras): {len(projects_in_column) - len(CORRECT_IDS)}")
    
    # Separar em corretos e extras
    correct_projects = []
    extra_projects = []
    
    for row in projects_in_column:
        zoho_id = str(row.id)
        if zoho_id in CORRECT_IDS:
            correct_projects.append(row)
        else:
            extra_projects.append(row)
    
    # Mostrar projetos CORRETOS
    print("\n" + "-"*80)
    print(f"PROJETOS CORRETOS ({len(correct_projects)}/{len(CORRECT_IDS)}):")
    print("-"*80)
    
    for i, row in enumerate(correct_projects, 1):
        tags_parsed = []
        if row.tags:
            try:
                tags_data = json.loads(row.tags)
                for tag in tags_data:
                    if isinstance(tag, dict):
                        tags_parsed.append(f"{tag.get('id')} ({tag.get('name')})")
            except:
                tags_parsed = [row.tags]
        
        print(f"\n{i}. {row.nome}")
        print(f"   Zoho ID: {row.id}")
        print(f"   Status ID: {row.status_id}")
        print(f"   Status Atual: {row.status_atual}")
        print(f"   Tags: {', '.join(tags_parsed) if tags_parsed else 'Sem tags'}")
    
    # Mostrar projetos EXTRAS
    print("\n" + "="*80)
    print(f"PROJETOS EXTRAS (NÃO DEVERIAM ESTAR NESTA COLUNA) - {len(extra_projects)} encontrados:")
    print("="*80)
    
    for i, row in enumerate(extra_projects, 1):
        tags_parsed = []
        if row.tags:
            try:
                tags_data = json.loads(row.tags)
                for tag in tags_data:
                    if isinstance(tag, dict):
                        tags_parsed.append(f"{tag.get('id')} ({tag.get('name')})")
            except:
                tags_parsed = [row.tags]
        
        print(f"\n{i}. {row.nome}")
        print(f"   Zoho ID: {row.id}")
        print(f"   Status ID: {row.status_id}")
        print(f"   Status Atual: {row.status_atual}")
        print(f"   Tags: {', '.join(tags_parsed) if tags_parsed else 'Sem tags'}")
    
    # Verificar se algum ID correto está faltando
    found_ids = [str(row.id) for row in correct_projects]
    missing_ids = [id for id in CORRECT_IDS if id not in found_ids]
    
    if missing_ids:
        print("\n" + "="*80)
        print(f"ATENÇÃO: IDs CORRETOS FALTANDO NO BANCO ({len(missing_ids)}):")
        print("="*80)
        for id in missing_ids:
            print(f"   - {id}")
    
    print("\n" + "="*80)
    print("RESUMO:")
    print("="*80)
    print(f"Projetos corretos encontrados: {len(correct_projects)}/{len(CORRECT_IDS)}")
    print(f"Projetos extras (incorretos): {len(extra_projects)}")
    print(f"Projetos corretos faltando: {len(missing_ids)}")
    
    session.close()

if __name__ == "__main__":
    main()
