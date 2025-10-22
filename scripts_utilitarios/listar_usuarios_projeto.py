"""
Verifica quais usuários estão associados ao projeto
"""

import requests
import json

def listar_usuarios_projeto():
    """Lista todos os usuários do projeto"""
    import utils
    
    access_token = utils.obter_access_token()
    portal_id = "868230290"
    project_id = "2376502000005180127"
    
    # API v3 - Usuários do portal
    url = f"https://projectsapi.zoho.com/api/v3/portal/{portal_id}/users"
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
    }
    
    print("=" * 70)
    print("👥 USUÁRIOS DO PROJETO")
    print("=" * 70)
    print()
    
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        
        if "users" in data:
            print(f"Total de usuários: {len(data['users'])}")
            print()
            
            for user in data['users']:
                print(f"👤 {user.get('name', 'N/A')}")
                print(f"   zpuid: {user.get('zpuid', 'N/A')}")
                print(f"   email: {user.get('email', 'N/A')}")
                print(f"   role: {user.get('role', 'N/A')}")
                print()
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
    
    print("=" * 70)


if __name__ == "__main__":
    listar_usuarios_projeto()
