#!/usr/bin/env python3
"""
Teste detalhado para adicionar usuário ao projeto no Zoho Projects.
Inclui verificação de permissões e tentativas com diferentes endpoints.
"""

import requests
import json
from utils import obter_access_token
from config import ZOHO_PORTAL_ID

# Configurações do teste
PROJECT_ID = "2376502000004324882"  # Projeto de teste
USER_EMAIL = "camilo.rodrigues@animati.com.br"  # Email do Camilo

def test_permissions():
    """Testa se temos permissão para acessar informações do projeto."""
    
    print("=" * 80)
    print("TESTE 1: Verificar Permissões de Acesso ao Projeto")
    print("=" * 80)
    
    try:
        access_token = obter_access_token()
        print("✅ Access token obtido")
    except Exception as e:
        print(f"❌ Erro ao obter access token: {e}")
        return False
    
    # Testar GET project details
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Accept": "application/json"
    }
    
    print(f"\n📋 Testando GET {url}")
    response = requests.get(url, headers=headers, timeout=30)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.ok:
        print("✅ Temos permissão para acessar detalhes do projeto")
        data = response.json()
        project_name = data.get("projects", [{}])[0].get("name", "N/A")
        print(f"Nome do Projeto: {project_name}")
        return True
    else:
        print(f"❌ Sem permissão para acessar projeto")
        print(f"Response: {response.text[:500]}")
        return False

def test_list_users():
    """Testa se conseguimos listar usuários do projeto."""
    
    print("\n" + "=" * 80)
    print("TESTE 2: Listar Usuários do Projeto")
    print("=" * 80)
    
    try:
        access_token = obter_access_token()
    except Exception as e:
        print(f"❌ Erro ao obter access token: {e}")
        return
    
    # Testar GET project users
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}/users"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Accept": "application/json"
    }
    
    print(f"\n📋 Testando GET {url}")
    response = requests.get(url, headers=headers, timeout=30)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.ok:
        print("✅ Conseguimos listar usuários do projeto")
        try:
            data = response.json()
            users = data.get("users", [])
            print(f"\n👥 Total de usuários: {len(users)}")
            
            for user in users[:5]:  # Mostrar apenas os primeiros 5
                print(f"  - {user.get('name')} ({user.get('email')})")
            
            # Verificar se Camilo já está no projeto
            camilo_exists = any(u.get('email') == USER_EMAIL for u in users)
            if camilo_exists:
                print(f"\n⚠️  {USER_EMAIL} JÁ ESTÁ NO PROJETO!")
                return True
            else:
                print(f"\n✅ {USER_EMAIL} NÃO está no projeto (pode adicionar)")
                return False
        except Exception as e:
            print(f"⚠️  Erro ao processar resposta: {e}")
    else:
        print(f"❌ Não conseguimos listar usuários")
        print(f"Response: {response.text[:500]}")

def test_add_user_v3():
    """Testa adicionar usuário usando API v3."""
    
    print("\n" + "=" * 80)
    print("TESTE 3: Adicionar Usuário (API v3)")
    print("=" * 80)
    
    try:
        access_token = obter_access_token()
    except Exception as e:
        print(f"❌ Erro ao obter access token: {e}")
        return
    
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}/projectusers"
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "userdetails": [{
            "email_id": USER_EMAIL
        }],
        "notify": False
    }
    
    print(f"\n📋 POST {url}")
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    print(f"\n📤 Resposta:")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    try:
        data = response.json()
        print(f"\nJSON Response:")
        print(json.dumps(data, indent=2))
        
        if response.ok:
            print("\n✅ SUCESSO! Usuário adicionado ao projeto!")
        else:
            print(f"\n❌ ERRO: {response.status_code}")
            
            # Análise detalhada do erro
            if response.status_code == 401:
                error_title = data.get("error", {}).get("title", "")
                if "INVALID_OAUTHSCOPE" in error_title:
                    print("\n⚠️  DIAGNÓSTICO:")
                    print("    Embora você afirme que o escopo ZohoProjects.users.all existe,")
                    print("    o Zoho está rejeitando a requisição por falta de escopo OAuth.")
                    print("\n    Possíveis causas:")
                    print("    1. O refresh token foi gerado SEM o escopo ZohoProjects.users.all")
                    print("    2. O escopo correto é diferente (ex: ZohoProjects.projectusers.ALL)")
                    print("    3. É necessário escopo de portal (ZohoProjects.portals.ALL)")
                    print("\n    Solução: Verificar documentação oficial de escopos do Zoho")
                    
    except Exception as e:
        print(f"Response Text: {response.text[:1000]}")
        print(f"\n⚠️  Erro ao processar resposta: {e}")

def main():
    """Executa todos os testes."""
    
    # Teste 1: Permissões básicas
    has_permission = test_permissions()
    if not has_permission:
        print("\n⚠️  Sem permissão básica ao projeto. Abortando testes.")
        return
    
    # Teste 2: Listar usuários
    user_exists = test_list_users()
    
    # Teste 3: Adicionar usuário (apenas se não existir)
    if user_exists:
        print("\n⚠️  Usuário já existe. Pulando teste de adição.")
    else:
        test_add_user_v3()
    
    print("\n" + "=" * 80)
    print("TESTES CONCLUÍDOS")
    print("=" * 80)

if __name__ == "__main__":
    main()
