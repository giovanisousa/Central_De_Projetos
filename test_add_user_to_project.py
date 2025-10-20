#!/usr/bin/env python3
"""
Teste para adicionar usuário ao projeto no Zoho Projects.
Seguindo a documentação oficial da API v3.

Endpoint: POST /api/v3/portal/{PORTALID}/projects/{PROJECTID}/projectusers
"""

import requests
import json
from utils import obter_access_token
from config import ZOHO_PORTAL_ID

# Configurações do teste
PROJECT_ID = "2376502000004324882"  # Projeto de teste
USER_EMAIL = "camilo.rodrigues@animati.com.br"  # Email do Camilo

def test_add_user_to_project():
    """
    Testa adicionar usuário ao projeto seguindo a documentação oficial.
    
    Conforme documentação do Zoho Projects API v3:
    - NÃO usar zpuid no payload
    - Usar apenas email_id (obrigatório)
    - Outros campos são opcionais: profile_id, role_id, rate, etc.
    """
    
    print("=" * 80)
    print("TESTE: Adicionar Usuário ao Projeto")
    print("=" * 80)
    print(f"\nProjeto ID: {PROJECT_ID}")
    print(f"Usuário: {USER_EMAIL}")
    
    # Obter access token
    print("\n[1/4] Obtendo access token...")
    try:
        access_token = obter_access_token()
        print("✅ Access token obtido com sucesso")
    except Exception as e:
        print(f"❌ Erro ao obter access token: {e}")
        return
    
    # Preparar requisição
    print("\n[2/4] Preparando requisição...")
    
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}/projectusers"
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Payload conforme documentação oficial
    # Campos obrigatórios: email_id
    # Campos opcionais: profile_id, role_id, rate, cost_rate_per_hour, etc.
    payload = {
        "userdetails": [{
            "email_id": USER_EMAIL,
            # "profile_id": "",  # Opcional - ID do perfil de acesso
            # "role_id": "",     # Opcional - ID do papel no projeto
            # "rate": "",        # Opcional - Taxa de cobrança por hora
            # "cost_rate_per_hour": "",  # Opcional - Custo por hora
            # "revenue_budget": "",      # Opcional - Orçamento de receita
            # "cost_budget": "",         # Opcional - Orçamento de custo
            # "budget_threshold": "",    # Opcional - Limite de orçamento
            # "is_readonly": false,      # Opcional - Acesso somente leitura
        }],
        "notify": False  # Não enviar notificação por email
    }
    
    print(f"\n📍 URL: {url}")
    print(f"\n📋 Headers:")
    print(json.dumps({k: v for k, v in headers.items() if k != 'Authorization'}, indent=2))
    print(f"   Authorization: Zoho-oauthtoken {access_token[:20]}...")
    print(f"\n📦 Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    # Enviar requisição
    print("\n[3/4] Enviando requisição para API do Zoho...")
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"\n[4/4] Resposta recebida")
        print(f"\n📊 Status Code: {response.status_code}")
        
        # Tentar parsear JSON
        try:
            response_data = response.json()
            print(f"\n📄 Resposta JSON:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(f"\n📄 Resposta (texto):")
            print(response.text[:1000])
        
        # Analisar resultado
        print("\n" + "=" * 80)
        print("RESULTADO")
        print("=" * 80)
        
        if response.status_code in (200, 201):
            print("✅ SUCESSO: Usuário adicionado ao projeto!")
            if 'response_data' in locals() and 'users' in response_data:
                print(f"\nUsuários no projeto: {len(response_data.get('users', []))}")
        elif response.status_code == 400:
            print("❌ ERRO 400: Bad Request")
            print("   Possíveis causas:")
            print("   - Email inválido ou formato incorreto")
            print("   - Campos obrigatórios faltando")
            print("   - Payload com formato incorreto")
        elif response.status_code == 403:
            print("❌ ERRO 403: Forbidden")
            print("   Possíveis causas:")
            print("   - Permissões insuficientes no token")
            print("   - Usuário não tem permissão para adicionar membros")
        elif response.status_code == 404:
            print("❌ ERRO 404: Not Found")
            print("   Possíveis causas:")
            print("   - Projeto ID inválido ou não existe")
            print("   - Portal ID incorreto")
        elif response.status_code == 500:
            print("❌ ERRO 500: Internal Server Error")
            print("   Possíveis causas:")
            print("   - Problema no servidor do Zoho")
            print("   - Usuário já existe no projeto (bug do Zoho)")
            print("   - Email não está cadastrado no portal")
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erro na requisição: {e}")
        return
    
    print("\n" + "=" * 80)


def check_user_in_project():
    """
    Verifica se o usuário já está no projeto antes de tentar adicionar.
    """
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO: Usuário já está no projeto?")
    print("=" * 80)
    
    try:
        access_token = obter_access_token()
        
        url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}/projectusers"
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Accept": "application/json"
        }
        
        print(f"\n📍 GET {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('users', [])
            
            print(f"\n✅ Projeto tem {len(users)} usuário(s)")
            print("\nUsuários no projeto:")
            
            user_found = False
            for user in users:
                email = user.get('email', 'N/A')
                name = user.get('name', 'N/A')
                zpuid = user.get('zpuid', 'N/A')
                
                is_target = email.lower() == USER_EMAIL.lower()
                marker = "👉 " if is_target else "   "
                
                print(f"{marker}{name} ({email}) - ZPUID: {zpuid}")
                
                if is_target:
                    user_found = True
            
            if user_found:
                print(f"\n⚠️  Usuário {USER_EMAIL} JÁ ESTÁ no projeto!")
                print("   Adicionar novamente pode causar erro 500")
            else:
                print(f"\n✅ Usuário {USER_EMAIL} NÃO está no projeto")
                print("   É seguro adicionar")
                
        else:
            print(f"❌ Erro ao buscar usuários: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    # Primeiro, verificar se usuário já está no projeto
    check_user_in_project()
    
    # Perguntar se deseja continuar
    print("\n")
    continuar = input("Deseja continuar e tentar adicionar o usuário? (s/n): ").strip().lower()
    
    if continuar == 's':
        test_add_user_to_project()
    else:
        print("\n❌ Teste cancelado pelo usuário")
