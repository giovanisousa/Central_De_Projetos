import requests

# Ler o refresh token
with open('zoho_refresh_token.txt', 'r') as f:
    refresh_token = f.read().strip()

# Credenciais do Zoho
client_id = '1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR'
client_secret = '70226965d09b04444346222d9b4846c86a5d31d2fe'

# Fazer requisição para gerar novo access token
response = requests.post(
    'https://accounts.zoho.com/oauth/v2/token',
    data={
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token'
    }
)

# Mostrar resultado
print('=' * 80)
print('ZOHO ACCESS TOKEN GERADO')
print('=' * 80)

result = response.json()

if 'access_token' in result:
    print(f"\n✅ ACCESS TOKEN GERADO COM SUCESSO!\n")
    print(f"Access Token: {result['access_token']}")
    print(f"\nExpira em: {result.get('expires_in', 'N/A')} segundos ({result.get('expires_in', 0) // 60} minutos)")
    print(f"Token Type: {result.get('token_type', 'Bearer')}")
    print(f"API Domain: {result.get('api_domain', 'https://www.zohoapis.com')}")
else:
    print(f"\n❌ ERRO AO GERAR TOKEN!")
    print(f"Resposta: {result}")

print('\n' + '=' * 80)
print('COPIE O ACCESS TOKEN ACIMA')
print('=' * 80)
