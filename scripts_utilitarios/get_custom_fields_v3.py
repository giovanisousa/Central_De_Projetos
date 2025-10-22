from utils import obter_access_token, _zp_headers
import requests
import json
from config import ZOHO_PORTAL_ID

def get_custom_fields_v3():
    try:
        token = obter_access_token()
        headers = _zp_headers(token)
        project_id = "2376502000005544019"
        
        # Tentar diferentes endpoints da API v3
        endpoints = [
            f'/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/customfields/',
            f'/portal/{ZOHO_PORTAL_ID}/projects/customfields/',
            f'/portal/{ZOHO_PORTAL_ID}/layouts/2376502000005584766/customfields/'
        ]
        
        base_url = 'https://projectsapi.zoho.com/api/v3'
        
        for endpoint in endpoints:
            try:
                url = base_url + endpoint
                print(f"\nTentando URL: {url}")
                resp = requests.get(url, headers=headers)
                print(f"Status: {resp.status_code}")
                print("Resposta:")
                print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"Erro neste endpoint: {e}")

    except Exception as e:
        print(f"Erro geral: {e}")

if __name__ == '__main__':
    get_custom_fields_v3()