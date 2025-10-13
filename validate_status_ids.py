# -*- coding: utf-8 -*-
"""
Script para validar IDs de status no Zoho Projects.
Verifica se os STATUS_CONCLUIDO_ID e outros IDs estão corretos.

Uso:
    python validate_status_ids.py
"""

import requests
import json
from config import (
    ZOHO_PORTAL_ID,
    STATUS_CONCLUIDO_ID,
    STATUS_EM_ANDAMENTO_ID,
    STATUS_ABERTO_ID,
    STATUS_CANCELADO_ID,
    STATUS_FINALIZADO_ID,
)
from utils import obter_access_token


def validate_status_ids():
    """Valida se os IDs de status configurados estão corretos."""
    
    print(f"===== VALIDAÇÃO DE IDs DE STATUS =====")
    print(f"Portal ID: {ZOHO_PORTAL_ID}")
    
    try:
        # Obter access token
        access_token = obter_access_token()
        print(f"INFO: Token obtido com sucesso")
        
        # Headers para API
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Buscar um projeto para obter os status através das tarefas
        print(f"INFO: Buscando projetos para extrair status...")
        url_projects = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
        
        resp = requests.get(url_projects, headers=headers, timeout=30)
        
        if resp.status_code not in (200, 201):
            print(f"ERROR: Falha ao buscar projetos - HTTP {resp.status_code}")
            print(f"ERROR: Response: {resp.text}")
            return False
        
        data = resp.json()
        
        # A resposta pode ser uma lista direta ou um objeto com 'projects'
        if isinstance(data, list):
            projects = data
        elif isinstance(data, dict):
            projects = data.get('projects', [])
        else:
            projects = []
        
        if not projects:
            print(f"ERROR: Nenhum projeto encontrado no portal")
            return False
        
        # Pegar o primeiro projeto e buscar suas tarefas para extrair status
        project_id = projects[0].get('id')
        print(f"INFO: Usando projeto {project_id} para extrair status...")
        
        url_tasks = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
        
        resp_tasks = requests.get(url_tasks, headers=headers, timeout=30)
        
        if resp_tasks.status_code not in (200, 201):
            print(f"ERROR: Falha ao buscar tarefas - HTTP {resp_tasks.status_code}")
            print(f"ERROR: Response: {resp_tasks.text}")
            return False
        
        tasks_data = resp_tasks.json()
        tasks = tasks_data.get('tasks', [])
        
        print(f"INFO: Encontradas {len(tasks)} tarefas no projeto")
        
        # Extrair status únicos das tarefas
        status_map = {}
        for task in tasks:
            status = task.get('status', {})
            if status:
                status_id = status.get('id')
                status_name = status.get('name', 'SEM_NOME')
                
                if status_id and status_id not in status_map:
                    status_map[status_id] = {
                        'name': status_name,
                        'type': 'task_status'
                    }
        
        print(f"\nStatus encontrados nas tarefas:")
        for status_id, status_info in status_map.items():
            print(f"  ID: {status_id} | Nome: '{status_info['name']}'")
        
        # Tentar buscar status do portal de forma alternativa
        print(f"\nINFO: Tentando buscar layouts de projeto para mais status...")
        url_layouts = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projectlayouts"
        
        resp_layouts = requests.get(url_layouts, headers=headers, timeout=30)
        
        if resp_layouts.status_code in (200, 201):
            layouts_data = resp_layouts.json()
            layouts = layouts_data.get('project_layouts', [])
            
            for layout in layouts:
                # Extrair status dos layouts se disponível
                status_list = layout.get('status', [])
                for status in status_list:
                    status_id = status.get('id')
                    status_name = status.get('name', 'SEM_NOME')
                    
                    if status_id and status_id not in status_map:
                        status_map[status_id] = {
                            'name': status_name,
                            'type': 'layout_status'
                        }
        
        print(f"\nTodos os status disponíveis encontrados ({len(status_map)}):")
        for status_id, status_info in status_map.items():
            print(f"  ID: {status_id} | Nome: '{status_info['name']}' | Fonte: {status_info['type']}")
        
        # Validar os IDs configurados
        print(f"\n===== VALIDAÇÃO DOS IDs CONFIGURADOS =====")
        
        config_statuses = {
            'STATUS_CONCLUIDO_ID': STATUS_CONCLUIDO_ID,
            'STATUS_EM_ANDAMENTO_ID': STATUS_EM_ANDAMENTO_ID,
            'STATUS_ABERTO_ID': STATUS_ABERTO_ID,
            'STATUS_CANCELADO_ID': STATUS_CANCELADO_ID,
            'STATUS_FINALIZADO_ID': STATUS_FINALIZADO_ID,
        }
        
        all_valid = True
        
        for config_name, config_id in config_statuses.items():
            if config_id in status_map:
                status_info = status_map[config_id]
                print(f"✓ {config_name}: {config_id} = '{status_info['name']}' ({status_info['type']})")
            else:
                print(f"✗ {config_name}: {config_id} = NÃO ENCONTRADO")
                all_valid = False
        
        if all_valid:
            print(f"\n✓ Todos os IDs de status estão válidos!")
        else:
            print(f"\n✗ Alguns IDs de status estão inválidos!")
            print(f"AÇÃO: Atualize os IDs inválidos no arquivo config.py")
        
        # Sugestões para IDs comuns
        print(f"\n===== SUGESTÕES PARA IDs COMUNS =====")
        
        common_patterns = {
            'concluído': ['concluído', 'concluido', 'completed', 'done', 'finalizado'],
            'em andamento': ['em andamento', 'em progresso', 'in progress', 'progress'],
            'aberto': ['aberto', 'open', 'novo', 'new'],
            'cancelado': ['cancelado', 'cancelled', 'canceled'],
        }
        
        for pattern_name, keywords in common_patterns.items():
            print(f"\nPossíveis IDs para '{pattern_name}':")
            found_any = False
            for status_id, status_info in status_map.items():
                status_name_lower = status_info['name'].lower()
                for keyword in keywords:
                    if keyword in status_name_lower:
                        print(f"  ID: {status_id} | Nome: '{status_info['name']}'")
                        found_any = True
                        break
            if not found_any:
                print(f"  Nenhum status encontrado para '{pattern_name}'")
        
        # Teste específico do STATUS_CONCLUIDO_ID
        print(f"\n===== TESTE ESPECÍFICO DO STATUS_CONCLUIDO_ID =====")
        print(f"ID configurado: {STATUS_CONCLUIDO_ID}")
        
        if STATUS_CONCLUIDO_ID in status_map:
            print(f"✓ ID válido: '{status_map[STATUS_CONCLUIDO_ID]['name']}'")
        else:
            print(f"✗ ID inválido - precisa ser corrigido!")
            print(f"SUGESTÃO: Verifique os IDs listados acima e escolha um adequado para 'concluído'")
        
        return all_valid
        
    except Exception as e:
        print(f"ERROR: Falha na validação: {e}")
        import traceback
        print(f"ERROR: Traceback: {traceback.format_exc()}")
        return False


def main():
    success = validate_status_ids()
    
    if success:
        print(f"\nValidação concluída com sucesso!")
    else:
        print(f"\nValidação falhou - verifique os logs acima")


if __name__ == "__main__":
    main()