import requests
import json
import os
from utils import obter_access_token_zoho, _zp_base, _zp_headers
from config import ZOHO_PORTAL_ID

# --- CONFIGURAÇÃO DA CLASSIFICAÇÃO ---

# Define os nomes dos usuários para cada equipe.
# Usar um set (conjunto) torna a busca mais rápida.
EQUIPE_RIS = {
    "Pablo Pyerri Ferreira da Costa",
    "Lukas Correa",
    "Rodrigo Brasil",
    "Jessika Rodrigues",
    "Rodrigo Viera Chagas",
    "Celio Santos",
    "Fernando Carvalho"
}

EQUIPE_PACS = {
    "Marcello Roza de Souza",
    "Camilo Osaida",
    "Katieli Abreu Rodrigues",
    "Antonio Furtado Luiz Junior",
    "Geraldo Junior",
    "Danilo Sales",
    "Aneidia Sa"
}

# Nome do arquivo de saída classificado
OUTPUT_JSON_FILE = 'equipe_implantacao_classificada.json'
# Nome do time que estamos procurando na API
TARGET_TEAM_NAME = 'Implantação'

# --- FUNÇÕES DE API (sem alteração) ---

def get_all_teams(access_token):
    """Busca todas as equipes no portal do Zoho Projects."""
    try:
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/teams"
        headers = _zp_headers(access_token)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('teams', [])
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao buscar equipes: {e}")
        return []

def get_team_users(access_token, team_id):
    """Busca usuários de um time específico."""
    try:
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/teams/users"
        headers = _zp_headers(access_token)
        params = {'team_ids': json.dumps([team_id])}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('team_users', [])
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao buscar usuários do time: {e}")
        return []

def get_user_details(access_token, user_id):
    """Busca detalhes de um usuário específico pelo seu ZPUID."""
    try:
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/users/{user_id}"
        headers = _zp_headers(access_token)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        if 'users' in user_data and isinstance(user_data['users'], list) and user_data['users']:
            return user_data['users'][0]
        elif 'id' in user_data:
            return user_data
        return {}
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao buscar detalhes do usuário {user_id}: {e}")
        return []

# --- LÓGICA PRINCIPAL ---

def main():
    """Função principal para orquestrar a geração e classificação do JSON."""
    try:
        access_token = obter_access_token_zoho()
        
        # 1. Obter todos os usuários detalhados da equipe 'Implantação'
        print("INFO: Iniciando busca de usuários da equipe de Implantação...")
        all_teams = get_all_teams(access_token)
        target_team_id = next((team['id'] for team in all_teams if team.get('name', '').lower() == TARGET_TEAM_NAME.lower()), None)

        if not target_team_id:
            print(f"ERRO: Equipe '{TARGET_TEAM_NAME}' não encontrada.")
            return

        team_users = get_team_users(access_token, target_team_id)
        if not team_users:
            print("AVISO: Nenhum usuário encontrado na equipe.")
            return

        detailed_users_list = []
        for user_info in team_users:
            zpuid = user_info.get('id')
            if zpuid:
                details = get_user_details(access_token, zpuid)
                if details:
                    detailed_users_list.append({
                        'name': details.get('full_name'),
                        'zuid': details.get('zuid'),
                        'zpuid': zpuid,
                        'email': details.get('email')
                    })
        
        print(f"INFO: Total de {len(detailed_users_list)} usuários detalhados encontrados.")

        # 2. Classificar os usuários nas suas respectivas equipes
        print("INFO: Classificando usuários nas equipes RIS e PACS...")
        classificacao = {
            "Implantação RIS": [],
            "Implantação PACS": [],
            "Não Classificado": []
        }

        for user in detailed_users_list:
            user_name = user.get('name')
            if not user_name:
                continue
            
            if user_name in EQUIPE_RIS:
                classificacao["Implantação RIS"].append(user)
            elif user_name in EQUIPE_PACS:
                classificacao["Implantação PACS"].append(user)
            else:
                classificacao["Não Classificado"].append(user)

        # 3. Salvar o resultado classificado em um novo arquivo JSON
        file_path = os.path.join(os.path.dirname(__file__), OUTPUT_JSON_FILE)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(classificacao, f, indent=4, ensure_ascii=False)
        
        print(f"\nSUCESSO: Arquivo '{OUTPUT_JSON_FILE}' criado.")
        print(f"  - {len(classificacao['Implantação RIS'])} usuários em RIS.")
        print(f"  - {len(classificacao['Implantação PACS'])} usuários em PACS.")
        print(f"  - {len(classificacao['Não Classificado'])} usuários não classificados.")

    except Exception as e:
        print(f"ERRO: Ocorreu um erro inesperado no processo: {e}")

if __name__ == "__main__":
    main()