from utils import obter_access_token, _zp_headers
import requests
import json
from config import ZOHO_PORTAL_ID

def get_layout_fields():
    try:
        token = obter_access_token()
        headers = _zp_headers(token)
        
        # Tentar obter os campos do layout
        layout_id = "2376502000005584766"  # ID do layout do projeto
        url = f'https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/layout/{layout_id}/customfields/'
        
        print(f"URL: {url}")
        print(f"Headers: {headers}")
        
        resp = requests.get(url, headers=headers)
        print(f"\nStatus: {resp.status_code}")
        print("\nResposta:")
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Erro: {e}")
        if isinstance(e, requests.exceptions.RequestException):
            print(f"Resposta da API: {e.response.text if hasattr(e, 'response') else 'N/A'}")

if __name__ == '__main__':
    get_layout_fields()