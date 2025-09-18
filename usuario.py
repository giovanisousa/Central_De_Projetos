
import requests
import json
from utils import obter_access_token_zoho, _zp_base, _zp_headers
from config import ZOHO_PORTAL_ID

def get_team_users(team_ids: list):
    """
    Busca usuários de um ou mais times no Zoho Projects.

    Args:
        team_ids: Uma lista de IDs de times.

    Returns:
        Um dicionário com a resposta da API.
    """
    try:
        # Obter o token de acesso atualizado
        access_token = obter_access_token_zoho()

        # Construir a URL da API
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/teams/users"

        # Preparar os cabeçalhos da requisição
        headers = _zp_headers(access_token)

        # Preparar os parâmetros da query
        # A API espera um JSONArray, então convertemos a lista para uma string JSON
        params = {
            'team_ids': json.dumps(team_ids)
        }

        print(f"INFO: Requisitando usuários para os times: {team_ids}")
        print(f"URL: {url}")
        print(f"Params: {params}")

        # Fazer a requisição GET
        response = requests.get(url, headers=headers, params=params)
        
        # Lançar uma exceção para respostas com erro (status code 4xx ou 5xx)
        response.raise_for_status()

        print("INFO: Requisição bem-sucedida!")
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha na requisição à API do Zoho: {e}")
        if e.response is not None:
            print(f"Response Body: {e.response.text}")
        return None
    except Exception as e:
        print(f"ERRO: Ocorreu um erro inesperado: {e}")
        return None

if __name__ == "__main__":
    # ID do time fornecido por você
    target_team_id = "2376502000000106177"
    
    # A função espera uma lista de IDs
    users_data = get_team_users([target_team_id])
    
    if users_data:
        print("\n--- DADOS DOS USUÁRIOS DO TIME ---")
        # Imprime o resultado de forma legível
        print(json.dumps(users_data, indent=4, ensure_ascii=False))
        
        # Exemplo de como acessar os nomes dos usuários
        if 'users' in users_data:
            print("\n--- NOMES DOS USUÁRIOS ---")
            for user in users_data['users']:
                print(f"- {user.get('name')}")
    else:
        print("\nNão foi possível obter os dados dos usuários.")
