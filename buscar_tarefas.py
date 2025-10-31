# -*- coding: utf-8 -*-
"""
Script auxiliar para buscar tarefas de um projeto no Zoho Projects e
verificar correspondência com as listas TAREFAS_PARA_ATRIBUIR e
TAREFAS_PARA_CONCLUIR definidas em config.py.

Uso:
    python buscar_tarefas.py [<project_id>]

Se não for informado, usa o ID padrão solicitado: 2376502000005726003
"""

import sys
import time
import re
import unicodedata
from typing import Dict, List, Optional

import requests

from config import (
    ZOHO_PORTAL_ID,
    TAREFAS_PARA_ATRIBUIR,
    TAREFAS_PARA_CONCLUIR,
    DEFAULT_TASKS_CUSTOM_VIEW_ID,
    BASE_DIR
)
from utils import obter_access_token_zoho as obter_access_token, _zp_base, _zp_headers


DEFAULT_PROJECT_ID = "2376502000005726003"


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


def _get_task_by_name(nome_raw: str, tasks_by_name: Dict[str, dict], tasks_by_name_norm: Dict[str, dict]) -> Optional[dict]:
    """Procura tarefa por nome exato, normalizado e por substring normalizada (estratégia tolerante)."""
    if not nome_raw:
        return None
    t = tasks_by_name.get(nome_raw)
    if t:
        return t
    key = _normalize(nome_raw)
    t2 = tasks_by_name_norm.get(key)
    if t2:
        return t2
    # Busca por substring normalizada
    for name, task in tasks_by_name.items():
        try:
            norm_name = _normalize(name)
        except Exception:
            norm_name = name
        if norm_name == key or key in norm_name:
            return task
    return None


def listar_tarefas_do_projeto(project_id: str, access_token: str) -> List[dict]:
    """
    Lista todas as tarefas do projeto usando estratégias múltiplas de paginação para contornar limites (50/100/200 itens):
    1) Somente range (1-200, 201-400, ...)
    2) Index com range fixo (index=1..N, range=1-200)
    3) Index + range progressivo (index=1..N, range=1-50, 51-100, ...)
    Repete tentativas e deduplica por ID. Usa fallback por Custom View se houver.
    """
    headers = _zp_headers(access_token)
    base = _zp_base()

    def _request(url: str) -> List[dict]:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code in (200, 201):
                data = r.json() or {}
                return data.get("tasks", []) if isinstance(data, dict) else []
        except Exception:
            pass
        return []

    tasks_by_id: Dict[str, dict] = {}

    def _collect_range_only(page_size: int = 200, custom_view_id: Optional[str] = None, status: Optional[str] = None, max_pages: int = 40):
        start = 1
        no_progress_pages = 0
        for page in range(1, max_pages + 1):
            end = start + page_size - 1
            if custom_view_id:
                url = (
                    f"{base}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/custom-view/"
                    f"{custom_view_id}?range={start}-{end}"
                )
            else:
                url = f"{base}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks?range={start}-{end}"
                if status:
                    url += f"&status={status}"
            chunk = _request(url)
            new_added = 0
            for t in chunk:
                tid = t.get("id")
                if tid and tid not in tasks_by_id:
                    tasks_by_id[tid] = t
                    new_added += 1
            print(f"[range-only] {start}-{end} s={status or 'default'}: {len(chunk)} itens, novos={new_added}")
            if not chunk or new_added == 0:
                no_progress_pages += 1
            else:
                no_progress_pages = 0
            if not chunk or no_progress_pages >= 2:
                break
            start += page_size
            time.sleep(0.15)

    def _collect_index_fixed(page_size: int = 200, custom_view_id: Optional[str] = None, status: Optional[str] = None, max_pages: int = 60):
        start, end = 1, page_size
        no_progress_pages = 0
        for index in range(1, max_pages + 1):
            if custom_view_id:
                url = (
                    f"{base}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/custom-view/"
                    f"{custom_view_id}?index={index}&range={start}-{end}"
                )
            else:
                url = (
                    f"{base}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks?index={index}&range={start}-{end}"
                )
                if status:
                    url += f"&status={status}"
            chunk = _request(url)
            new_added = 0
            for t in chunk:
                tid = t.get("id")
                if tid and tid not in tasks_by_id:
                    tasks_by_id[tid] = t
                    new_added += 1
            print(f"[index-fixed] index={index} {start}-{end} s={status or 'default'}: {len(chunk)} itens, novos={new_added}")
            if not chunk or new_added == 0:
                no_progress_pages += 1
            else:
                no_progress_pages = 0
            if not chunk or no_progress_pages >= 2:
                break
            time.sleep(0.15)

    def _collect_index_and_range(step_size: int = 50, custom_view_id: Optional[str] = None, status: Optional[str] = None, max_pages: int = 120):
        no_progress_pages = 0
        for page_index in range(1, max_pages + 1):
            start = (page_index - 1) * step_size + 1
            end = page_index * step_size
            if custom_view_id:
                url = (
                    f"{base}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/custom-view/"
                    f"{custom_view_id}?index={page_index}&range={start}-{end}"
                )
            else:
                url = (
                    f"{base}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks?index={page_index}&range={start}-{end}"
                )
                if status:
                    url += f"&status={status}"
            chunk = _request(url)
            new_added = 0
            for t in chunk:
                tid = t.get("id")
                if tid and tid not in tasks_by_id:
                    tasks_by_id[tid] = t
                    new_added += 1
            print(f"[index+range] index={page_index} {start}-{end} s={status or 'default'}: {len(chunk)} itens, novos={new_added}")
            if not chunk or new_added == 0:
                no_progress_pages += 1
            else:
                no_progress_pages = 0
            if not chunk or no_progress_pages >= 2:
                break
            time.sleep(0.12)

    def _collect_index_offset(page_size: int = 200, custom_view_id: Optional[str] = None, status: Optional[str] = None, max_pages: int = 40):
        """
        Variante onde 'index' é tratado como offset absoluto (1, 201, 401, ...),
        e range acompanha o intervalo absoluto "start-end".
        """
        start = 1
        no_progress_pages = 0
        for _ in range(1, max_pages + 1):
            end = start + page_size - 1
            if custom_view_id:
                url = (
                    f"{base}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/custom-view/"
                    f"{custom_view_id}?index={start}&range={start}-{end}"
                )
            else:
                url = (
                    f"{base}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks?index={start}&range={start}-{end}"
                )
                if status:
                    url += f"&status={status}"
            chunk = _request(url)
            new_added = 0
            for t in chunk:
                tid = t.get("id")
                if tid and tid not in tasks_by_id:
                    tasks_by_id[tid] = t
                    new_added += 1
            print(f"[index-offset] index={start} {start}-{end} s={status or 'default'}: {len(chunk)} itens, novos={new_added}")
            if not chunk or new_added == 0:
                no_progress_pages += 1
            else:
                no_progress_pages = 0
            if not chunk or no_progress_pages >= 2:
                break
            start += page_size
            time.sleep(0.15)

    def _collect_page_per_page(per_page: int = 200, status: Optional[str] = None, max_pages: int = 60):
        """
        Fallback alternativo usando "page" e "per_page" (alguns tenants/versões aceitam esses parâmetros).
        """
        no_progress_pages = 0
        for page in range(1, max_pages + 1):
            url = f"{base}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks?page={page}&per_page={per_page}"
            if status:
                url += f"&status={status}"
            chunk = _request(url)
            new_added = 0
            for t in chunk:
                tid = t.get("id")
                if tid and tid not in tasks_by_id:
                    tasks_by_id[tid] = t
                    new_added += 1
            print(f"[page/per_page] page={page} per_page={per_page} s={status or 'default'}: {len(chunk)} itens, novos={new_added}")
            if not chunk or new_added == 0:
                no_progress_pages += 1
            else:
                no_progress_pages = 0
            if not chunk or no_progress_pages >= 2:
                break
            time.sleep(0.15)

    # Execução: tentar cada estratégia algumas vezes (para materialização tardia)
    for tentativa in range(2):
        before_round = len(tasks_by_id)
        print(f"\n[passo] tentativa={tentativa+1} | acumulado={before_round}")
        _collect_range_only(page_size=200, status='all')
        _collect_index_fixed(page_size=200, status='all')
        _collect_index_and_range(step_size=50, status='all')
        _collect_index_offset(page_size=200, status='all')
        _collect_page_per_page(per_page=200, status='all')
        after_round = len(tasks_by_id)
        print(f"[passo] total apos tentativa={tentativa+1}: {after_round}")
        if after_round == before_round:
            break
        time.sleep(0.5)

    # Fallback via Custom View (repete as estratégias quando ainda há poucas tarefas)
    if DEFAULT_TASKS_CUSTOM_VIEW_ID and len(tasks_by_id) < 180:
        for tentativa in range(2):
            before_round = len(tasks_by_id)
            print(f"\n[cv] tentativa={tentativa+1} | acumulado={before_round}")
            _collect_range_only(page_size=200, custom_view_id=DEFAULT_TASKS_CUSTOM_VIEW_ID)
            _collect_index_fixed(page_size=200, custom_view_id=DEFAULT_TASKS_CUSTOM_VIEW_ID)
            _collect_index_and_range(step_size=50, custom_view_id=DEFAULT_TASKS_CUSTOM_VIEW_ID)
            _collect_index_offset(page_size=200, custom_view_id=DEFAULT_TASKS_CUSTOM_VIEW_ID)
            after_round = len(tasks_by_id)
            print(f"[cv] total apos tentativa={tentativa+1}: {after_round}")
            if after_round == before_round:
                break
            time.sleep(0.5)

    # Tentativa extra por status específicos caso ainda esteja baixo
    if len(tasks_by_id) < 180:
        for status_try in ("open", "inprogress", "completed"):
            before_round = len(tasks_by_id)
            print(f"\n[status:{status_try}] acumulado={before_round}")
            _collect_range_only(page_size=200, status=status_try)
            _collect_index_fixed(page_size=200, status=status_try)
            _collect_index_and_range(step_size=50, status=status_try)
            _collect_index_offset(page_size=200, status=status_try)
            _collect_page_per_page(per_page=200, status=status_try)

    return list(tasks_by_id.values())


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROJECT_ID
    print(f"Buscando tarefas do projeto: {project_id}\n")

    access_token = obter_access_token()
    tasks = listar_tarefas_do_projeto(project_id, access_token)
    print(f"Total de tarefas retornadas: {len(tasks)}\n")

    # Indexações por nome
    tasks_by_name: Dict[str, dict] = {}
    tasks_by_name_norm: Dict[str, dict] = {}
    for t in tasks:
        name = (t.get("name") or "").strip()
        if not name:
            continue
        tasks_by_name[name] = t
        tasks_by_name_norm[_normalize(name)] = t

    # Lista todos os nomes para inspeção
    if tasks_by_name:
        nomes = sorted(tasks_by_name.keys())
        print(f"Nomes de tarefas ({len(nomes)}):")
        for i, n in enumerate(nomes, start=1):
            print(f"  {i:02d}. {n}")
        print("")

    # Conjunto alvo: as tarefas do config.py
    alvos = [
        ("ATRIBUIR", nome) for nome in TAREFAS_PARA_ATRIBUIR
    ] + [
        ("CONCLUIR", nome) for nome in TAREFAS_PARA_CONCLUIR
    ]

    print("Verificando correspondência com as tarefas do config.py:\n")
    for tipo, nome in alvos:
        task = _get_task_by_name(nome, tasks_by_name, tasks_by_name_norm)
        if task:
            tid = task.get("id")
            owner = (task.get("owner") or {}).get("zpuid")
            is_done = task.get("is_completed")
            print(f"[OK] ({tipo}) '{nome}' -> id={tid} owner={owner} concluida={is_done}")
        else:
            print(f"[FALHOU MATCH] ({tipo}) '{nome}' -> não encontrada no projeto")

    print("\nConcluído.")


if __name__ == "__main__":
    main()