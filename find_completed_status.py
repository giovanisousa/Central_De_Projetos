# -*- coding: utf-8 -*-
"""
Script simples para descobrir o ID correto do status "Concluído" 
analisando uma tarefa específica e seus possíveis status.
"""

import requests
from config import ZOHO_PORTAL_ID
from utils import obter_access_token

def find_completed_status_id():
    """Encontra o ID correto para status concluído."""
    
    print(f"===== DESCOBRINDO STATUS CONCLUÍDO =====")
    
    try:
        access_token = obter_access_token()
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Buscar um projeto
        url_projects = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
        resp = requests.get(url_projects, headers=headers, timeout=30)
        
        if resp.status_code not in (200, 201):
            print(f"ERROR: Falha ao buscar projetos")
            return None
        
        data = resp.json()
        if isinstance(data, list):
            projects = data
        else:
            projects = data.get('projects', [])
        
        if not projects:
            print(f"ERROR: Nenhum projeto encontrado")
            return None
        
        project_id = projects[0].get('id')
        print(f"INFO: Usando projeto {project_id}")
        
        # Buscar uma tarefa
        url_tasks = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
        resp_tasks = requests.get(url_tasks, headers=headers, timeout=30)
        
        if resp_tasks.status_code not in (200, 201):
            print(f"ERROR: Falha ao buscar tarefas")
            return None
        
        tasks_data = resp_tasks.json()
        if isinstance(tasks_data, dict):
            tasks = tasks_data.get('tasks', [])
        else:
            tasks = tasks_data
        
        if not tasks:
            print(f"ERROR: Nenhuma tarefa encontrada")
            return None
        
        task_id = tasks[0].get('id')
        task_name = tasks[0].get('name', 'SEM_NOME')
        current_status = tasks[0].get('status', {})
        
        print(f"INFO: Usando tarefa {task_id} - '{task_name}'")
        print(f"INFO: Status atual: {current_status}")
        
        # Tentar buscar detalhes da tarefa para ver status disponíveis
        url_task_detail = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}"
        resp_detail = requests.get(url_task_detail, headers=headers, timeout=30)
        
        if resp_detail.status_code in (200, 201):
            task_detail = resp_detail.json()
            print(f"INFO: Detalhes da tarefa obtidos")
            
            # Verificar se há informações sobre status disponíveis
            if 'task' in task_detail:
                task_info = task_detail['task']
                print(f"DEBUG: Task info keys: {list(task_info.keys())}")
        
        # Tentar buscar layouts do projeto para encontrar status
        url_layouts = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projectlayouts"
        resp_layouts = requests.get(url_layouts, headers=headers, timeout=30)
        
        if resp_layouts.status_code in (200, 201):
            layouts_data = resp_layouts.json()
            print(f"INFO: Layouts obtidos")
            
            if 'project_layouts' in layouts_data:
                for layout in layouts_data['project_layouts']:
                    print(f"Layout: {layout.get('name', 'SEM_NOME')}")
                    
                    # Verificar se há status na definição do layout
                    if 'status' in layout:
                        status_list = layout['status']
                        print(f"  Status no layout: {len(status_list)} encontrados")
                        
                        for status in status_list:
                            status_id = status.get('id')
                            status_name = status.get('name', 'SEM_NOME')
                            status_type = status.get('type', 'SEM_TIPO')
                            
                            print(f"    ID: {status_id} | Nome: '{status_name}' | Tipo: {status_type}")
                            
                            # Procurar por status de conclusão
                            name_lower = status_name.lower()
                            if any(word in name_lower for word in ['concluido', 'concluído', 'completed', 'done', 'finalizado']):
                                print(f"  >>> CANDIDATO PARA CONCLUÍDO: {status_id} = '{status_name}' <<<")
                                return status_id
        
        # Se não encontrou nos layouts, sugerir usar o status atual como base para testes
        current_status_id = current_status.get('id')
        if current_status_id:
            print(f"INFO: Status atual da tarefa encontrada: {current_status_id} = '{current_status.get('name')}'")
            print(f"SUGESTÃO: Use este ID como referência ou teste manualmente")
            return current_status_id
        
        return None
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        print(f"ERROR: {traceback.format_exc()}")
        return None

def main():
    status_id = find_completed_status_id()
    
    if status_id:
        print(f"\nSUGESTÃO PARA config.py:")
        print(f"STATUS_CONCLUIDO_ID = \"{status_id}\"")
    else:
        print(f"\nNão foi possível encontrar um ID específico para status concluído")
        print(f"AÇÃO: Execute o discover_all_status.py para análise completa")

if __name__ == "__main__":
    main()