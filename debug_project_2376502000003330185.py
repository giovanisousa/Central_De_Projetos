"""
Debug específico do projeto 2376502000003330185
Verifica dados do Zoho vs Banco e determina coluna correta
"""
import os
import sys
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ZOHO_PORTAL_ID
from database import Project
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import utils

PROJECT_ID = '2376502000003330185'

def obter_access_token():
    return utils.obter_access_token_zoho()

def main():
    db_url = input("Digite a URL do banco PostgreSQL: ").strip()
    
    print("\n" + "="*80)
    print(f"DEBUG: Projeto {PROJECT_ID}")
    print("="*80)
    
    # Buscar do Zoho
    print("\n1️⃣ Buscando dados do Zoho...")
    access_token = obter_access_token()
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}"
    headers = {'Authorization': f'Zoho-oauthtoken {access_token}'}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Erro ao buscar projeto: {response.status_code}")
        print(response.text)
        return
    
    zoho_data = response.json()
    
    # Informações do Zoho
    print(f"\n📊 DADOS DO ZOHO:")
    print(f"   Nome: {zoho_data.get('name')}")
    print(f"   Status ID: {zoho_data.get('status', {}).get('id')}")
    print(f"   Status Nome: {zoho_data.get('status', {}).get('name')}")
    
    tags = zoho_data.get('tags', [])
    print(f"   Tags ({len(tags)}):")
    for tag in tags:
        print(f"      - ID: {tag.get('id')}, Nome: {tag.get('name', 'N/A')}")
    
    owner = zoho_data.get('owner', {})
    print(f"   Proprietário: {owner.get('name')} (ZPUID: {owner.get('zpuid')})")
    
    # Determinar coluna pelo Zoho
    coluna_zoho = utils.determinar_coluna_projeto(zoho_data)
    print(f"   ✅ Coluna determinada (Zoho): '{coluna_zoho}'")
    
    # Buscar do Banco
    print(f"\n2️⃣ Buscando dados do Banco...")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    db_project = session.query(Project).filter(Project.id == PROJECT_ID).first()
    
    if not db_project:
        print("   ⚠️ Projeto NÃO EXISTE no banco!")
    else:
        print(f"\n📊 DADOS DO BANCO:")
        print(f"   Nome: {db_project.nome}")
        print(f"   Status ID: {db_project.status_id}")
        print(f"   Status Atual: {db_project.status_atual}")
        
        if db_project.tags:
            try:
                tags_parsed = json.loads(db_project.tags)
                print(f"   Tags ({len(tags_parsed)}):")
                for tag in tags_parsed:
                    if isinstance(tag, dict):
                        print(f"      - ID: {tag.get('id')}, Nome: {tag.get('name', 'N/A')}")
            except:
                print(f"   Tags (raw): {db_project.tags}")
        else:
            print("   Tags: Nenhuma")
        
        # Determinar coluna pelo banco
        coluna_banco = utils.determinar_coluna_projeto_from_db(db_project)
        print(f"   ✅ Coluna determinada (Banco): '{coluna_banco}'")
    
    # Comparação
    print(f"\n3️⃣ ANÁLISE:")
    
    # Verificar mapeamento
    mapeamento_path = os.path.join(os.path.dirname(__file__), 'mapeamento_colunas.json')
    with open(mapeamento_path, 'r', encoding='utf-8') as f:
        mapeamento = json.load(f)
    
    status_id = str(zoho_data.get('status', {}).get('id'))
    tag_ids = {str(tag.get('id')) for tag in tags if tag.get('id')}
    
    print(f"\n   Status ID do projeto: {status_id}")
    print(f"   Tag IDs do projeto: {tag_ids}")
    
    print(f"\n   📋 Verificando mapeamentos possíveis:")
    
    for coluna_nome, config in mapeamento.items():
        status_esperado = config.get('zohoStatusId')
        tags_esperadas = set(config.get('zohoTagsToAdd', []))
        
        status_match = (str(status_esperado) == status_id)
        
        if tags_esperadas:
            tags_match = tags_esperadas.issubset(tag_ids)
            match_completo = status_match and tags_match
        else:
            tags_match = True  # Não exige tags
            # Verifica se não tem tags conflitantes
            match_completo = status_match and not any(
                str(t) in tag_ids for outras_col, outras_cfg in mapeamento.items()
                if outras_col != coluna_nome and outras_cfg.get('zohoStatusId') == status_esperado
                for t in outras_cfg.get('zohoTagsToAdd', [])
            )
        
        if status_match:
            emoji = "✅" if match_completo else "⚠️"
            print(f"\n   {emoji} {coluna_nome}:")
            print(f"      Status ID: {status_esperado} {'✅' if status_match else '❌'}")
            print(f"      Tags: {tags_esperadas or 'nenhuma'} {'✅' if tags_match else '❌'}")
            print(f"      Match completo: {'SIM' if match_completo else 'NÃO'}")
    
    session.close()

if __name__ == "__main__":
    main()
