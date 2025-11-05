"""
Script para sincronizar os 6 projetos EXTRAS em 'Falta Liberar Servidor Infra'
que não deveriam estar nesta coluna.
"""

import os
import sys
import json
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# IDs dos projetos para testar
# Teste: 1 projeto do Willian + 1 projeto do Giovani
EXTRA_IDS = [
    '2376502000004242191',  # 1150 - Hospital e Clínica Santa Paula (Willian)
    '2376502000005542081',  # 0548 - Med-X (Giovani - correto)
]

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
from database import upsert_project
from config import ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_TOKEN_PATH, ZOHO_PORTAL_ID

def get_refresh_token():
    """Lê o refresh token do arquivo."""
    try:
        with open(ZOHO_TOKEN_PATH, 'r') as f:
            return f.read().strip()
    except:
        raise Exception("Não foi possível ler o refresh token. Verifique o arquivo zoho_refresh_token.txt")

def get_access_token():
    """Obtém um novo access token usando o refresh token."""
    refresh_token = get_refresh_token()
    url = "https://accounts.zoho.com/oauth/v2/token"
    params = {
        "refresh_token": refresh_token,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Erro ao obter access token: {response.text}")

def fetch_project_from_zoho(project_id, access_token):
    """Busca dados de um projeto específico do Zoho."""
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:
        # Token expirou, renova
        print("   Token expirado, renovando...")
        access_token = get_access_token()
        headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
        response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        # API v3 retorna o projeto diretamente
        return data, access_token
    elif response.status_code == 410:
        print(f"   ⚠️ Projeto {project_id} foi excluído no Zoho (HTTP 410)")
        return None, access_token
    else:
        raise Exception(f"Erro ao buscar projeto {project_id}: {response.status_code} - {response.text}")

def main():
    # Conectar ao banco usando URL externa
    db_url = input("Digite a URL do banco PostgreSQL (ex: postgresql://user:pass@host:port/db): ").strip()
    
    # Reconfigurar database para usar URL externa
    database.engine = create_engine(db_url)
    database.Session = sessionmaker(bind=database.engine)
    
    print("\n" + "="*80)
    print("SINCRONIZAÇÃO: 6 Projetos extras em 'Falta Liberar Servidor Infra'")
    print("="*80)
    
    access_token = get_access_token()
    
    sincronizados = 0
    erros = 0
    
    for i, project_id in enumerate(EXTRA_IDS, 1):
        print(f"\n[{i}/{len(EXTRA_IDS)}] Sincronizando projeto {project_id}...")
        
        try:
            project_data, access_token = fetch_project_from_zoho(project_id, access_token)
            
            if project_data is None:
                # Projeto excluído (HTTP 410)
                erros += 1
                continue
            
            # Debug: mostrar informações do proprietário
            print(f"\n   DEBUG - Informações do projeto:")
            print(f"   Owner: {project_data.get('owner_name', 'N/A')} (ID: {project_data.get('owner_id', 'N/A')})")
            print(f"   Owner ZPUID: {project_data.get('owner_zpuid', 'N/A')}")
            if 'owner' in project_data:
                print(f"   Owner object: {project_data.get('owner')}")
            
            # Sincronizar no banco
            upsert_project(project_data)
            
            # Debug: mostrar tags retornadas pela API
            tags_from_api = project_data.get('tags', [])
            print(f"   Tags da API: {tags_from_api}")
            
            # Mostrar info
            nome = project_data.get('name', 'N/A')
            status = project_data.get('status', {})
            status_nome = status.get('name', 'N/A')
            tags = project_data.get('tags', [])
            tags_str = ', '.join([f"{t.get('name')}" for t in tags]) if tags else 'Sem tags'
            
            print(f"   ✅ {nome}")
            print(f"   Status: {status_nome}")
            print(f"   Tags: {tags_str}")
            
            sincronizados += 1
            
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            erros += 1
    
    print("\n" + "="*80)
    print("RESUMO DA SINCRONIZAÇÃO:")
    print("="*80)
    print(f"Total de projetos: {len(EXTRA_IDS)}")
    print(f"Sincronizados: {sincronizados}/{len(EXTRA_IDS)}")
    print(f"Erros: {erros}/{len(EXTRA_IDS)}")
    print("\nSincronização concluída!")

if __name__ == "__main__":
    main()
