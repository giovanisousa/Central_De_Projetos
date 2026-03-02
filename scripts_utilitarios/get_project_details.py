import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
os.chdir(ROOT_DIR)

from utils import obter_access_token, _zp_headers
import requests
import json
from config import ZOHO_PORTAL_ID

def get_project_details():
    try:
        token = obter_access_token()
        headers = _zp_headers(token)
        
        # Obter detalhes completos do projeto usando o PORTAL_ID da config
        project_url = f'https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/2376502000007984003'
        resp = requests.get(project_url, headers=headers)
        data = resp.json()
        
        # Imprimir o JSON completo para análise
        print("\n=== JSON Completo do Projeto ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # Procurar especificamente por campos que começam com data_ ou cf_
        if isinstance(data, dict):
            print("\n=== Campos Customizados Encontrados ===")
            for key in data.keys():
                if key.startswith(('data_', 'cf_')) or key == 'custom_fields':
                    print(f"Nome do campo: {key}")
            
            if 'custom_fields' in data:
                print("\n=== Conteúdo de custom_fields ===")
                print(json.dumps(data['custom_fields'], indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Erro: {e}")
        if isinstance(e, requests.exceptions.RequestException):
            print(f"\nDetalhes da requisição:")
            print(f"URL: {project_url}")
            print(f"Headers: {headers}")

if __name__ == '__main__':
    get_project_details()