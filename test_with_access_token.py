#!/usr/bin/env python3
"""
Teste DIRETO com access token - sem usar refresh token.
"""

import requests
import json
from config import ZOHO_PORTAL_ID

# Access token que você acabou de gerar (válido por 1 hora)
ACCESS_TOKEN = "1000.66ae61d09826399d0c75831f45499fee.96c50de708b5622a76edaf3118722177"

PROJECT_ID = "2376502000004324882"
USER_EMAIL = "camilo.osaida@animati.com.br"  # Email CORRETO do Camilo

def test_add_user_with_token():
    """Testa adicionar usuário usando access token direto."""
    
    print("=" * 80)
    print("TESTE COM ACCESS TOKEN DIRETO")
    print("=" * 80)
    
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}/projectusers"
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "userdetails": [{
            "email_id": USER_EMAIL
        }],
        "notify": False
    }
    
    print(f"\nTentando adicionar: {USER_EMAIL}")
    print(f"Ao projeto: {PROJECT_ID}")
    print("\nPayload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    print(f"\n📤 RESPOSTA:")
    print(f"Status Code: {response.status_code}")
    
    try:
        data = response.json()
        print(f"\nJSON:")
        print(json.dumps(data, indent=2))
        
        if response.ok:
            print("\n" + "=" * 80)
            print("✅ ✅ ✅ SUCESSO! ✅ ✅ ✅")
            print("=" * 80)
            print(f"\n🎉 Usuário {USER_EMAIL} adicionado ao projeto!")
            print("\n✅ O ESCOPO ZohoProjects.users.ALL ESTÁ FUNCIONANDO!")
            print("\n📋 PRÓXIMO PASSO:")
            print("   Você precisa salvar o REFRESH TOKEN (não o access token)")
            print("   para que o sistema possa gerar novos access tokens automaticamente.")
            return True
        else:
            print(f"\n❌ ERRO: {response.status_code}")
            if data.get("error", {}).get("title") == "INVALID_OAUTHSCOPE":
                print("\n⚠️  Token SEM escopo de usuários")
            return False
            
    except Exception as e:
        print(f"\nResponse text: {response.text}")
        print(f"Erro: {e}")
        return False

if __name__ == "__main__":
    test_add_user_with_token()
