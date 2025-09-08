# -*- coding: utf-8 -*-
"""
Teste de verificação de tarefas impeditivas ("00.01 - Itens impeditivos de virada") em um projeto do Zoho Projects.

- Usa as mesmas credenciais do app (client_id/secret e refresh_token em zoho_refresh_token.txt)
- Domínio pode ser ajustado pela variável de ambiente ZOHO_DOMAIN (ex: com, com.br). Padrão: com
- Executa contra um PROJECT_ID e imprime:
  * ID da tasklist encontrada (se houver)
  * Quantidade de tarefas abertas nessa lista

Como executar:
    python teste_tarefas_impeditivos.py 2376502000003782093
ou simplesmente execute sem argumentos para usar o ID padrão acima.
"""

import os
import sys
import json
import time
import requests

# Importa constantes do app (mesmo arquivo usado pelo Flask)
try:
    from app import ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_PORTAL_ID  # type: ignore
except Exception as e:
    print("AVISO: Não foi possível importar constantes do app.py, defina via ambiente ou ajuste abaixo.")
    ZOHO_CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID", "")
    ZOHO_CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET", "")
    ZOHO_PORTAL_ID = os.environ.get("ZOHO_PORTAL_ID", "")

ROOT = os.path.dirname(os.path.abspath(__file__))
REFRESH_PATH = os.path.join(ROOT, "zoho_refresh_token.txt")

DEFAULT_PROJECT_ID = "2376502000003782093"


def _zoho_domain() -> str:
    return (os.environ.get("ZOHO_DOMAIN") or "com").strip()


def _zp_base() -> str:
    return f"https://projectsapi.zoho.{_zoho_domain()}/api/v3"


def _headers(access_token: str) -> dict:
    return {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Accept": "application/json"
    }


def obter_access_token() -> str:
    """Obtém access_token usando refresh_token local."""
    if not ZOHO_CLIENT_ID or not ZOHO_CLIENT_SECRET:
        raise RuntimeError("ZOHO_CLIENT_ID/ZOHO_CLIENT_SECRET não definidos (app.py ou ambiente)")
    if not os.path.exists(REFRESH_PATH):
        raise FileNotFoundError(f"Arquivo não encontrado: {REFRESH_PATH}")
    refresh_token = (open(REFRESH_PATH, 'r', encoding='utf-8').read()).strip()
    if not refresh_token:
        raise RuntimeError("refresh_token vazio em zoho_refresh_token.txt")

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


def buscar_tasklist_impeditivos(access_token: str, project_id: str) -> str | None:
    """Retorna o ID da tasklist '00.01 - Itens impeditivos de virada' (case-insensitive)."""
    alvo = "00.01 - itens impeditivos de virada"
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasklists"
    page = 1
    per_page = 100
    while True:
        params = {"page": page, "per_page": per_page}
        r = requests.get(url, headers=_headers(access_token), params=params, timeout=25)
        r.raise_for_status()
        data = r.json()
        listas = data.get('tasklists') if isinstance(data, dict) else data
        if not isinstance(listas, list):
            listas = []
        for tl in listas:
            nome = str((tl.get('name') or tl.get('title') or '')).strip().lower()
            if nome == alvo:
                return str(tl.get('id') or tl.get('tasklist_id') or '')
        if len(listas) < per_page:
            break
        page += 1
    return None


def contar_tarefas_abertas_na_tasklist(access_token: str, project_id: str, tasklist_id: str) -> int:
    """Conta tarefas abertas pertencentes à tasklist informada."""
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
    page = 1
    per_page = 200
    total_abertas = 0
    while True:
        params = {"page": page, "per_page": per_page}
        r = requests.get(url, headers=_headers(access_token), params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        tarefas = data.get('tasks') if isinstance(data, dict) else data
        if not isinstance(tarefas, list) or not tarefas:
            break
        for t in tarefas:
            # Tasklist vinculado
            tl_id = None
            try:
                tl_id = t.get('tasklist', {}).get('id') or t.get('tasklist_id')
            except Exception:
                tl_id = t.get('tasklist_id')
            if str(tl_id) != str(tasklist_id):
                continue
            # Aberta x Concluída
            is_completed = t.get('is_completed')
            status_name = (t.get('status', {}) or {}).get('name', '')
            if is_completed in [True, 'True', 'true']:
                continue
            if str(status_name).strip().lower() in ['completed', 'concluída', 'finalizado', 'closed']:
                continue
            total_abertas += 1
        if len(tarefas) < per_page:
            break
        page += 1
    return total_abertas


def main():
    project_id = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROJECT_ID).strip()
    print(f"Testando impeditivos para project_id={project_id} | portal={ZOHO_PORTAL_ID} | dom={_zoho_domain()}")
    access_token = obter_access_token()
    print("Access token obtido com sucesso.")

    tasklist_id = buscar_tasklist_impeditivos(access_token, project_id)
    if not tasklist_id:
        print("Tasklist '00.01 - Itens impeditivos de virada' não encontrada neste projeto.")
        print(json.dumps({"project_id": project_id, "tasklist_id": None, "open_tasks": 0}, ensure_ascii=False, indent=2))
        return

    print(f"Tasklist encontrada: {tasklist_id}")
    count = contar_tarefas_abertas_na_tasklist(access_token, project_id, tasklist_id)
    print(f"Tarefas abertas na lista: {count}")

    print(json.dumps({
        "project_id": project_id,
        "tasklist_id": tasklist_id,
        "open_tasks": count
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        # Tenta exibir corpo de erro da API
        resp = getattr(e, 'response', None)
        body = None
        if resp is not None:
            try:
                body = resp.json()
            except Exception:
                body = resp.text
        print(f"HTTPError: status={getattr(resp, 'status_code', '?')} body={body}")
        raise