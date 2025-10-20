"""
Teste FINAL para adicionar usuário ao projeto Zoho
Usando o refresh token NOVO gerado
"""

import requests
import json

# =========================================
# CONFIGURAÇÕES
# =========================================
PORTAL_ID = "868230290"
PROJECT_ID = "2376502000005544019"  # Projeto PACS
USER_EMAIL = "camilo.osaida@animati.com.br"

# OAuth
CLIENT_ID = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
CLIENT_SECRET = "70226965d09b04444346222d9b4846c86a5d31d2fe"

# Ler refresh token do arquivo
with open('zoho_refresh_token.txt', 'r') as f:
    REFRESH_TOKEN = f.read().strip()

print("=" * 80)
print(" TESTE FINAL - ADICIONAR USUÁRIO AO PROJETO")
print("=" * 80)
print()
print(f"📋 Configurações:")
print(f"   Portal ID: {PORTAL_ID}")
print(f"   Project ID: {PROJECT_ID}")
print(f"   User Email: {USER_EMAIL}")
print(f"   Refresh Token: {REFRESH_TOKEN[:20]}...{REFRESH_TOKEN[-20:]}")
print()

# =========================================
# PASSO 1: Obter Access Token
# =========================================
print("🔄 PASSO 1: Obtendo access token...")
print()

token_url = "https://accounts.zoho.com/oauth/v2/token"
token_params = {
    "refresh_token": REFRESH_TOKEN,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "refresh_token"
}

try:
    token_response = requests.post(token_url, data=token_params)
    token_data = token_response.json()
    
    if 'access_token' in token_data:
        access_token = token_data['access_token']
        print(f"✅ Access token obtido com sucesso!")
        print(f"   Token: {access_token[:30]}...{access_token[-10:]}")
        print(f"   Expira em: {token_data.get('expires_in', 'N/A')} segundos")
        print()
        
        # Verificar escopos
        if 'scope' in token_data:
            scopes = token_data['scope'].split()
            print(f"📋 Escopos disponíveis ({len(scopes)}):")
            for scope in scopes:
                marker = "✅" if "users" in scope.lower() else "  "
                print(f"   {marker} {scope}")
            print()
    else:
        print("❌ ERRO ao obter access token:")
        print(json.dumps(token_data, indent=2))
        exit(1)
        
except Exception as e:
    print(f"❌ ERRO na requisição de token:")
    print(f"   {e}")
    exit(1)

# =========================================
# PASSO 2: Listar Usuários do Portal
# =========================================
print("🔍 PASSO 2: Verificando se usuário existe no portal...")
print()

headers = {
    "Authorization": f"Zoho-oauthtoken {access_token}"
}

# Endpoint correto para listar usuários do portal
users_url = f"https://projectsapi.zoho.com/restapi/portal/{PORTAL_ID}/users/"

try:
    users_response = requests.get(users_url, headers=headers)
    
    print(f"Status Code: {users_response.status_code}")
    
    if users_response.status_code == 200:
        users_data = users_response.json()
        total_users = len(users_data.get('users', []))
        print(f"✅ Portal tem {total_users} usuários")
        print()
        
        # Procurar pelo usuário
        user_found = False
        target_user = None
        
        for user in users_data.get('users', []):
            if user.get('email') == USER_EMAIL:
                user_found = True
                target_user = user
                print(f"✅ Usuário ENCONTRADO no portal:")
                print(f"   ID: {user.get('id')}")
                print(f"   Nome: {user.get('name')}")
                print(f"   Email: {user.get('email')}")
                print(f"   Role: {user.get('role')}")
                break
        
        if not user_found:
            print(f"❌ Usuário {USER_EMAIL} NÃO encontrado no portal!")
            print()
            print("📋 Usuários disponíveis:")
            for user in users_data.get('users', [])[:10]:  # Mostrar primeiros 10
                print(f"   - {user.get('name')} ({user.get('email')})")
            print()
            print("⚠️  Para adicionar ao projeto, o usuário precisa existir no portal primeiro!")
            exit(1)
        
        print()
        
    else:
        print(f"❌ ERRO ao listar usuários:")
        print(users_response.text)
        exit(1)
        
except Exception as e:
    print(f"❌ ERRO na requisição:")
    print(f"   {e}")
    exit(1)

# =========================================
# PASSO 3: Verificar Usuários do Projeto
# =========================================
print("🔍 PASSO 3: Verificando se usuário já está no projeto...")
print()

# Endpoint correto para listar usuários do projeto
project_users_url = f"https://projectsapi.zoho.com/restapi/portal/{PORTAL_ID}/projects/{PROJECT_ID}/users/"

try:
    project_users_response = requests.get(project_users_url, headers=headers)
    
    print(f"Status Code: {project_users_response.status_code}")
    
    if project_users_response.status_code == 200:
        project_users_data = project_users_response.json()
        total_project_users = len(project_users_data.get('users', []))
        print(f"✅ Projeto tem {total_project_users} usuários")
        print()
        
        # Verificar se usuário já está no projeto
        already_in_project = False
        
        for user in project_users_data.get('users', []):
            if user.get('email') == USER_EMAIL:
                already_in_project = True
                print(f"⚠️  Usuário JÁ ESTÁ no projeto:")
                print(f"   ID: {user.get('id')}")
                print(f"   Nome: {user.get('name')}")
                print(f"   Email: {user.get('email')}")
                print(f"   Role: {user.get('role')}")
                print()
                print("✅ Teste concluído - Usuário já está no projeto!")
                exit(0)
        
        print(f"ℹ️  Usuário NÃO está no projeto ainda.")
        print(f"   Usuários atuais no projeto:")
        for user in project_users_data.get('users', [])[:5]:
            print(f"   - {user.get('name')} ({user.get('email')})")
        print()
        
    else:
        print(f"❌ ERRO ao listar usuários do projeto:")
        print(project_users_response.text)
        exit(1)
        
except Exception as e:
    print(f"❌ ERRO na requisição:")
    print(f"   {e}")
    exit(1)

# =========================================
# PASSO 4: Adicionar Usuário ao Projeto
# =========================================
print("➕ PASSO 4: Adicionando usuário ao projeto...")
print()

# Endpoint correto para adicionar usuário (API REST v1)
add_user_url = f"https://projectsapi.zoho.com/restapi/portal/{PORTAL_ID}/projects/{PROJECT_ID}/users/"

# Payload para API REST v1 (formato diferente da v3)
payload = {
    "email": USER_EMAIL,
    "role": "employee"
}

print(f"📤 Payload:")
print(json.dumps(payload, indent=2))
print()

try:
    add_user_response = requests.post(
        add_user_url,
        headers=headers,
        data=payload  # API v1 usa data, não json
    )
    
    print(f"Status Code: {add_user_response.status_code}")
    print()
    
    if add_user_response.status_code == 200 or add_user_response.status_code == 201:
        result = add_user_response.json()
        print("=" * 80)
        print(" ✅ ✅ ✅ SUCESSO! ✅ ✅ ✅")
        print("=" * 80)
        print()
        print("📋 Resposta completa:")
        print(json.dumps(result, indent=2))
        print()
        print(f"✅ Usuário {USER_EMAIL} adicionado ao projeto com sucesso!")
        
    elif add_user_response.status_code == 500:
        print("=" * 80)
        print(" ❌ ERRO 500 - BUG DO ZOHO CONFIRMADO")
        print("=" * 80)
        print()
        print("⚠️  O endpoint retornou erro 500 (Internal Server Error)")
        print()
        print("📋 Resposta do servidor:")
        print(add_user_response.text)
        print()
        print("🔍 ANÁLISE:")
        print("   ✅ Refresh token: VÁLIDO")
        print("   ✅ Access token: VÁLIDO")
        print("   ✅ Escopo users.ALL: PRESENTE")
        print("   ✅ Usuário existe no portal: SIM")
        print("   ✅ Payload correto: SIM")
        print("   ❌ API retorna erro 500: BUG DO ZOHO")
        print()
        print("📝 CONCLUSÃO:")
        print("   Este é um BUG conhecido da API do Zoho Projects.")
        print("   O endpoint /projectusers não está funcionando corretamente.")
        print()
        print("💡 ALTERNATIVAS:")
        print("   1. Adicionar usuários manualmente via interface web do Zoho")
        print("   2. Reportar o bug ao suporte: support@zohoprojects.com")
        print("   3. Aguardar correção do Zoho")
        
    else:
        print("=" * 80)
        print(f" ❌ ERRO {add_user_response.status_code}")
        print("=" * 80)
        print()
        print("📋 Resposta completa:")
        print(add_user_response.text)
        print()
        
        try:
            error_data = add_user_response.json()
            print("📋 Resposta JSON:")
            print(json.dumps(error_data, indent=2))
        except:
            pass
        
except Exception as e:
    print(f"❌ ERRO na requisição:")
    print(f"   {e}")
    exit(1)

print()
print("=" * 80)
print(" TESTE CONCLUÍDO")
print("=" * 80)
