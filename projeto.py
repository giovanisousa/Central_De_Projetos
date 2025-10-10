import requests
import json
import sys

# Adiciona o diretório atual ao path para encontrar os outros módulos
sys.path.append('.')

# Importa as funções necessárias dos módulos existentes
from utils import obter_access_token_zoho, _zp_base, _zp_headers
from config import ZOHO_PORTAL_ID

def get_project_details(project_id):
    """
    Busca os detalhes de um projeto específico no Zoho e imprime o resultado.

    Args:
        project_id (str): O ID do projeto a ser buscado.
    """
    print(f"--- Buscando detalhes do projeto ID: {project_id} ---")
    
    try:
        # 1. Obter o token de acesso
        access_token = obter_access_token_zoho()
        
        # 2. Montar a URL e os headers
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
        headers = _zp_headers(access_token)
        
        # 3. Fazer a requisição para a API
        print(f"Acessando URL: {url}")
        response = requests.get(url, headers=headers, timeout=45)
        
        # Lança um erro para status HTTP 4xx/5xx
        response.raise_for_status()
        
        # 4. Processar e imprimir a resposta
        project_data = response.json()
        
        print("\n--- Resposta Completa da API do Zoho ---")
        # Usa json.dumps para formatar o JSON de forma legível (pretty-print)
        print(json.dumps(project_data, indent=4, ensure_ascii=False))
        print("\n------------------------------------------")

    except requests.exceptions.RequestException as e:
        print(f"\nERRO DE API: Falha ao comunicar com o Zoho. {e}")
        if e.response is not None:
            print(f"Detalhes: {e.response.text}")
    except Exception as e:
        print(f"\nERRO INESPERADO: Ocorreu um erro: {e}")

if __name__ == "__main__":
    # O ID do projeto pode ser passado como argumento na linha de comando
    # Ex: python projeto.py 2376502000005330021
    # Se nenhum argumento for passado, usa o ID de exemplo.
    if len(sys.argv) > 1:
        project_id_to_fetch = sys.argv[1]
    else:
        project_id_to_fetch = "2376502000005544019" # ID de exemplo
        
    get_project_details(project_id_to_fetch)
