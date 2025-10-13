# -*- coding: utf-8 -*-
"""
Script para testar a busca e atribuição de tarefas em um projeto real.
"""

import requests
import re
import unicodedata
from config import (
    ZOHO_PORTAL_ID,
    DONOS_PROJETO,
    TAREFAS_PARA_ATRIBUIR,
    TAREFAS_PARA_CONCLUIR,
)
from utils import obter_access_token

def test_task_finding_and_assignment():
    """Testa busca e atribuição de tarefas."""
    
    print(f"===== TESTE DE BUSCA E ATRIBUIÇÃO DE TAREFAS =====")
    
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
        
        data = resp.json()
        if isinstance(data, list):
            projects = data
        else:
            projects = data.get('projects', [])
        
        project_id = projects[0].get('id')
        project_name = projects[0].get('name', 'SEM_NOME')
        print(f"INFO: Testando com projeto {project_id} - '{project_name}'")
        
        # Buscar tarefas
        url_tasks = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
        resp_tasks = requests.get(url_tasks, headers=headers, timeout=30)
        
        tasks_data = resp_tasks.json()
        if isinstance(tasks_data, dict):
            tasks = tasks_data.get('tasks', [])
        else:
            tasks = tasks_data
        
        print(f"INFO: Encontradas {len(tasks)} tarefas no projeto")
        
        # Indexar tarefas
        tarefas_por_nome = {}
        for t in tasks:
            nome = (t.get('name') or '').strip()
            if nome:
                tarefas_por_nome[nome] = t
        
        print(f"INFO: {len(tarefas_por_nome)} tarefas indexadas por nome")
        
        # Mostrar todas as tarefas para análise
        print(f"\nTODAS AS TAREFAS NO PROJETO:")
        for i, (nome, task) in enumerate(tarefas_por_nome.items(), 1):
            owner = (task.get('owner') or {}).get('zpuid', 'SEM_OWNER')
            status = task.get('status', {}).get('name', 'SEM_STATUS')
            print(f"  {i:2d}. '{nome}' | Owner: {owner} | Status: {status}")
        
        # Função de normalização
        def _normalize(n: str) -> str:
            if not n:
                return ''
            t = n.strip()
            try:
                t = re.sub(r'^\s*\d+(?:\.\d+)*\s*-\s*', '', t)
            except Exception:
                pass
            try:
                t = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
            except Exception:
                pass
            t = t.casefold()
            t = ' '.join(t.split())
            return t
        
        tarefas_por_nome_norm = {}
        for k, v in tarefas_por_nome.items():
            tarefas_por_nome_norm[_normalize(k)] = v
        
        # Função de busca melhorada
        def _get_task_by_name(nome_raw: str):
            print(f"\nDEBUG: Buscando tarefa: '{nome_raw}'")
            
            # 1. Busca exata
            t = tarefas_por_nome.get(nome_raw)
            if t:
                print(f"DEBUG: ✓ Match exato encontrado")
                return t
            
            # 2. Busca normalizada
            key = _normalize(nome_raw)
            print(f"DEBUG: Nome normalizado: '{key}'")
            t2 = tarefas_por_nome_norm.get(key)
            if t2:
                print(f"DEBUG: ✓ Match normalizado -> '{t2.get('name')}'")
                return t2
            
            # 3. Busca por substring
            for name, task in tarefas_por_nome.items():
                norm_name = _normalize(name)
                if key in norm_name or norm_name in key:
                    print(f"DEBUG: ✓ Match por substring -> '{name}'")
                    return task
            
            # 4. Busca por palavras-chave
            palavras_chave = key.split()
            print(f"DEBUG: Palavras-chave: {palavras_chave}")
            
            best_match = None
            best_score = 0
            
            for name, task in tarefas_por_nome.items():
                norm_name = _normalize(name)
                score = sum(1 for palavra in palavras_chave if palavra in norm_name)
                if score > best_score and score >= max(1, len(palavras_chave) - 1):
                    best_match = task
                    best_score = score
                    print(f"DEBUG: Candidato: '{name}' (score: {score}/{len(palavras_chave)})")
            
            if best_match:
                print(f"DEBUG: ✓ Melhor match por palavras-chave -> '{best_match.get('name')}'")
                return best_match
            
            print(f"DEBUG: ✗ Nenhum match encontrado")
            return None
        
        # Testar busca das tarefas configuradas
        print(f"\n===== TESTE DE BUSCA DAS TAREFAS CONFIGURADAS =====")
        
        todas_tarefas_config = TAREFAS_PARA_ATRIBUIR + TAREFAS_PARA_CONCLUIR
        
        for nome_tarefa in todas_tarefas_config:
            print(f"\n--- Testando: '{nome_tarefa}' ---")
            task = _get_task_by_name(nome_tarefa)
            
            if task:
                task_id = task.get('id')
                task_name = task.get('name')
                owner = (task.get('owner') or {}).get('zpuid')
                status = task.get('status', {}).get('name')
                print(f"✓ ENCONTRADA: ID={task_id}, Nome='{task_name}', Owner={owner}, Status={status}")
            else:
                print(f"✗ NÃO ENCONTRADA")
        
        # Testar atribuição de uma tarefa (se encontrou alguma)
        print(f"\n===== TESTE DE ATRIBUIÇÃO =====")
        
        gp_name = "Giovani de Sousa"  # ou outro GP disponível
        if gp_name not in DONOS_PROJETO:
            gp_name = list(DONOS_PROJETO.keys())[0]
        
        gp_zpuid = DONOS_PROJETO[gp_name]
        print(f"INFO: Usando GP '{gp_name}' (zpuid: {gp_zpuid})")
        
        # Pegar primeira tarefa das configuradas que foi encontrada
        task_to_test = None
        task_name_to_test = None
        
        for nome_tarefa in TAREFAS_PARA_ATRIBUIR[:3]:  # Testar só as 3 primeiras
            task = _get_task_by_name(nome_tarefa)
            if task:
                task_to_test = task
                task_name_to_test = nome_tarefa
                break
        
        if task_to_test:
            task_id = task_to_test.get('id')
            current_owner = (task_to_test.get('owner') or {}).get('zpuid')
            
            print(f"INFO: Testando atribuição da tarefa '{task_name_to_test}'")
            print(f"INFO: ID: {task_id}, Owner atual: {current_owner}")
            
            if str(current_owner) == str(gp_zpuid):
                print(f"INFO: Tarefa já está atribuída ao GP correto")
            else:
                print(f"INFO: Tentando atribuir para GP {gp_zpuid}...")
                
                # Testar atribuição via API v3
                url_update = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}"
                payload_update = {"owner": {"zpuid": str(gp_zpuid)}}
                
                resp_update = requests.patch(url_update, headers=headers, json=payload_update, timeout=45)
                
                print(f"DEBUG: Response status: {resp_update.status_code}")
                print(f"DEBUG: Response: {resp_update.text[:300]}")
                
                if resp_update.status_code in (200, 201):
                    print(f"✓ ATRIBUIÇÃO BEM-SUCEDIDA!")
                    
                    # Verificar se realmente foi atribuída
                    resp_check = requests.get(url_update, headers=headers, timeout=30)
                    if resp_check.status_code in (200, 201):
                        updated_task = resp_check.json()
                        if 'task' in updated_task:
                            new_owner = (updated_task['task'].get('owner') or {}).get('zpuid')
                        else:
                            new_owner = (updated_task.get('owner') or {}).get('zpuid')
                        print(f"INFO: Owner atualizado para: {new_owner}")
                else:
                    print(f"✗ ATRIBUIÇÃO FALHOU: {resp_update.text[:200]}")
        else:
            print(f"WARN: Nenhuma tarefa configurada foi encontrada para teste")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        print(f"ERROR: {traceback.format_exc()}")
        return False

def main():
    success = test_task_finding_and_assignment()
    print(f"\nTeste {'bem-sucedido' if success else 'falhou'}")

if __name__ == "__main__":
    main()