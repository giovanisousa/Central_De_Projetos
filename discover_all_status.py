# -*- coding: utf-8 -*-
"""
Script para descobrir todos os status disponíveis no Zoho Projects.
Busca em múltiplos projetos e tarefas para mapear todos os status possíveis.

Uso:
    python discover_all_status.py
"""

import requests
import json
from config import ZOHO_PORTAL_ID
from utils import obter_access_token


def discover_all_status():
    """Descobre todos os status disponíveis no portal."""
    
    print(f"===== DESCOBERTA DE TODOS OS STATUS =====")
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
        
        all_status = {}
        
        # Buscar todos os projetos
        print(f"INFO: Buscando todos os projetos...")
        url_projects = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
        
        resp = requests.get(url_projects, headers=headers, timeout=30)
        
        if resp.status_code not in (200, 201):
            print(f"ERROR: Falha ao buscar projetos - HTTP {resp.status_code}")
            return False
        
        data = resp.json()
        
        # A resposta pode ser uma lista direta ou um objeto com 'projects'
        if isinstance(data, list):
            projects = data
        elif isinstance(data, dict):
            projects = data.get('projects', [])
        else:
            projects = []
        
        print(f"INFO: Encontrados {len(projects)} projetos")
        
        # Buscar tarefas de vários projetos (máximo 10 para não sobrecarregar)
        max_projects = min(10, len(projects))
        
        for i, project in enumerate(projects[:max_projects]):
            project_id = project.get('id')
            project_name = project.get('name', 'SEM_NOME')
            
            print(f"INFO: Analisando projeto {i+1}/{max_projects}: {project_id} - '{project_name[:50]}...'")
            
            # Buscar tarefas com diferentes status
            status_filters = ['all', 'open', 'inprogress', 'completed', 'overdue']
            
            for status_filter in status_filters:
                print(f"  INFO: Buscando tarefas com status '{status_filter}'...")
                
                url_tasks = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
                params = {'status': status_filter}
                
                try:
                    resp_tasks = requests.get(url_tasks, headers=headers, params=params, timeout=20)
                    
                    if resp_tasks.status_code in (200, 201):
                        tasks_data = resp_tasks.json()
                        
                        if isinstance(tasks_data, dict):
                            tasks = tasks_data.get('tasks', [])
                        elif isinstance(tasks_data, list):
                            tasks = tasks_data
                        else:
                            tasks = []
                        
                        print(f"    INFO: Encontradas {len(tasks)} tarefas")
                        
                        # Extrair status das tarefas
                        for task in tasks:
                            status = task.get('status', {})
                            if status and isinstance(status, dict):
                                status_id = status.get('id')
                                status_name = status.get('name', 'SEM_NOME')
                                
                                if status_id and status_id not in all_status:
                                    all_status[status_id] = {
                                        'name': status_name,
                                        'found_in_project': project_name,
                                        'found_with_filter': status_filter
                                    }
                                    print(f"    NOVO STATUS: ID {status_id} = '{status_name}'")
                    else:
                        print(f"    WARN: Falha ao buscar tarefas - HTTP {resp_tasks.status_code}")
                        
                except Exception as e:
                    print(f"    ERROR: Exceção ao buscar tarefas: {e}")
        
        print(f"\n===== TODOS OS STATUS DESCOBERTOS =====")
        print(f"Total de status únicos encontrados: {len(all_status)}")
        
        for status_id, status_info in all_status.items():
            print(f"ID: {status_id}")
            print(f"  Nome: '{status_info['name']}'")
            print(f"  Encontrado no projeto: '{status_info['found_in_project'][:50]}...'")
            print(f"  Filtro usado: {status_info['found_with_filter']}")
            print()
        
        # Gerar sugestões para config.py
        print(f"===== SUGESTÕES PARA config.py =====")
        
        suggestions = {
            'STATUS_ABERTO_ID': ['aberto', 'open', 'novo', 'new'],
            'STATUS_EM_ANDAMENTO_ID': ['em andamento', 'em progresso', 'in progress', 'progress'],
            'STATUS_CONCLUIDO_ID': ['concluído', 'concluido', 'completed', 'done', 'finalizado'],
            'STATUS_CANCELADO_ID': ['cancelado', 'cancelled', 'canceled'],
            'STATUS_FINALIZADO_ID': ['finalizado', 'finished', 'closed', 'fechado'],
        }
        
        print("# Sugestões de IDs para atualizar no config.py:")
        print()
        
        for config_var, keywords in suggestions.items():
            print(f"# {config_var}")
            matches_found = False
            
            for status_id, status_info in all_status.items():
                status_name_lower = status_info['name'].lower()
                
                for keyword in keywords:
                    if keyword in status_name_lower:
                        print(f"{config_var} = \"{status_id}\"  # '{status_info['name']}'")
                        matches_found = True
                        break
                
                if matches_found:
                    break
            
            if not matches_found:
                print(f"# {config_var} = \"ID_NAO_ENCONTRADO\"  # Nenhum match para {keywords}")
            
            print()
        
        # Salvar resultado em arquivo
        result = {
            'portal_id': ZOHO_PORTAL_ID,
            'timestamp': str(__import__('datetime').datetime.now()),
            'total_projects_analyzed': max_projects,
            'total_status_found': len(all_status),
            'status_list': all_status
        }
        
        with open('discovered_status.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"INFO: Resultado salvo em 'discovered_status.json'")
        
        return len(all_status) > 0
        
    except Exception as e:
        print(f"ERROR: Falha na descoberta: {e}")
        import traceback
        print(f"ERROR: Traceback: {traceback.format_exc()}")
        return False


def main():
    success = discover_all_status()
    
    if success:
        print(f"\nDescoberta concluída com sucesso!")
    else:
        print(f"\nDescoberta falhou - verifique os logs acima")


if __name__ == "__main__":
    main()