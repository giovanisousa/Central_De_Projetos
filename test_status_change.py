# -*- coding: utf-8 -*-
"""
Script para testar mudança de status de uma tarefa específica.
Tenta diferentes IDs de status para ver quais funcionam.
"""

import requests
from config import ZOHO_PORTAL_ID, STATUS_CONCLUIDO_ID
from utils import obter_access_token

def test_status_change():
    """Testa mudança de status em uma tarefa."""
    
    print(f"===== TESTE DE MUDANÇA DE STATUS =====")
    
    try:
        access_token = obter_access_token()
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Buscar um projeto e uma tarefa
        url_projects = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
        resp = requests.get(url_projects, headers=headers, timeout=30)
        
        data = resp.json()
        if isinstance(data, list):
            projects = data
        else:
            projects = data.get('projects', [])
        
        project_id = projects[0].get('id')
        
        # Buscar tarefas
        url_tasks = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
        resp_tasks = requests.get(url_tasks, headers=headers, timeout=30)
        
        tasks_data = resp_tasks.json()
        if isinstance(tasks_data, dict):
            tasks = tasks_data.get('tasks', [])
        else:
            tasks = tasks_data
        
        # Pegar uma tarefa que não seja crítica para teste
        test_task = None
        for task in tasks:
            task_name = task.get('name', '').lower()
            # Escolher uma tarefa de teste não crítica
            if 'teste' in task_name or 'test' in task_name or len(tasks) > 10:
                test_task = task
                break
        
        if not test_task:
            test_task = tasks[0]  # Usar a primeira se não encontrar tarefa de teste
        
        task_id = test_task.get('id')
        task_name = test_task.get('name', 'SEM_NOME')
        current_status = test_task.get('status', {})
        
        print(f"INFO: Testando com tarefa: {task_id} - '{task_name}'")
        print(f"INFO: Status atual: {current_status}")
        
        # Status IDs para testar (incluindo alguns comuns)
        status_ids_to_test = [
            STATUS_CONCLUIDO_ID,  # O que está no config atual
            "2376502000000685557",  # Aberto (sabemos que existe)
            # Alguns IDs comuns que podem existir
            "2376502000000020089",  # STATUS_ABERTO_ID do config
            "2376502000000020092",  # STATUS_EM_ANDAMENTO_ID do config
            "2376502000000020116",  # STATUS_FINALIZADO_ID do config
        ]
        
        print(f"\nTentando diferentes status IDs...")
        
        for i, status_id in enumerate(status_ids_to_test):
            print(f"\nTeste {i+1}: Tentando status ID {status_id}")
            
            # Tentar via API v3 PATCH
            url_v3 = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}"
            payload_v3 = {"status": {"id": status_id}}
            
            try:
                resp_v3 = requests.patch(url_v3, headers=headers, json=payload_v3, timeout=30)
                print(f"  v3 PATCH: Status {resp_v3.status_code}")
                
                if resp_v3.status_code in (200, 201):
                    print(f"  ✓ SUCESSO com v3 PATCH! Status ID {status_id} funciona")
                    
                    # Verificar o status atual da tarefa
                    resp_check = requests.get(url_v3, headers=headers, timeout=30)
                    if resp_check.status_code in (200, 201):
                        updated_task = resp_check.json()
                        if 'task' in updated_task:
                            new_status = updated_task['task'].get('status', {})
                        else:
                            new_status = updated_task.get('status', {})
                        print(f"  Status atualizado para: {new_status}")
                    
                    return status_id  # Retornar o primeiro que funcionar
                else:
                    print(f"  ✗ Falhou: {resp_v3.text[:200]}")
                    
            except Exception as e:
                print(f"  ✗ Exceção: {e}")
            
            # Tentar via REST API
            url_rest = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}/"
            headers_rest = {"Authorization": f"Bearer {access_token}"}
            payload_rest = {"custom_status": status_id}
            
            try:
                resp_rest = requests.post(url_rest, headers=headers_rest, data=payload_rest, timeout=30)
                print(f"  REST POST: Status {resp_rest.status_code}")
                
                if resp_rest.status_code in (200, 201):
                    print(f"  ✓ SUCESSO com REST POST! Status ID {status_id} funciona")
                    return status_id
                else:
                    print(f"  ✗ Falhou: {resp_rest.text[:200]}")
                    
            except Exception as e:
                print(f"  ✗ Exceção: {e}")
        
        print(f"\nNenhum dos status IDs testados funcionou.")
        print(f"Isso pode indicar que:")
        print(f"1. Os IDs estão incorretos para este portal")
        print(f"2. O usuário não tem permissão para alterar status")
        print(f"3. O portal usa um esquema de status diferente")
        
        return None
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        print(f"ERROR: {traceback.format_exc()}")
        return None

def main():
    working_status_id = test_status_change()
    
    if working_status_id:
        print(f"\n✓ Status ID que funciona: {working_status_id}")
        print(f"Atualize o config.py com este valor")
    else:
        print(f"\n✗ Nenhum status ID funcionou")
        print(f"Verifique permissões ou consulte documentação do Zoho")

if __name__ == "__main__":
    main()