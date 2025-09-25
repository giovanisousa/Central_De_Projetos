# -*- coding: utf-8 -*-
"""
Inspeciona um projeto existente que tem campos de múltipla seleção preenchidos
para descobrir o formato exato que o Zoho espera
"""
import json
import requests
from config import ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_PORTAL_ID, ZOHO_TOKEN_PATH

def obter_access_token():
    with open(ZOHO_TOKEN_PATH, 'r', encoding='utf-8') as f:
        refresh_token = f.read().strip()
    
    url = f"https://accounts.zoho.com/oauth/v2/token"
    payload = {
        "refresh_token": refresh_token,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(url, data=payload, headers=headers, timeout=25)
    r.raise_for_status()
    return r.json().get("access_token")

def inspecionar_projeto_de_referencia():
    """
    Analisa o projeto que você mostrou na primeira resposta (ID: 2376502000005609027)
    para ver exatamente como os campos de múltipla seleção estão estruturados
    """
    token = obter_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Accept": "application/json",
    }
    
    # ID do projeto de referência que tem os campos preenchidos
    project_id_referencia = "2376502000005609027"
    
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id_referencia}"
    
    print(f"🔍 Inspecionando projeto de referência: {project_id_referencia}")
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            projeto = resp.json()
            
            print("✅ Projeto encontrado!")
            print(f"Nome: {projeto.get('name')}")
            
            # Analisar campos de múltipla seleção
            print("\n📥 CAMPO IMPORTAÇÕES:")
            importacoes = projeto.get('importacoes', [])
            if importacoes:
                print(f"Tipo: {type(importacoes)}")
                print(f"Quantidade: {len(importacoes)}")
                print("Estrutura completa:")
                for i, item in enumerate(importacoes):
                    print(f"  [{i}] {json.dumps(item, indent=4, ensure_ascii=False)}")
                
                # Extrair apenas os IDs para ver o formato
                ids_importacoes = [item.get('id') for item in importacoes]
                print(f"Lista de IDs: {ids_importacoes}")
            else:
                print("Vazio ou não encontrado")
            
            print("\n🔗 CAMPO INTEGRAÇÕES:")
            integracoes = projeto.get('integracoes', [])
            if integracoes:
                print(f"Tipo: {type(integracoes)}")
                print(f"Quantidade: {len(integracoes)}")
                print("Estrutura completa:")
                for i, item in enumerate(integracoes):
                    print(f"  [{i}] {json.dumps(item, indent=4, ensure_ascii=False)}")
                
                # Extrair apenas os IDs para ver o formato
                ids_integracoes = [item.get('id') for item in integracoes]
                print(f"Lista de IDs: {ids_integracoes}")
            else:
                print("Vazio ou não encontrado")
            
            # Analisar outros campos customizados
            print("\n📋 OUTROS CAMPOS CUSTOMIZADOS:")
            campos_interesse = [
                'solucoes_contratadas', 'havera_integracao', 'havera_importacao',
                'projects_cf_0001', 'link_do_google'
            ]
            
            for campo in campos_interesse:
                valor = projeto.get(campo)
                if valor is not None:
                    print(f"  {campo}: {valor} (tipo: {type(valor)})")
            
            # JSON completo para análise
            print(f"\n📄 JSON COMPLETO (primeiros 2000 chars):")
            json_str = json.dumps(projeto, indent=2, ensure_ascii=False)
            print(json_str[:2000])
            
            return projeto
            
        else:
            print(f"❌ Erro ao buscar projeto: {resp.status_code}")
            print(resp.text)
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def testar_formato_descoberto(project_id_teste, projeto_referencia):
    """
    Testa enviar campos usando o formato exato descoberto no projeto de referência
    """
    if not projeto_referencia:
        print("❌ Sem projeto de referência para copiar formato")
        return
    
    token = obter_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    # Extrair formato exato das importações do projeto de referência
    importacoes_ref = projeto_referencia.get('importacoes', [])
    integracoes_ref = projeto_referencia.get('integracoes', [])
    
    print(f"\n🧪 TESTANDO FORMATO DESCOBERTO no projeto {project_id_teste}")
    
    # Tentar usar o formato exato do projeto de referência
    if importacoes_ref:
        # Pegar alguns IDs do projeto de referência para teste
        ids_para_teste = [item.get('id') for item in importacoes_ref[:3]]  # Primeiros 3
        
        print(f"\n📥 Testando importações com IDs: {ids_para_teste}")
        
        # Teste 1: Apenas lista de IDs (string)
        payload_test1 = {"importacoes": ids_para_teste}
        
        patch_url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id_teste}"
        resp1 = requests.patch(patch_url, headers=headers, json=payload_test1, timeout=30)
        
        print(f"Teste 1 (lista de strings): Status {resp1.status_code}")
        if resp1.status_code != 200:
            print(f"Erro: {resp1.text}")
        
        # Teste 2: Lista de objetos (como vem na resposta)
        objetos_importacao = []
        for item in importacoes_ref[:3]:
            objetos_importacao.append({
                "id": item.get('id'),
                "value": item.get('value')
            })
        
        payload_test2 = {"importacoes": objetos_importacao}
        
        print(f"\n📥 Testando importações como objetos:")
        print(json.dumps(payload_test2, indent=2, ensure_ascii=False))
        
        resp2 = requests.patch(patch_url, headers=headers, json=payload_test2, timeout=30)
        print(f"Teste 2 (lista de objetos): Status {resp2.status_code}")
        if resp2.status_code != 200:
            print(f"Erro: {resp2.text}")

def main():
    print("🔍 ANÁLISE: Descobrindo formato correto dos campos de múltipla seleção")
    print("="*60)
    
    # 1. Inspecionar projeto de referência
    projeto_ref = inspecionar_projeto_de_referencia()
    
    # 2. Testar formato descoberto no projeto de teste
    project_id_teste = "2376502000005609159"  # O projeto que criamos no teste anterior
    
    if projeto_ref:
        print("\n" + "="*60)
        testar_formato_descoberto(project_id_teste, projeto_ref)
    
    print("\n✅ Análise concluída!")

if __name__ == "__main__":
    main()