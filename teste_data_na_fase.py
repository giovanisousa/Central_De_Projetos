# -*- coding: utf-8 -*-
"""
Script standalone para investigar os eventos (edits) de um projeto no Zoho Projects
- Lê credenciais do Zoho via variáveis no topo ou via input
- Obtém access_token via refresh_token
- Busca edits do projeto e imprime todos os eventos completos (JSON pretty) para análise

Uso:
    python teste_data_na_fase.py

Ajuste os valores abaixo conforme necessário.
"""
import os
import json
import time
import requests

# ========= CONFIGURAR AQUI =========
# Se sua conta for .com.br, troque para 'com.br'
ZOHO_DOMAIN = os.environ.get('ZOHO_DOMAIN', 'com')  # 'com' ou 'com.br'

# Preencha abaixo OU use variáveis de ambiente com os mesmos nomes
ZOHO_CLIENT_ID = os.environ.get('ZOHO_CLIENT_ID', '1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR')
ZOHO_CLIENT_SECRET = os.environ.get('ZOHO_CLIENT_SECRET', '70226965d09b04444346222d9b4846c86a5d31d2fe')
ZOHO_PORTAL_ID = os.environ.get('ZOHO_PORTAL_ID', '868230290')
# Lê refresh_token do arquivo do projeto por padrão
DEFAULT_TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'zoho_refresh_token.txt')
ZOHO_REFRESH_TOKEN = os.environ.get('ZOHO_REFRESH_TOKEN', '') or (open(DEFAULT_TOKEN_PATH, 'r').read().strip() if os.path.exists(DEFAULT_TOKEN_PATH) else '')

# Projeto alvo para inspeção
PROJECT_ID = os.environ.get('ZOHO_PROJECT_ID', '2376502000000213310')

# ========= FUNÇÕES =========

def zoho_token_url():
    return f"https://accounts.zoho.{ZOHO_DOMAIN}/oauth/v2/token"

def zoho_projects_base():
    return f"https://projectsapi.zoho.{ZOHO_DOMAIN}/api/v3"


def obter_access_token():
    if not ZOHO_REFRESH_TOKEN:
        print('ERRO: refresh_token não definido. Configure ZOHO_REFRESH_TOKEN ou zoho_refresh_token.txt')
        return None
    url = zoho_token_url()
    payload = {
        'refresh_token': ZOHO_REFRESH_TOKEN,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'grant_type': 'refresh_token'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=20)
        try:
            r.raise_for_status()
        except requests.exceptions.RequestException:
            body = None
            try:
                body = r.json()
            except Exception:
                body = r.text
            print(f"ERRO token: status={r.status_code} body={body}")
            return None
        data = r.json()
        token = data.get('access_token')
        print(f"OK token obtido. expires_in={data.get('expires_in')} scope={data.get('scope')}")
        return token
    except Exception as e:
        print(f"ERRO inesperado ao obter token: {e}")
        return None


def listar_edits_projeto(access_token, project_id, index=1, rng=50):
    url = f"{zoho_projects_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/edits"
    headers = {'Authorization': f"Bearer {access_token}"}
    params = {'index': index, 'range': rng}
    r = requests.get(url, headers=headers, params=params, timeout=30)
    try:
        r.raise_for_status()
    except requests.exceptions.RequestException:
        body = None
        try:
            body = r.json()
        except Exception:
            body = r.text
        print(f"ERRO edits: status={r.status_code} body={body}")
        return None
    try:
        return r.json()
    except Exception:
        print('ERRO: resposta de edits não é JSON válido')
        return None


def imprimir_eventos_completos(data):
    print('\n===== RESPOSTA COMPLETA DO ENDPOINT /edits =====')
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print('===== FIM =====\n')

    # Tenta localizar listas comuns de atividades/edits
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for k in ['edits', 'data', 'activities', 'logs', 'history', 'items']:
            if isinstance(data.get(k), list):
                items = data[k]
                break
        if not items and isinstance(data.get('project'), dict):
            proj = data['project']
            for k in ['edits', 'data', 'activities', 'logs', 'history', 'items']:
                if isinstance(proj.get(k), list):
                    items = proj[k]
                    break
    print(f"Itens identificados: {len(items)}")

    # Tenta evidenciar campos de data e de mudança de status/tags
    for i, item in enumerate(items):
        texto = json.dumps(item, ensure_ascii=False)
        data_candidata = None
        for key in ['updated_time','modified_time','modified_at','time','date','created_time','log_time','timestamp']:
            if isinstance(item, dict) and key in item:
                data_candidata = item[key]
                break
        print(f"\n-- ITEM #{i+1} --")
        print(texto)
        print(f"Possível campo de data: {data_candidata}")


def main():
    print('Configuração:')
    print(f"  ZOHO_DOMAIN     = {ZOHO_DOMAIN}")
    print(f"  ZOHO_PORTAL_ID  = {ZOHO_PORTAL_ID}")
    print(f"  PROJECT_ID      = {PROJECT_ID}")
    print(f"  Tem refresh?    = {'sim' if bool(ZOHO_REFRESH_TOKEN) else 'não'}")

    token = obter_access_token()
    if not token:
        print('Falha ao obter access_token. Verifique domínio (.com vs .com.br), client_id/secret e refresh_token.')
        return

    data = listar_edits_projeto(token, PROJECT_ID, index=1, rng=50)
    if data is None:
        print('Falha ao obter edits.')
        return

    imprimir_eventos_completos(data)


if __name__ == '__main__':
    main()