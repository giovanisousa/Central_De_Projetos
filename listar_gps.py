"""
Script para listar todos os GPs (owners) únicos dos projetos.
"""

import requests
import time
from config import ZOHO_PORTAL_ID
import utils


def buscar_todos_projetos(access_token):
    """Busca todos os projetos do portal."""
    print("🔍 Buscando todos os projetos do portal...")
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
    
    todos_projetos = []
    index = 1
    range_size = 200
    
    while True:
        params = {
            "index": index,
            "range": range_size
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                break
            
            data = response.json()
            
            if isinstance(data, list):
                projetos = data
            elif isinstance(data, dict):
                projetos = data.get('projects', [])
            else:
                break
            
            if not projetos:
                break
            
            todos_projetos.extend(projetos)
            
            if len(projetos) < range_size:
                break
            
            index += range_size
            # Polling: aguarda até 2s ou até que próximo fetch esteja disponível
            import time
            polling_timeout = 2
            polling_interval = 0.3
            polling_start = time.time()
            while time.time() - polling_start < polling_timeout:
                print(f"[polling] aguardando próximo fetch... ({int((time.time()-polling_start)*1000)}ms)")
                time.sleep(polling_interval)
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            break
    
    return todos_projetos


def main():
    """Função principal."""
    print("=" * 80)
    print("📋 LISTANDO TODOS OS GPs (OWNERS) DOS PROJETOS")
    print("=" * 80)
    print()
    
    # Obter access token
    try:
        access_token = utils.obter_access_token()
        print("✅ Access token obtido\n")
    except Exception as e:
        print(f"❌ Erro ao obter access token: {e}")
        return
    
    # Buscar todos os projetos
    todos_projetos = buscar_todos_projetos(access_token)
    print(f"✅ Total de projetos: {len(todos_projetos)}\n")
    
    # Extrair owners únicos
    owners = {}
    
    for projeto in todos_projetos:
        owner = projeto.get('owner', {})
        owner_name = owner.get('name', 'Sem nome')
        owner_id = owner.get('id', 'Sem ID')
        
        if owner_name not in owners:
            owners[owner_name] = {
                'id': owner_id,
                'count': 0
            }
        owners[owner_name]['count'] += 1
    
    # Ordenar por quantidade de projetos (decrescente)
    owners_sorted = sorted(owners.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print("=" * 80)
    print("📊 GPs ENCONTRADOS (ordenados por quantidade de projetos):")
    print("=" * 80)
    print()
    
    for owner_name, info in owners_sorted:
        print(f"👤 {owner_name}")
        print(f"   ID: {info['id']}")
        print(f"   Projetos: {info['count']}")
        print()
    
    print("=" * 80)
    print(f"Total de GPs únicos: {len(owners)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
