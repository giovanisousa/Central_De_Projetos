#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar sincronização de fases de um projeto específico do Zoho.
"""

import requests
from config import ZOHO_PORTAL_ID
from utils import obter_access_token as obter_access_token_zoho, _zp_base, _zp_headers

# ID do projeto para testar
PROJECT_ID = "2376502000005180127"

def test_sync_fase():
    print("=" * 80)
    print(f"TESTE DE SINCRONIZAÇÃO DE FASES")
    print(f"Projeto ID: {PROJECT_ID}")
    print("=" * 80)
    
    # Obter token de acesso
    print("\n1. Obtendo access token...")
    try:
        access_token = obter_access_token_zoho()
        print(f"   ✓ Token obtido com sucesso: {access_token[:20]}...")
    except Exception as e:
        print(f"   ✗ Erro ao obter token: {e}")
        return
    
    # Construir URL
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{PROJECT_ID}/phases"
    headers = _zp_headers(access_token)
    
    print(f"\n2. Testando endpoint da API...")
    print(f"   URL: {url}")
    print(f"   Headers: {headers}")
    
    # Fazer requisição
    try:
        print(f"\n3. Fazendo requisição GET...")
        response = requests.get(url, headers=headers, timeout=45)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers da Resposta: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   ✓ Requisição bem-sucedida!")
            print(f"\n4. Analisando resposta...")
            print(f"   Chaves na resposta: {list(data.keys())}")
            
            # Verificar se tem milestones
            if 'milestones' in data:
                milestones = data['milestones']
                print(f"   ✓ Encontrados {len(milestones)} milestones/fases")
                
                print(f"\n5. Detalhes das fases:")
                for idx, milestone in enumerate(milestones, 1):
                    print(f"\n   Fase {idx}:")
                    print(f"   - ID: {milestone.get('id')}")
                    print(f"   - Nome: {milestone.get('name')}")
                    print(f"   - Status: {milestone.get('status', {}).get('name', 'N/A')}")
                    print(f"   - Data início: {milestone.get('start_date', 'N/A')}")
                    print(f"   - Data fim: {milestone.get('end_date', 'N/A')}")
            else:
                print(f"   ⚠ Não há chave 'milestones' na resposta")
                print(f"\n   Resposta completa:")
                import json
                print(json.dumps(data, indent=2))
        else:
            print(f"\n   ✗ Erro na requisição!")
            print(f"   Resposta: {response.text}")
            response.raise_for_status()
            
    except requests.exceptions.RequestException as e:
        print(f"\n   ✗ Erro na requisição: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Corpo da resposta de erro: {e.response.text}")
    except Exception as e:
        print(f"\n   ✗ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("FIM DO TESTE")
    print("=" * 80)

if __name__ == "__main__":
    test_sync_fase()
