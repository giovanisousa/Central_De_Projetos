#!/usr/bin/env python3
"""
Script para verificar e atualizar um projeto específico do Zoho
"""
import os
import sys
import json

# Usar conexão externa do Railway
EXTERNAL_DATABASE_URL = input("Cole a URL EXTERNA do PostgreSQL:\n> ").strip()
os.environ['SQLALCHEMY_DATABASE_URI'] = EXTERNAL_DATABASE_URL
os.environ['DATABASE_URL'] = EXTERNAL_DATABASE_URL

PROJECT_ID = "2376502000002326783"

print(f"\n🔍 Buscando informações do projeto {PROJECT_ID} no Zoho...\n")

try:
    from utils import obter_access_token as obter_access_token_zoho, _zp_headers
    from config import ZOHO_PORTAL_ID
    import requests
    from database import insert_or_update_project, Session
    
    print("� Obtendo access token...")
    access_token = obter_access_token_zoho()
    
    print(f"� Buscando dados do projeto {PROJECT_ID} no Zoho API...")
    headers = _zp_headers(access_token)
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        project_data = data.get('projects', [{}])[0] if 'projects' in data else data
        
        print("\n📋 Dados do projeto no Zoho:")
        print(f"   Nome: {project_data.get('name')}")
        
        status = project_data.get('status', {})
        print(f"\n🏷️  Status:")
        print(f"   ID: {status.get('id')}")
        print(f"   Nome: {status.get('name')}")
        
        tags = project_data.get('tags', [])
        print(f"\n� Tags: ({len(tags)} tags)")
        if tags:
            for tag in tags:
                print(f"   - {tag.get('name')} (ID: {tag.get('id')})")
        else:
            print("   (nenhuma tag)")
        
        # Atualizar no banco
        print(f"\n💾 Atualizando projeto no banco de dados...")
        session = Session()
        try:
            insert_or_update_project(session, project_data)
            session.commit()
            print("✅ Projeto atualizado com sucesso!")
        except Exception as e:
            session.rollback()
            print(f"❌ Erro ao atualizar: {e}")
            import traceback
            traceback.print_exc()
        finally:
            session.close()
        
        print("\n📊 Agora consulte no DBeaver:")
        print(f"   SELECT id, status_id, status_atual, substring(tags, 1, 100) as tags")
        print(f"   FROM projects WHERE id = '{PROJECT_ID}';")
        
    else:
        print(f"\n❌ Erro na API: {response.status_code}")
        print(f"   Resposta: {response.text}")
        
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
