from utils import obter_access_token, _zp_headers
import requests
import json
from config import ZOHO_PORTAL_ID

def get_project_layout():
    try:
        token = obter_access_token()
        headers = _zp_headers(token)
        
        # Obter detalhes do layout do projeto
        layout_url = f'https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/layouts/2376502000005584766'
        resp = requests.get(layout_url, headers=headers)
        data = resp.json()
        
        print("\n=== Layout do Projeto ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Erro: {e}")
        if isinstance(e, requests.exceptions.RequestException):
            print(f"\nDetalhes da requisição:")
            print(f"URL: {layout_url}")
            print(f"Headers: {headers}")

if __name__ == '__main__':
    get_project_layout()