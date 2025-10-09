from utils import obter_access_token, _zp_headers
import requests
import json
from config import ZOHO_PORTAL_ID

def get_custom_fields():
    try:
        token = obter_access_token()
        headers = _zp_headers(token)
        
        # Tentar diferentes endpoints para campos customizados
        endpoints = [
            f'/projects/2376502000005544019/customfields',  # campos do projeto
            f'/customfields/project',  # todos os campos customizados de projetos
            f'/projects/2376502000005544019',  # detalhes do projeto com ?custom_fields=true
        ]
        
        for endpoint in endpoints:
            print(f"\n=== Tentando endpoint: {endpoint} ===")
            url = f'https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}{endpoint}'
            
            # Tentar com e sem parâmetro custom_fields
            for params in [None, {'custom_fields': 'true'}]:
                try:
                    resp = requests.get(url, headers=headers, params=params)
                    print(f"Status: {resp.status_code}")
                    data = resp.json()
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except Exception as inner_e:
                    print(f"Erro nesta tentativa: {inner_e}")

    except Exception as e:
        print(f"Erro geral: {e}")

if __name__ == '__main__':
    get_custom_fields()