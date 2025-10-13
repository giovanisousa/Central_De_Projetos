# -*- coding: utf-8 -*-
"""
Script de teste para diagnosticar problemas com atribuição e conclusão de tarefas.
Permite testar as operações de forma isolada em um projeto específico.

Uso:
    python test_task_assignment.py <project_id> <gp_name>
    
Exemplo:
    python test_task_assignment.py 2376502000005726003 "Giovani de Sousa"
"""

import sys
import traceback
from typing import Dict, List
import requests
import re
import unicodedata

from config import (
    ZOHO_PORTAL_ID,
    DONOS_PROJETO,
    TAREFAS_PARA_ATRIBUIR,
    TAREFAS_PARA_CONCLUIR,
    TEMPO_RELATO,
    STATUS_CONCLUIDO_ID,
    DEFAULT_TASKS_CUSTOM_VIEW_ID,
)
from utils import obter_access_token
from buscar_tarefas import listar_tarefas_do_projeto


def _normalize(name: str) -> str:
    """Normaliza nomes para reduzir mismatches: remove prefixos numéricos, acentos e espaços extras."""
    if not name:
        return ""
    t = (name or "").strip()
    # Remove prefixos do tipo "01.01 - "
    try:
        t = re.sub(r"^\s*\d+(?:\.\d+)*\s*-\s*", "", t)
    except Exception:
        pass
    # Remove acentos
    try:
        t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    except Exception:
        pass
    # Casefold + collapse spaces
    t = t.casefold()
    t = " ".join(t.split())
    return t


def _get_task_by_name(nome_raw: str, tasks_by_name: Dict[str, dict], tasks_by_name_norm: Dict[str, dict]) -> dict:
    """Procura tarefa por nome exato, normalizado e por substring normalizada (estratégia tolerante)."""
    if not nome_raw:
        return None
    
    # Busca exata
    t = tasks_by_name.get(nome_raw)
    if t:
        print(f"DEBUG: Match exato para '{nome_raw}'")
        return t
    
    # Busca normalizada
    key = _normalize(nome_raw)
    t2 = tasks_by_name_norm.get(key)
    if t2:
        print(f"DEBUG: Match normalizado para '{nome_raw}' -> '{t2.get('name')}'")
        return t2
    
    # Busca por substring normalizada
    for name, task in tasks_by_name.items():
        try:
            norm_name = _normalize(name)
        except Exception:
            norm_name = name
        if norm_name == key or key in norm_name:
            print(f"DEBUG: Match por substring para '{nome_raw}' -> '{name}'")
            return task
    
    print(f"WARN: Nenhum match encontrado para '{nome_raw}'")
    return None


def test_task_assignment(project_id: str, gp_name: str):
    """Testa atribuição e conclusão de tarefas em um projeto específico."""
    
    print(f"===== TESTE DE ATRIBUIÇÃO E CONCLUSÃO DE TAREFAS =====")
    print(f"Projeto ID: {project_id}")
    print(f"GP: {gp_name}")
    print(f"======================================================")
    
    # Validar GP
    if gp_name not in DONOS_PROJETO:
        print(f"ERROR: GP inválido '{gp_name}'. GPs válidos: {list(DONOS_PROJETO.keys())}")
        return False
    
    gp_zpuid = DONOS_PROJETO[gp_name]
    print(f"INFO: GP zpuid: {gp_zpuid}")
    
    try:
        # Obter access token
        print(f"INFO: Obtendo access token...")
        access_token = obter_access_token()
        print(f"INFO: Token obtido: {access_token[:20]}...")
        
        # Headers para API
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Listar tarefas do projeto
        print(f"INFO: Buscando tarefas do projeto...")
        tasks = listar_tarefas_do_projeto(project_id, access_token)
        print(f"INFO: Total de tarefas encontradas: {len(tasks)}")
        
        if not tasks:
            print(f"ERROR: Nenhuma tarefa encontrada no projeto {project_id}")
            return False
        
        # Indexar tarefas por nome
        tasks_by_name: Dict[str, dict] = {}
        tasks_by_name_norm: Dict[str, dict] = {}
        
        for t in tasks:
            name = (t.get("name") or "").strip()
            if not name:
                continue
            tasks_by_name[name] = t
            tasks_by_name_norm[_normalize(name)] = t
        
        print(f"INFO: Tarefas indexadas: {len(tasks_by_name)}")
        
        # Mostrar algumas tarefas para debug
        print(f"INFO: Primeiras 5 tarefas:")
        for i, (name, task) in enumerate(list(tasks_by_name.items())[:5]):
            owner = (task.get('owner') or {}).get('zpuid', 'SEM_OWNER')
            completed = task.get('is_completed', False)
            print(f"INFO:   {i+1}. '{name}' | Owner: {owner} | Concluída: {completed}")
        
        # Testar atribuições
        print(f"\n===== TESTANDO ATRIBUIÇÕES =====")
        for nome_tarefa in TAREFAS_PARA_ATRIBUIR[:3]:  # Testa apenas as 3 primeiras
            print(f"INFO: Testando atribuição: '{nome_tarefa}'")
            task = _get_task_by_name(nome_tarefa, tasks_by_name, tasks_by_name_norm)
            
            if not task:
                print(f"ERROR: Tarefa não encontrada: '{nome_tarefa}'")
                continue
            
            task_id = task.get('id')
            current_owner = (task.get('owner') or {}).get('zpuid')
            task_name_actual = task.get('name', 'NOME_NAO_ENCONTRADO')
            
            print(f"INFO: Encontrada - ID: {task_id}, Nome: '{task_name_actual}', Owner atual: {current_owner}")
            
            if str(current_owner) == str(gp_zpuid):
                print(f"INFO: Tarefa já está atribuída corretamente")
                continue
            
            # Testar atribuição
            print(f"INFO: Atribuindo para GP zpuid {gp_zpuid}...")
            try:
                url_update = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}"
                payload_update = {"owner": {"zpuid": str(gp_zpuid)}}
                
                resp_update = requests.patch(url_update, headers=headers, json=payload_update, timeout=45)
                
                print(f"DEBUG: Response status: {resp_update.status_code}")
                print(f"DEBUG: Response: {resp_update.text[:300]}")
                
                if resp_update.status_code in (200, 201):
                    print(f"SUCCESS: Atribuição bem-sucedida!")
                else:
                    print(f"ERROR: Atribuição falhou - Status: {resp_update.status_code}")
                    
            except Exception as e:
                print(f"ERROR: Exceção na atribuição: {e}")
                print(f"ERROR: Traceback: {traceback.format_exc()}")
        
        # Testar conclusões
        print(f"\n===== TESTANDO CONCLUSÕES =====")
        for nome_tarefa in TAREFAS_PARA_CONCLUIR[:2]:  # Testa apenas as 2 primeiras
            print(f"INFO: Testando conclusão: '{nome_tarefa}'")
            task = _get_task_by_name(nome_tarefa, tasks_by_name, tasks_by_name_norm)
            
            if not task:
                print(f"ERROR: Tarefa não encontrada: '{nome_tarefa}'")
                continue
            
            task_id = task.get('id')
            current_owner = (task.get('owner') or {}).get('zpuid')
            is_completed = task.get('is_completed', False)
            task_name_actual = task.get('name', 'NOME_NAO_ENCONTRADO')
            
            print(f"INFO: Encontrada - ID: {task_id}, Nome: '{task_name_actual}', Owner: {current_owner}, Concluída: {is_completed}")
            
            if is_completed:
                print(f"INFO: Tarefa já está concluída")
                continue
            
            # Primeiro atribuir se necessário
            if str(current_owner) != str(gp_zpuid):
                print(f"INFO: Atribuindo para GP antes de concluir...")
                try:
                    url_assign = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}"
                    payload_assign = {"owner": {"zpuid": str(gp_zpuid)}}
                    resp_assign = requests.patch(url_assign, headers=headers, json=payload_assign, timeout=45)
                    
                    if resp_assign.status_code in (200, 201):
                        print(f"SUCCESS: Reatribuição bem-sucedida")
                    else:
                        print(f"WARN: Reatribuição falhou - Status: {resp_assign.status_code}")
                        
                except Exception as e_assign:
                    print(f"ERROR: Erro na reatribuição: {e_assign}")
            
            # Marcar como concluída
            print(f"INFO: Marcando como concluída usando STATUS_CONCLUIDO_ID: {STATUS_CONCLUIDO_ID}")
            try:
                url_complete = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}"
                payload_complete = {"status": {"id": STATUS_CONCLUIDO_ID}}
                
                resp_complete = requests.patch(url_complete, headers=headers, json=payload_complete, timeout=45)
                
                print(f"DEBUG: Response status: {resp_complete.status_code}")
                print(f"DEBUG: Response: {resp_complete.text[:300]}")
                
                if resp_complete.status_code in (200, 201):
                    print(f"SUCCESS: Conclusão bem-sucedida!")
                else:
                    print(f"ERROR: Conclusão falhou - Status: {resp_complete.status_code}")
                    print(f"ERROR: Verifique se STATUS_CONCLUIDO_ID ({STATUS_CONCLUIDO_ID}) está correto")
                    
            except Exception as e_complete:
                print(f"ERROR: Exceção na conclusão: {e_complete}")
                print(f"ERROR: Traceback: {traceback.format_exc()}")
        
        # Testar timesheet
        print(f"\n===== TESTANDO TIMESHEET =====")
        from datetime import date as _date
        hoje = _date.today().strftime('%Y-%m-%d')
        
        for nome_tarefa, tempo_hhmm in list(TEMPO_RELATO.items())[:2]:  # Testa apenas os 2 primeiros
            print(f"INFO: Testando timesheet: '{nome_tarefa}' - {tempo_hhmm}")
            task = _get_task_by_name(nome_tarefa, tasks_by_name, tasks_by_name_norm)
            
            if not task:
                print(f"WARN: Tarefa para timesheet não encontrada: '{nome_tarefa}'")
                continue
            
            task_id = task.get('id')
            task_name_actual = task.get('name', 'NOME_NAO_ENCONTRADO')
            
            print(f"INFO: Lançando {tempo_hhmm} para tarefa ID {task_id}")
            
            try:
                from datetime import datetime as _dt
                mmddyyyy = _dt.strptime(hoje, "%Y-%m-%d").strftime("%m-%d-%Y")
                
                url_rest = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}/logs/"
                headers_rest = {"Authorization": f"Bearer {access_token}"}
                payload_rest = {
                    "owner_zpuid": str(gp_zpuid),
                    "hours": tempo_hhmm,
                    "date": mmddyyyy,
                    "bill_status": "Billable",
                    "notes": "Teste via script de diagnóstico."
                }
                
                print(f"DEBUG: URL: {url_rest}")
                print(f"DEBUG: Payload: {payload_rest}")
                
                resp_rest = requests.post(url_rest, headers=headers_rest, data=payload_rest, timeout=45)
                
                print(f"DEBUG: Response status: {resp_rest.status_code}")
                print(f"DEBUG: Response: {resp_rest.text[:300]}")
                
                if resp_rest.status_code in (200, 201):
                    print(f"SUCCESS: Timesheet bem-sucedido!")
                else:
                    print(f"ERROR: Timesheet falhou - Status: {resp_rest.status_code}")
                    
            except Exception as e2:
                print(f"ERROR: Exceção no timesheet: {e2}")
                print(f"ERROR: Traceback: {traceback.format_exc()}")
        
        print(f"\n===== TESTE FINALIZADO =====")
        return True
        
    except Exception as e:
        print(f"ERROR: Falha geral no teste: {e}")
        print(f"ERROR: Traceback: {traceback.format_exc()}")
        return False


def main():
    if len(sys.argv) < 3:
        print("Uso: python test_task_assignment.py <project_id> <gp_name>")
        print("Exemplo: python test_task_assignment.py 2376502000005726003 \"Giovani de Sousa\"")
        sys.exit(1)
    
    project_id = sys.argv[1]
    gp_name = sys.argv[2]
    
    success = test_task_assignment(project_id, gp_name)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()