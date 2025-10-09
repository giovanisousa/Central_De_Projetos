from utils import obter_access_token, _zp_headers
import requests
import json

def list_custom_fields():
    try:
        token = obter_access_token()
        headers = _zp_headers(token)
        
        # Tentar obter campos customizados do portal
        portal_url = f'https://projectsapi.zoho.com/api/v3/portal/2376502000000026019/customfields'
        resp = requests.get(portal_url, headers=headers)
        print("\n=== Campos customizados do Portal ===")
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
        
        # Tentar obter campos customizados de um projeto específico
        project_url = f'https://projectsapi.zoho.com/api/v3/portal/2376502000000026019/projects/2376502000005544019'
        resp = requests.get(project_url, headers=headers)
        project_data = resp.json()
        
        print("\n=== Campos customizados do Projeto ===")
        if 'custom_fields' in project_data:
            print(json.dumps(project_data['custom_fields'], indent=2, ensure_ascii=False))
        else:
            print("Campos customizados encontrados no projeto:")
            for key, value in project_data.items():
                if key.startswith(('custom_fields', 'cf_', 'data_')):
                    print(f"{key}: {value}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    list_custom_fields()