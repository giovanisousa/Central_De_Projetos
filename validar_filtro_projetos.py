# -*- coding: utf-8 -*-
"""
Script de validação de filtro de projetos do Zoho.

Este script busca TODOS os projetos do Zoho e aplica os filtros de validação:
1. Proprietário deve ser Giovani de Sousa OU Willian dos Anjos
2. Status NÃO deve ser Concluído, Finalizado ou Cancelado

Os projetos que passarem pelos filtros serão exibidos nos logs para validação
antes de implementar a lógica no código principal da aplicação.
"""

import requests
import time
from config import (
    ZOHO_PORTAL_ID,
    DONOS_PROJETO,
    STATUS_CANCELADO_ID,
    STATUS_FINALIZADO_ID,
    STATUS_CONCLUIDO_ID
)
from utils import obter_access_token as obter_access_token_zoho, _zp_base, _zp_headers


# IDs dos proprietários válidos (mapeamento de NOME para ID)
PROPRIETARIOS_VALIDOS_IDS = {
    "Giovani de Sousa": "2376502000000057291",
    "Willian dos Anjos": "2376502000000057285"
}

# Nomes dos proprietários válidos (a API retorna apenas o nome, não o ID)
# Variações conhecidas dos nomes que aparecem na API
PROPRIETARIOS_VALIDOS_NOMES = {
    "Giovani de Sousa",
    "Giovani",  # Variação que aparece na API
    "Willian dos Anjos",
    "willian.anjos",  # Variação que aparece na API
    "Willian Anjos",  # Possível variação
}

# IDs dos status que devem ser EXCLUÍDOS
STATUS_EXCLUIDOS = {
    STATUS_CANCELADO_ID,    # Cancelado
    STATUS_FINALIZADO_ID,   # Finalizado / Completed
    STATUS_CONCLUIDO_ID     # Concluído
}


def validar_projeto(project_data):
    """
    Valida se um projeto atende aos critérios de filtro.
    
    Critérios:
    1. Proprietário (owner) deve ser Giovani de Sousa OU Willian dos Anjos
       (validação por NOME, pois a API não retorna o ID do proprietário)
    2. Status NÃO deve estar na lista de status excluídos
    
    Retorna:
        tuple: (bool, str) - (é_válido, motivo_rejeição)
    """
    # Extrai informações do proprietário
    owner = project_data.get('owner', {})
    owner_id = str(owner.get('id', '')) or 'N/A'
    owner_name = owner.get('name', 'Desconhecido')
    
    # Extrai informações do status
    status = project_data.get('status', {})
    status_id = str(status.get('id', ''))
    status_name = status.get('name', 'Desconhecido')
    
    # Valida proprietário por NOME (pois a API não retorna o ID)
    proprietario_valido = owner_name in PROPRIETARIOS_VALIDOS_NOMES
    
    # Valida status
    status_valido = status_id not in STATUS_EXCLUIDOS
    
    # Determina se o projeto é válido e o motivo de rejeição
    if not proprietario_valido and not status_valido:
        return False, f"Proprietário inválido ({owner_name}) E Status excluído ({status_name})"
    elif not proprietario_valido:
        return False, f"Proprietário inválido ({owner_name})"
    elif not status_valido:
        return False, f"Status excluído ({status_name})"
    
    return True, "Projeto válido"


def listar_todos_projetos():
    """
    Busca TODOS os projetos do Zoho e aplica os filtros de validação.
    Exibe nos logs quais projetos são válidos e quais devem ser excluídos.
    """
    print("=" * 80)
    print("VALIDAÇÃO DE FILTRO DE PROJETOS DO ZOHO")
    print("=" * 80)
    print(f"\nProprietários válidos (nomes aceitos):")
    for nome in sorted(PROPRIETARIOS_VALIDOS_NOMES):
        print(f"  - {nome}")
    
    print(f"\nStatus excluídos:")
    status_names = {
        STATUS_CANCELADO_ID: "Cancelado",
        STATUS_FINALIZADO_ID: "Finalizado",
        STATUS_CONCLUIDO_ID: "Concluído"
    }
    for status_id in STATUS_EXCLUIDOS:
        print(f"  - {status_names.get(status_id, 'Desconhecido')} (ID: {status_id})")
    
    print("\n" + "=" * 80)
    print("BUSCANDO PROJETOS DO ZOHO...")
    print("=" * 80 + "\n")
    
    try:
        access_token = obter_access_token_zoho()
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects"
        headers = _zp_headers(access_token)
        
        page = 1
        total_projetos = 0
        projetos_validos = []
        projetos_rejeitados = []
        
        while True:
            params = {"page": page, "per_page": 50}
            print(f"Buscando página {page} de projetos...")
            
            response = requests.get(url, headers=headers, params=params, timeout=45)
            response.raise_for_status()
            data = response.json()
            
            projects = []
            if isinstance(data, dict):
                projects = data.get('projects', [])
            elif isinstance(data, list):
                projects = data
            
            if not projects:
                print("Nenhum projeto encontrado nesta página. Encerrando busca.\n")
                break
            
            print(f"  - {len(projects)} projetos encontrados nesta página\n")
            
            for project in projects:
                total_projetos += 1
                project_id = project.get('id')
                project_name = project.get('name', 'N/A')
                
                # Valida o projeto
                is_valid, reason = validar_projeto(project)
                
                # Informações do proprietário e status
                owner = project.get('owner', {})
                owner_name = owner.get('name', 'Desconhecido')
                owner_id = owner.get('id', 'N/A')
                
                status = project.get('status', {})
                status_name = status.get('name', 'Desconhecido')
                status_id = status.get('id', 'N/A')
                
                project_info = {
                    'id': project_id,
                    'name': project_name,
                    'owner_name': owner_name,
                    'owner_id': owner_id,
                    'status_name': status_name,
                    'status_id': status_id,
                    'reason': reason
                }
                
                if is_valid:
                    projetos_validos.append(project_info)
                    print(f"      [OK] {project_name}")
                else:
                    projetos_rejeitados.append(project_info)
            
            # Verifica se há mais páginas
            if len(projects) < 50:
                break
            
            page += 1
            time.sleep(0.5)  # Pausa para não sobrecarregar a API
        
        # Exibe resumo e resultados
        print("\n" + "=" * 80)
        print("RESUMO DA VALIDACAO")
        print("=" * 80)
        print(f"\nTotal de projetos encontrados: {total_projetos}")
        print(f"Projetos VALIDOS (serao salvos no banco): {len(projetos_validos)}")
        print(f"Projetos REJEITADOS (NAO serao salvos): {len(projetos_rejeitados)}")
        
        # Salva relatório em arquivo
        relatorio_path = "relatorio_validacao_projetos.txt"
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RELATÓRIO DE VALIDAÇÃO DE FILTRO DE PROJETOS\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total de projetos encontrados: {total_projetos}\n")
            f.write(f"Projetos VÁLIDOS (serão salvos no banco): {len(projetos_validos)}\n")
            f.write(f"Projetos REJEITADOS (NÃO serão salvos): {len(projetos_rejeitados)}\n\n")
            
            # Lista projetos válidos
            if projetos_validos:
                f.write("\n" + "=" * 80 + "\n")
                f.write("PROJETOS VÁLIDOS (Serão salvos no banco de dados)\n")
                f.write("=" * 80 + "\n\n")
                for idx, proj in enumerate(projetos_validos, 1):
                    f.write(f"{idx}. {proj['name']}\n")
                    f.write(f"   ID: {proj['id']}\n")
                    f.write(f"   Proprietário: {proj['owner_name']}\n")
                    f.write(f"   Status: {proj['status_name']}\n")
                    f.write(f"   ✓ {proj['reason']}\n\n")
            
            # Lista projetos rejeitados
            if projetos_rejeitados:
                f.write("\n" + "=" * 80 + "\n")
                f.write("PROJETOS REJEITADOS (NÃO serão salvos no banco de dados)\n")
                f.write("=" * 80 + "\n\n")
                for idx, proj in enumerate(projetos_rejeitados, 1):
                    f.write(f"{idx}. {proj['name']}\n")
                    f.write(f"   ID: {proj['id']}\n")
                    f.write(f"   Proprietário: {proj['owner_name']}\n")
                    f.write(f"   Status: {proj['status_name']}\n")
                    f.write(f"   ✗ Motivo: {proj['reason']}\n\n")
        
        print(f"\nRelatorio detalhado salvo em: {relatorio_path}")
        print("\n" + "=" * 80)
        print("VALIDACAO CONCLUIDA!")
        print("=" * 80)
        print("\nSe os resultados estiverem corretos, podemos implementar")
        print("esses filtros no codigo principal da aplicacao (sync_zoho.py).")
        print("=" * 80 + "\n")
        
    except requests.exceptions.RequestException as e:
        print(f"\n[ERRO] ERRO DE API: Falha ao comunicar com o Zoho. {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Detalhes: {e.response.text}")
    except Exception as e:
        print(f"\n[ERRO] ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    listar_todos_projetos()
