"""
Sincroniza projetos específicos identificados na validação:
- Em Operação Assistida: 2 projetos
- Aguardando Encerramento: 1 projeto
- Projeto Parado: 2 projetos
Total: 5 projetos
"""
import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
from database import upsert_project
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import utils

# IDs identificados na validação
PROJECTS_TO_SYNC = {
    'Em Operação Assistida': [
        '2376502000004886545',  # 1172 - Hospital Geral Intermunicipal
        '2376502000002763533',  # 1091 - Pro Imagem Diagnóstico
    ],
    'Aguardando Encerramento': [
        '2376502000003782093',  # 1135 - IMR - INSTITUTO MARQUES DE RADIOLOGIA
    ],
    'Projeto Parado': [
        '2376502000001249141',  # Hugolino Andrade - NR
        '2376502000000351049',  # Clinica Dr. Edson Coltro - NR/AP
    ]
}

def get_access_token():
    """Obtém access token do Zoho"""
    return utils.obter_access_token_zoho()

def fetch_project_from_zoho(project_id, access_token):
    """Busca projeto específico do Zoho API v3"""
    from config import ZOHO_PORTAL_ID
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = {'Authorization': f'Zoho-oauthtoken {access_token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:
        # Token expirou, renova
        print("   🔄 Token expirado, renovando...")
        access_token = get_access_token()
        headers['Authorization'] = f'Zoho-oauthtoken {access_token}'
        response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json(), access_token
    elif response.status_code == 410:
        print(f"   ⚠️ Projeto {project_id} excluído no Zoho (HTTP 410)")
        return None, access_token
    elif response.status_code == 404:
        print(f"   ⚠️ Projeto {project_id} não encontrado (HTTP 404)")
        return None, access_token
    else:
        raise Exception(f"Erro HTTP {response.status_code}: {response.text}")

def main():
    db_url = input("📝 Cole a URL do PostgreSQL do Railway: ").strip()
    if not db_url:
        print("\n❌ URL do banco é obrigatória!")
        sys.exit(1)
    
    # Reconfigura database para usar URL externa
    database.engine = create_engine(db_url)
    database.Session = sessionmaker(bind=database.engine)
    
    print("\n" + "="*80)
    print("🔄 SINCRONIZAÇÃO DE PROJETOS ESPECÍFICOS (Giovani)")
    print("="*80)
    
    access_token = get_access_token()
    
    total_sync = 0
    total_errors = 0
    results_by_column = {}
    
    for coluna, ids in PROJECTS_TO_SYNC.items():
        print(f"\n{'='*80}")
        print(f"📂 Coluna: {coluna}")
        print(f"{'='*80}")
        
        sync_count = 0
        error_count = 0
        
        for idx, project_id in enumerate(ids, 1):
            print(f"\n[{idx}/{len(ids)}] Sincronizando projeto {project_id}...")
            
            try:
                project_data, access_token = fetch_project_from_zoho(project_id, access_token)
                
                if project_data is None:
                    error_count += 1
                    continue
                
                # Sincroniza no banco
                upsert_project(project_data)
                
                # Mostra info
                nome = project_data.get('name', 'N/A')
                status = project_data.get('status', {})
                status_nome = status.get('name', 'N/A')
                
                print(f"   ✅ {nome}")
                print(f"   Status: {status_nome}")
                
                sync_count += 1
                
            except Exception as e:
                print(f"   ❌ Erro: {str(e)}")
                error_count += 1
        
        results_by_column[coluna] = {
            'sincronizados': sync_count,
            'erros': error_count
        }
        total_sync += sync_count
        total_errors += error_count
    
    # Resumo final
    print("\n" + "="*80)
    print("📊 RESUMO DA SINCRONIZAÇÃO")
    print("="*80)
    
    for coluna, result in results_by_column.items():
        print(f"\n{coluna}:")
        print(f"   ✅ Sincronizados: {result['sincronizados']}")
        print(f"   ❌ Erros: {result['erros']}")
    
    print(f"\n{'='*80}")
    print(f"Total sincronizados: {total_sync}")
    print(f"Total erros: {total_errors}")
    print("="*80)

if __name__ == "__main__":
    main()
