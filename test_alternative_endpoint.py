#!/usr/bin/env python3
"""
Teste com endpoint alternativo para adicionar usuários.
"""

import requests
import json
from config import ZOHO_PORTAL_ID

# Access token válido
ACCESS_TOKEN = "1000.66ae61d09826399d0c75831f45499fee.96c50de708b5622a76edaf3118722177"

PROJECT_ID = "2376502000004324882"
USER_EMAIL = "camilo.rodrigues@animati.com.br"

def test_list_portal_users():
    """Lista usuários disponíveis no portal."""
    
    print("=" * 80)
    print("TESTE 1: Listar Usuários do Portal")
    print("=" * 80)
    
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/users"
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {ACCESS_TOKEN}"
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    
    print(f"Status: {response.status_code}")
    
    if response.ok:
        data = response.json()
        users = data.get("users", [])
        print(f"\n✅ Total de usuários no portal: {len(users)}")
        
        # Procurar Camilo
        camilo = None
        for user in users:
            if user.get("email") == USER_EMAIL:
                camilo = user
                break
        
        if camilo:
            print(f"\n✅ {USER_EMAIL} encontrado!")
            print(f"   Nome: {camilo.get('name')}")
            print(f"   ID: {camilo.get('id')}")
            print(f"   ZPUID: {camilo.get('zpuid')}")
            return camilo.get("id")
        else:
            print(f"\n❌ {USER_EMAIL} NÃO encontrado no portal")
            print("\n📋 Primeiros 5 usuários:")
            for u in users[:5]:
                print(f"   - {u.get('email')} (ID: {u.get('id')})")
            return None
    else:
        print(f"❌ Erro: {response.text}")
        return None

def test_add_user_alternative(user_id):
    """Tenta adicionar usuário com endpoint alternativo."""
    
    print("\n" + "=" * 80)
    print("TESTE 2: Adicionar Usuário (Método Alternativo)")
    print("=" * 80)
    
    # Tentar com /users em vez de /projectusers
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}/users"
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Payload alternativo com user_id
    payload = {
        "users": [{
            "id": user_id
        }]
    }
    
    print(f"\nURL: {url}")
    print(f"Payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    print(f"\n📤 RESPOSTA:")
    print(f"Status Code: {response.status_code}")
    
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
        
        if response.ok:
            print("\n✅ SUCESSO!")
            return True
        else:
            print(f"\n❌ Erro: {response.status_code}")
            return False
    except:
        print(response.text)
        return False

if __name__ == "__main__":
    # Passo 1: Encontrar o user_id
    user_id = test_list_portal_users()
    
    if user_id:
        # Passo 2: Tentar adicionar ao projeto
        test_add_user_alternative(user_id)
    else:
        print("\n⚠️  Não é possível adicionar usuário que não está no portal")
        print("   O usuário precisa primeiro ser adicionado ao portal Zoho")
