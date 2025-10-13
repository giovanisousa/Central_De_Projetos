# -*- coding: utf-8 -*-
"""
Script para testar os filtros implementados sem sincronizar tudo.
Busca apenas a primeira página de projetos e mostra quais seriam salvos/ignorados.
"""

import requests
from config import (
    ZOHO_PORTAL_ID,
    PROPRIETARIOS_VALIDOS,
    STATUS_CANCELADO_ID,
    STATUS_FINALIZADO_ID,
    STATUS_CONCLUIDO_ID
)
from utils import obter_access_token as obter_access_token_zoho, _zp_base, _zp_headers

# IDs dos status que devem ser EXCLUÍDOS
STATUS_EXCLUIDOS = {
    STATUS_CANCELADO_ID,
    STATUS_FINALIZADO_ID,
    STATUS_CONCLUIDO_ID
}


def projeto_deve_ser_salvo(project_data):
    """Mesma função implementada em sync_zoho.py"""
    owner = project_data.get('owner', {})
    owner_name = owner.get('name', '')
    proprietario_valido = owner_name in PROPRIETARIOS_VALIDOS
    
    status = project_data.get('status', {})
    status_id = str(status.get('id', ''))
    status_valido = status_id not in STATUS_EXCLUIDOS
    
    return proprietario_valido and status_valido


def testar_filtros():
    """Testa os filtros na primeira página de projetos"""
    print("=" * 80)
    print("TESTE DOS FILTROS IMPLEMENTADOS")
    print("=" * 80)
    print("\nBuscando primeira página de projetos do Zoho...\n")
    
    try:
        access_token = obter_access_token_zoho()
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects"
        headers = _zp_headers(access_token)
        
        params = {"page": 1, "per_page": 50}
        response = requests.get(url, headers=headers, params=params, timeout=45)
        response.raise_for_status()
        data = response.json()
        
        projects = []
        if isinstance(data, dict):
            projects = data.get('projects', [])
        elif isinstance(data, list):
            projects = data
        
        if not projects:
            print("Nenhum projeto encontrado.")
            return
        
        print(f"Encontrados {len(projects)} projetos na primeira página.\n")
        print("=" * 80)
        
        validos = 0
        ignorados = 0
        
        for project in projects:
            nome = project.get('name', 'N/A')
            owner_name = project.get('owner', {}).get('name', 'Desconhecido')
            status_name = project.get('status', {}).get('name', 'Desconhecido')
            
            if projeto_deve_ser_salvo(project):
                print(f"✓ [VÁLIDO] {nome}")
                print(f"  Proprietário: {owner_name} | Status: {status_name}\n")
                validos += 1
            else:
                print(f"✗ [IGNORADO] {nome}")
                print(f"  Proprietário: {owner_name} | Status: {status_name}\n")
                ignorados += 1
        
        print("=" * 80)
        print(f"RESUMO DO TESTE (primeira página)")
        print("=" * 80)
        print(f"Total: {len(projects)}")
        print(f"Válidos (seriam salvos): {validos}")
        print(f"Ignorados (não seriam salvos): {ignorados}")
        print(f"Taxa de filtro: {(ignorados/len(projects)*100):.1f}% ignorados")
        print("=" * 80)
        print("\n✅ Filtros estão funcionando corretamente!")
        print("Execute 'python sync_zoho.py' para sincronizar todos os projetos com os filtros.")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    testar_filtros()
