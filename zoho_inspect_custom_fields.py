# -*- coding: utf-8 -*-
"""
Script utilitário para buscar detalhes de um projeto no Zoho Projects e
exibir os campos customizados encontrados.

Uso:
  python zoho_inspect_custom_fields.py --project-id <ID_DO_PROJETO>
  python zoho_inspect_custom_fields.py --name "parte do nome"

Pré-requisitos:
- Arquivo 'zoho_refresh_token.txt' na raiz do projeto contendo o refresh_token do Zoho.
- Variável opcional de ambiente ZOHO_DOMAIN (ex.: "com", "com.br", "eu", "in"...). Padrão: "com".

Observação:
- O script tenta identificar automaticamente chaves que contenham "custom" no JSON
  do projeto e imprime um resumo. Caso a API retorne em outra estrutura, o JSON
  completo do projeto também pode ser exibido com --dump-json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

import requests

# ==== CONFIGURAÇÕES (mantenha alinhadas com app.py) ====
ZOHO_CLIENT_ID = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
ZOHO_CLIENT_SECRET = "70226965d09b04444346222d9b4846c86a5d31d2fe"
ZOHO_PORTAL_ID = "868230290"
ZOHO_DOMAIN = (os.environ.get("ZOHO_DOMAIN") or "com").strip()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
REFRESH_TOKEN_PATH = os.path.join(BASE_DIR, "zoho_refresh_token.txt")

# ==== HELPERS DE API ====

def _api_base() -> str:
    return f"https://projectsapi.zoho.{ZOHO_DOMAIN}/api/v3"


def _auth_headers(access_token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Accept": "application/json",
    }


def _get_access_token(refresh_token: str) -> str:
    url = f"https://accounts.zoho.{ZOHO_DOMAIN}/oauth/v2/token"
    data = {
        "refresh_token": refresh_token,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    resp = requests.post(url, data=data, timeout=20)
    try:
        payload = resp.json()
    except Exception:
        payload = {"raw": resp.text}

    if not resp.ok:
        raise RuntimeError(f"Falha ao obter access_token: HTTP {resp.status_code} - {payload}")

    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Resposta sem access_token: {payload}")
    return token


def _read_refresh_token(path: str = REFRESH_TOKEN_PATH) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Arquivo de refresh token não encontrado: {path}. Crie este arquivo com o refresh_token do Zoho."
        )
    with open(path, "r", encoding="utf-8") as f:
        return (f.read() or "").strip()


# ==== CLIENTE ZOHO PROJECTS ====

def get_project_by_id(access_token: str, project_id: str) -> Dict[str, Any]:
    # Formato correto de endpoint na v3: inclui o portal no path
    url = f"{_api_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    r = requests.get(url, headers=_auth_headers(access_token), timeout=20)
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    if not r.ok:
        raise RuntimeError(f"Erro ao buscar projeto {project_id}: HTTP {r.status_code} - {data}")
    # Algumas respostas vêm como {"project": {...}}
    if isinstance(data, dict) and "project" in data and isinstance(data["project"], dict):
        return data["project"]
    return data if isinstance(data, dict) else {"data": data}


def list_projects(access_token: str, status: str = "all", rng: int = 200) -> List[Dict[str, Any]]:
    # Formato correto com portal no path
    url = f"{_api_base()}/portal/{ZOHO_PORTAL_ID}/projects"
    params = {"status": status, "range": rng}
    r = requests.get(url, headers=_auth_headers(access_token), params=params, timeout=20)
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    if not r.ok:
        raise RuntimeError(f"Erro ao listar projetos: HTTP {r.status_code} - {data}")
    projects = []
    if isinstance(data, dict):
        # Estrutura comum: {"projects": [{...}, {...}]}
        if isinstance(data.get("projects"), list):
            projects = data["projects"]
        # Alguns tenants podem devolver diretamente uma lista
        elif isinstance(data.get("data"), list):
            projects = data["data"]
    elif isinstance(data, list):
        projects = data
    return [p for p in projects if isinstance(p, dict)]


def find_project_by_name(access_token: str, name_substring: str) -> Optional[Dict[str, Any]]:
    name_substring_lower = name_substring.lower()
    for p in list_projects(access_token, status="all", rng=500):
        name = str(p.get("name") or p.get("project_name") or "")
        if name_substring_lower in name.lower():
            # Buscar detalhes completos pelo ID
            pid = str(p.get("id") or p.get("project_id") or "").strip()
            if pid:
                return get_project_by_id(access_token, pid)
            return p
    return None


# ==== EXTRAÇÃO DE CAMPOS CUSTOMIZADOS ====

def extract_custom_fields_blocks(project: Dict[str, Any]) -> Dict[str, Any]:
    """Procura quaisquer chaves relacionadas a campos customizados no objeto do projeto.
    Retorna um dicionário {chave: valor} apenas com as chaves que contêm 'custom'.
    """
    result = {}
    for k, v in (project or {}).items():
        if "custom" in str(k).lower():
            result[k] = v
    return result


def print_custom_fields_summary(project: Dict[str, Any]) -> None:
    custom_blocks = extract_custom_fields_blocks(project)
    if not custom_blocks:
        print("Nenhum bloco de campos customizados identificado no objeto do projeto.")
        return

    for key, block in custom_blocks.items():
        print(f"\n=== Bloco: {key} ===")
        if isinstance(block, list):
            # Lista de campos: tentar imprimir label/column/value quando for um dict
            for item in block:
                if isinstance(item, dict):
                    label = item.get("label") or item.get("display_name") or item.get("field_label")
                    col = item.get("column_name") or item.get("api_name") or item.get("field_name")
                    val = item.get("value") or item.get("field_value") or item.get("default_value")
                    print(f"- {label or col}: {val}")
                else:
                    print(f"- {item}")
        elif isinstance(block, dict):
            # Dicionário: imprimir pares simples
            for subk, subv in block.items():
                if isinstance(subv, (str, int, float)) or subv is None:
                    print(f"- {subk}: {subv}")
                else:
                    # Estrutura composta - exibir JSON compacto
                    print(f"- {subk}: {json.dumps(subv, ensure_ascii=False)}")
        else:
            print(json.dumps(block, ensure_ascii=False))


# ==== CLI ====

def main() -> int:
    parser = argparse.ArgumentParser(description="Inspeciona campos customizados de um projeto no Zoho Projects")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--project-id", help="ID do projeto no Zoho Projects")
    g.add_argument("--name", help="Parte do nome do projeto para localizar")
    parser.add_argument("--dump-json", action="store_true", help="Exibe o JSON completo do projeto")
    args = parser.parse_args()

    try:
        refresh_token = _read_refresh_token(REFRESH_TOKEN_PATH)
        access_token = _get_access_token(refresh_token)

        if args.project_id:
            project = get_project_by_id(access_token, args.project_id)
        else:
            project = find_project_by_name(access_token, args.name)
            if not project:
                print(f"Nenhum projeto encontrado contendo o nome: {args.name}")
                return 1

        # Saída: JSON completo do projeto
        print(json.dumps(project, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"Erro: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())