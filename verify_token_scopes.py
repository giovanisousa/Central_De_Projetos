# -*- coding: utf-8 -*-
"""
Script para verificar os escopos OAuth do token atual do Zoho.
"""
import requests
import utils

def verify_scopes():
    """Verifica os escopos do access token atual."""
    
    print("=" * 80)
    print("VERIFICAÇÃO DE ESCOPOS DO TOKEN ZOHO")
    print("=" * 80)
    
    # Obter access token
    try:
        access_token = utils.obter_access_token()
        print(f"\n✅ Access Token obtido com sucesso!")
        print(f"Token (primeiros 50 chars): {access_token[:50]}...")
    except Exception as e:
        print(f"\n❌ Erro ao obter access token: {e}")
        return
    
    # Verificar escopos
    print(f"\n📋 Verificando escopos do token...")
    
    url = "https://accounts.zoho.com/oauth/v2/token/info"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"\n✅ INFORMAÇÕES DO TOKEN:")
            print(f"\nResposta completa:")
            import json
            print(json.dumps(data, indent=2))
            
            # Extrair escopos se disponível
            if 'scope' in data:
                scopes = data['scope'].split()
                print(f"\n📌 ESCOPOS DISPONÍVEIS ({len(scopes)}):")
                for i, scope in enumerate(scopes, 1):
                    print(f"  {i}. {scope}")
                
                # Verificar escopo de usuários
                user_scopes = [s for s in scopes if 'user' in s.lower()]
                if user_scopes:
                    print(f"\n✅ Escopos relacionados a USUÁRIOS encontrados:")
                    for scope in user_scopes:
                        print(f"  - {scope}")
                else:
                    print(f"\n❌ NENHUM escopo relacionado a USUÁRIOS encontrado!")
                    
        else:
            print(f"\n❌ Erro na requisição:")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Erro ao verificar escopos: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    verify_scopes()
