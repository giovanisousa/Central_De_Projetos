"""
Script de teste DIRETO para atualizar campos de implantadores no Zoho Projects.
Testa AMBOS os formatos de nome de campo simultaneamente.
Usa tokens diretamente sem dependências complexas.
"""

import requests
import json
import os
from pathlib import Path

# ==== CONFIGURAÇÃO DO TESTE ====
PROJECT_ID = "2376502000005180127"  # Projeto: 1177 - Clinica Leonardo da Vinci
IMPLANTADOR_RIS = "Fernando Carvalho"
IMPLANTADOR_PACS = "Danilo Sales"

print("=" * 80)
print("TESTE: Atualizar Campos de Implantadores no Zoho Projects")
print("=" * 80)
print(f"Project ID: {PROJECT_ID}")
print(f"Implantador RIS: {IMPLANTADOR_RIS}")
print(f"Implantador PACS: {IMPLANTADOR_PACS}")
print("=" * 80)

# ==== 1. OBTER ACCESS TOKEN E PORTAL ID ====
print("\n[1/5] Lendo credenciais de config.py...")

try:
    from config import ZOHO_PORTAL_ID
    print(f"✅ ZOHO_PORTAL_ID: {ZOHO_PORTAL_ID}")
except ImportError as e:
    print(f"❌ ERRO ao importar config.py: {e}")
    exit(1)

# Obter access token usando o refresh token (mesma abordagem do gerar_zoho_token.py)
print("\n[2/5] Obtendo access token...")

try:
    # Ler o refresh token
    with open('zoho_refresh_token.txt', 'r') as f:
        refresh_token = f.read().strip()
    
    # Credenciais do Zoho
    client_id = '1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR'
    client_secret = '70226965d09b04444346222d9b4846c86a5d31d2fe'
    
    # Fazer requisição para gerar novo access token
    token_response = requests.post(
        'https://accounts.zoho.com/oauth/v2/token',
        data={
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token'
        },
        timeout=10
    )
    
    if token_response.status_code == 200:
        token_data = token_response.json()
        if 'access_token' in token_data:
            access_token = token_data['access_token']
            print(f"✅ Access token obtido: {access_token[:20]}...")
        else:
            print(f"❌ ERRO: 'access_token' não encontrado na resposta")
            print(f"Resposta: {token_data}")
            exit(1)
    else:
        print(f"❌ ERRO ao obter token: HTTP {token_response.status_code}")
        print(token_response.text)
        exit(1)
        
except FileNotFoundError:
    print("❌ ERRO: Arquivo zoho_refresh_token.txt não encontrado")
    exit(1)
except Exception as e:
    print(f"❌ ERRO ao obter access token: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

# ==== 3. MONTAR PAYLOAD COM AMBOS OS FORMATOS ====
print("\n[3/5] Montando payload com AMBOS os formatos de nome...")

custom_fields_implantadores = {}

# Adicionar Implantador RIS - AMBOS OS FORMATOS
if IMPLANTADOR_RIS:
    custom_fields_implantadores["Implantador RIS"] = IMPLANTADOR_RIS  # Formato com espaços
    custom_fields_implantadores["implantador_ris"] = IMPLANTADOR_RIS  # Formato snake_case

# Adicionar Implantador PACS - AMBOS OS FORMATOS
if IMPLANTADOR_PACS:
    custom_fields_implantadores["Implantador PACS"] = IMPLANTADOR_PACS  # Formato com espaços
    custom_fields_implantadores["implantador_pacs"] = IMPLANTADOR_PACS  # Formato snake_case

# Montar payload final
payload = {
    "custom_fields": custom_fields_implantadores
}

# Adicionar também no root level (padrão que funciona com outros campos)
payload.update(custom_fields_implantadores)

print("✅ Payload montado:")
print(json.dumps(payload, indent=2, ensure_ascii=False))

# ==== 4. ENVIAR PATCH REQUEST ====
print("\n[4/5] Enviando PATCH request para Zoho API v3...")

url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}"
headers = {
    "Authorization": f"Zoho-oauthtoken {access_token}",
    "Content-Type": "application/json"
}

print(f"URL: {url}")
print(f"Headers: Authorization: Zoho-oauthtoken {access_token[:20]}...")

try:
    response = requests.patch(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"\n✅ Resposta recebida:")
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code in (200, 201):
        print(f"✅ API retornou sucesso (HTTP {response.status_code})")
        
        try:
            response_data = response.json()
            print("\n📄 Resposta JSON (primeiros 2000 caracteres):")
            print(json.dumps(response_data, indent=2, ensure_ascii=False)[:2000])
            
            # Verificar se os campos estão na resposta
            print("\n🔍 Verificando campos na resposta:")
            
            campos_encontrados = []
            
            # Verificar todos os formatos no root level
            for campo_nome in ["implantador_ris", "Implantador RIS", "implantador_pacs", "Implantador PACS"]:
                if campo_nome in response_data:
                    valor = response_data[campo_nome]
                    print(f"   ✅ '{campo_nome}' (root): '{valor}'")
                    campos_encontrados.append(campo_nome)
                else:
                    print(f"   ❌ '{campo_nome}' (root): NÃO ENCONTRADO")
            
            # Verificar em custom_fields
            if "custom_fields" in response_data:
                custom_fields = response_data["custom_fields"]
                if isinstance(custom_fields, dict):
                    print(f"\n   📋 custom_fields encontrado com {len(custom_fields)} campos")
                    for key, value in custom_fields.items():
                        if "implantador" in key.lower():
                            print(f"      ✅ '{key}': '{value}'")
                            campos_encontrados.append(f"{key} (custom_fields)")
            
            print(f"\n✅ Total de campos encontrados: {len(campos_encontrados)}")
            
        except json.JSONDecodeError:
            print("⚠️  Resposta não é JSON válido")
            print("Conteúdo da resposta:")
            print(response.text[:1000])
    else:
        print(f"❌ API retornou erro (HTTP {response.status_code})")
        print(f"\nConteúdo da resposta:")
        print(response.text[:1000])
        
except requests.exceptions.Timeout:
    print("❌ ERRO: Timeout ao fazer request (>30s)")
    exit(1)
except requests.exceptions.RequestException as e:
    print(f"❌ ERRO na request: {str(e)}")
    exit(1)
except Exception as e:
    print(f"❌ ERRO inesperado: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

# ==== 5. VERIFICAR SE PERSISTIU (FAZER GET) ====
print("\n" + "=" * 80)
print("VERIFICAÇÃO FINAL: Consultando projeto novamente (GET)")
print("=" * 80)

try:
    url_get = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}"
    response_get = requests.get(url_get, headers=headers, timeout=30)
    
    if response_get.status_code == 200:
        project_data = response_get.json()
        
        print("\n🔍 Verificando se os campos PERSISTIRAM:")
        
        testes_persistencia = [
            ("implantador_ris", IMPLANTADOR_RIS),
            ("Implantador RIS", IMPLANTADOR_RIS),
            ("implantador_pacs", IMPLANTADOR_PACS),
            ("Implantador PACS", IMPLANTADOR_PACS)
        ]
        
        campos_persistidos = []
        campos_nao_persistidos = []
        
        for campo_nome, valor_esperado in testes_persistencia:
            valor_atual = project_data.get(campo_nome)
            
            if valor_atual:
                if valor_atual == valor_esperado:
                    print(f"   ✅ '{campo_nome}' PERSISTIU corretamente: '{valor_atual}'")
                    campos_persistidos.append(campo_nome)
                else:
                    print(f"   ⚠️  '{campo_nome}' tem valor diferente: '{valor_atual}' (esperado: '{valor_esperado}')")
            else:
                print(f"   ❌ '{campo_nome}' NÃO PERSISTIU (vazio ou ausente)")
                campos_nao_persistidos.append(campo_nome)
        
        print("\n" + "=" * 80)
        print("RESUMO FINAL:")
        print("=" * 80)
        print(f"✅ Campos que PERSISTIRAM: {len(campos_persistidos)}")
        for campo in campos_persistidos:
            print(f"   - {campo}")
        
        if campos_nao_persistidos:
            print(f"\n❌ Campos que NÃO PERSISTIRAM: {len(campos_nao_persistidos)}")
            for campo in campos_nao_persistidos:
                print(f"   - {campo}")
        
        if len(campos_persistidos) > 0:
            print("\n🎉 SUCESSO! Pelo menos um formato funcionou!")
        else:
            print("\n❌ FALHA! Nenhum formato persistiu os dados.")
            print("   Os campos podem ser READ-ONLY via API.")
        
    else:
        print(f"❌ Falha ao consultar projeto: HTTP {response_get.status_code}")
        print(response_get.text[:500])
        
except Exception as e:
    print(f"❌ Erro ao verificar persistência: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("FIM DO TESTE")
print("=" * 80)
