# -*- coding: utf-8 -*-
import json
import os
import sys
import requests
import time
from datetime import date, datetime

from config import (
    ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_PORTAL_ID, ZOHO_TOKEN_PATH,
    ZOHO_PROJECTS_CUSTOM_WEB_HOST, BASE_DIR
)
from dryrun_zoho_payload import montar_payload


def _zoho_domain() -> str:
    return (os.environ.get("ZOHO_DOMAIN") or "com").strip()


def obter_access_token() -> str:
    if not os.path.exists(ZOHO_TOKEN_PATH):
        raise FileNotFoundError(f"Arquivo de refresh token não encontrado: {ZOHO_TOKEN_PATH}")
    with open(ZOHO_TOKEN_PATH, 'r', encoding='utf-8') as f:
        refresh_token = (f.read() or '').strip()
    if not refresh_token:
        raise RuntimeError("Refresh token vazio em zoho_refresh_token.txt")
    if not ZOHO_CLIENT_ID or not ZOHO_CLIENT_SECRET:
        raise RuntimeError("ZOHO_CLIENT_ID/ZOHO_CLIENT_SECRET não definidos")

    url = f"https://accounts.zoho.{_zoho_domain()}/oauth/v2/token"
    payload = {
        "refresh_token": refresh_token,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(url, data=payload, headers=headers, timeout=25)
    try:
        r.raise_for_status()
    except requests.exceptions.RequestException:
        try:
            body = r.json()
        except Exception:
            body = r.text
        raise RuntimeError(f"Falha ao obter access_token: status={r.status_code} body={body}")
    data = r.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"Resposta sem access_token: {data}")
    return token


def diagnosticar_projeto(project_id: str) -> dict:
    """
    Busca os detalhes do projeto para diagnóstico
    """
    token = obter_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Accept": "application/json",
    }
    
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    resp = requests.get(url, headers=headers, timeout=30)
    
    if resp.status_code == 200:
        projeto = resp.json()
        
        print("=== DIAGNÓSTICO DO PROJETO ===")
        print(f"ID: {projeto.get('id')}")
        print(f"Nome: {projeto.get('name')}")
        
        # Campos customizados diretos
        campos_diretos = [
            'solucoes_contratadas',
            'havera_integracao', 
            'havera_importacao',
            'projects_cf_0001',
            'link_do_google'
        ]
        
        print("\n=== CAMPOS CUSTOMIZADOS DIRETOS ===")
        for campo in campos_diretos:
            valor = projeto.get(campo)
            print(f"{campo}: {valor}")
        
        # Campos de múltipla seleção
        print("\n=== CAMPOS DE MÚLTIPLA SELEÇÃO ===")
        
        integracoes = projeto.get('integracoes', [])
        print(f"integracoes ({len(integracoes)} items):")
        for item in integracoes:
            print(f"  - ID: {item.get('id')}, Value: {item.get('value')}")
        
        importacoes = projeto.get('importacoes', [])  
        print(f"importacoes ({len(importacoes)} items):")
        for item in importacoes:
            print(f"  - ID: {item.get('id')}, Value: {item.get('value')}")
        
        return projeto
    else:
        error_msg = f"Erro ao buscar projeto: {resp.status_code} - {resp.text}"
        print(error_msg)
        raise RuntimeError(error_msg)


def descobrir_ids_campos_customizados():
    """
    Descobre os IDs corretos dos campos de múltipla seleção
    """
    token = obter_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Accept": "application/json",
    }
    
    # Buscar detalhes do layout
    layout_id = "2376502000005584766"
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/layouts/{layout_id}/"
    resp = requests.get(url, headers=headers, timeout=30)
    
    if resp.status_code != 200:
        print(f"⚠️  Não foi possível buscar layout: {resp.status_code}")
        return {}, {}
    
    layout_details = resp.json()
    
    integracoes_ids = {}
    importacoes_ids = {}
    
    # Procurar campos customizados
    for field in layout_details.get('custom_fields', []):
        field_name = field.get('field_name', '').lower()
        
        if 'integr' in field_name and field.get('field_type') == 'picklist':
            print(f"🔍 Campo de integrações encontrado: {field.get('field_name')}")
            for opcao in field.get('picklist_values', []):
                valor = opcao.get('value', '')
                id_opcao = opcao.get('id', '')
                integracoes_ids[valor] = id_opcao
                print(f"  {valor}: {id_opcao}")
        
        elif 'import' in field_name and field.get('field_type') == 'picklist':
            print(f"🔍 Campo de importações encontrado: {field.get('field_name')}")
            for opcao in field.get('picklist_values', []):
                valor = opcao.get('value', '')
                id_opcao = opcao.get('id', '')
                importacoes_ids[valor] = id_opcao
                print(f"  {valor}: {id_opcao}")
    
    return integracoes_ids, importacoes_ids



def criar_projeto_com_retry(dados: dict) -> dict:
    """
    Cria projeto com estratégia de retry para campos customizados
    Usa o formato correto descoberto: objetos {id, value} para múltipla seleção
    """
    token = obter_access_token()
    payload = montar_payload(dados)
    
    print("=== PAYLOAD SENDO ENVIADO ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    # Primeira tentativa: criar projeto
    print("\n=== CRIANDO PROJETO ===")
    resp = requests.post(url, headers=headers, json=payload, timeout=45)
    try:
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Erro ao criar projeto: status={resp.status_code}, body={resp.text[:1000]}") from e

    projeto_criado = resp.json() if resp.text else {}
    project_id = projeto_criado.get('id')
    if not project_id:
        raise RuntimeError(f"Resposta OK, mas sem id do projeto: {projeto_criado}")

    print(f"✅ Projeto criado com sucesso! ID: {project_id}")
    
    # Aguardar um momento para o projeto ser processado
    print("⏳ Aguardando processamento...")
    time.sleep(3)
    
    # Segunda tentativa: PATCH de reforço com custom_fields
    print("\n=== APLICANDO PATCH DE REFORÇO ===")
    try:
        patch_url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
        patch_payload = {
            "custom_fields": payload.get('custom_fields', {}),
            "custom_fields_udf": payload.get('custom_fields_udf', {}),
        }
        
        print("Payload do PATCH:")
        print(json.dumps(patch_payload, indent=2, ensure_ascii=False))
        
        patch_resp = requests.patch(patch_url, headers=headers, json=patch_payload, timeout=30)
        if patch_resp.status_code in (200, 201):
            print("✅ PATCH aplicado com sucesso!")
        else:
            print(f"⚠️  PATCH retornou status {patch_resp.status_code}: {patch_resp.text[:500]}")
    except Exception as e:
        print(f"❌ Erro no PATCH de custom_fields: {e}")

    # Terceira tentativa: PUT individual para campos críticos
    print("\n=== APLICANDO PUT INDIVIDUAL PARA CAMPOS CRÍTICOS ===")
    campos_criticos = payload.get('custom_fields', {})
    
    for field_name, field_value in campos_criticos.items():
        if field_value:  # Só tentar atualizar campos não vazios
            try:
                individual_payload = {field_name: field_value}
                put_resp = requests.put(patch_url, headers=headers, json=individual_payload, timeout=20)
                
                if put_resp.status_code in (200, 201):
                    print(f"✅ Campo {field_name} atualizado")
                else:
                    print(f"⚠️  Falha ao atualizar {field_name}: {put_resp.status_code}")
            except Exception as e:
                print(f"❌ Erro ao atualizar {field_name}: {e}")
            
            time.sleep(0.5)  # Pequeno delay entre requests

    # Monta link do projeto
    base = (ZOHO_PROJECTS_CUSTOM_WEB_HOST or 'https://projects.zoho.com').rstrip('/')
    link = f"{base}/portal/{ZOHO_PORTAL_ID}#myprojects/{project_id}"

    # Diagnóstico final
    print("\n=== DIAGNÓSTICO FINAL ===")
    try:
        diagnosticar_projeto(project_id)
    except Exception as e:
        print(f"Erro no diagnóstico: {e}")

    return {
        "id": project_id,
        "name": projeto_criado.get('name'),
        "link": link,
        "payload": payload,
    }


def criar_projeto(dados: dict) -> dict:
    """
    Função principal para criar projeto (mantida para compatibilidade)
    """
    return criar_projeto_com_retry(dados)


def patch_custom_fields(project_id: str, dados: dict | None = None) -> dict:
    """Atualiza apenas os custom_fields de um projeto já criado."""
    token = obter_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    # Se dados não for fornecido, aplicar somente campos UDF/visíveis que conhecemos
    payload = montar_payload(dados) if dados else {}
    patch_body = {
        "custom_fields": payload.get("custom_fields", {}),
        "custom_fields_udf": payload.get("custom_fields_udf", {}),
    }
    
    # Também adicionar campos no nível raiz
    if payload.get("custom_fields"):
        patch_body.update(payload["custom_fields"])

    print("=== PATCH PAYLOAD ===")
    print(json.dumps(patch_body, indent=2, ensure_ascii=False))

    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    resp = requests.patch(url, headers=headers, json=patch_body, timeout=45)
    try:
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Erro no PATCH de custom_fields: status={resp.status_code}, body={resp.text[:1000]}") from e
    
    result = resp.json() if resp.text else {}
    
    # Diagnóstico após o patch
    print("\n=== DIAGNÓSTICO PÓS-PATCH ===")
    try:
        diagnosticar_projeto(project_id)
    except Exception as e:
        print(f"Erro no diagnóstico: {e}")
    
    return result


if __name__ == '__main__':
    # Dados iguais ao dry-run
    dados = {
        'produto': 'AnimatiPACS/netRIS',
        'integracao_status': 's',
        'importacao': 's',
        'integ_worklist': True,
        'integ_laudos': True,
        'integ_lab': False,
        'integ_teleradiologia': True,
        'integ_outros': False,
        'import_cadastros': True,
        'import_prontuarios': True,
        'import_laudos': False,
        'import_imagens': True,
        'gp_selecionado': 'Giovani de Sousa',
        'codigo_contrato_numero': '1234',
        'nome_cliente': 'Cliente Dry-Run',
        'start_date': '19-09-2025',
        'servidor': 'Cloud Animati',
        'link_google': 'https://drive.google.com/fake-folder',
        'observacoes': 'Projeto de teste dry-run',
        'data_de_virada': '25/09/2025',
    }

    # Execução flexível via argumento
    if len(sys.argv) > 1:
        if sys.argv[1] == "diagnosticar" and len(sys.argv) > 2:
            # python create_real_zoho_project.py diagnosticar PROJECT_ID
            project_id_arg = sys.argv[2]
            print(f"Executando diagnóstico do projeto {project_id_arg}...")
            diagnosticar_projeto(project_id_arg)
        else:
            # python create_real_zoho_project.py PROJECT_ID
            projeto_id_arg = sys.argv[1]
            print(f"Aplicando PATCH de custom_fields no projeto {projeto_id_arg}...")
            resp = patch_custom_fields(projeto_id_arg, dados)
            print("=== PATCH APLICADO ===")
            print(json.dumps(resp, indent=2, ensure_ascii=False))
    else:
        # python create_real_zoho_project.py
        print("🚀 Iniciando criação de projeto...")
        result = criar_projeto(dados)
        print("\n=== RESULTADO FINAL ===")
        print(json.dumps({k: v for k, v in result.items() if k != 'payload'}, indent=2, ensure_ascii=False))
        print(f"\n🔗 Link do projeto: {result['link']}")
        print(f"📋 ID do projeto: {result['id']}")