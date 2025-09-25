# -*- coding: utf-8 -*-
"""
Atualizador de campos customizados do Zoho Projects (v3) para um projeto específico.
- Lista os campos atuais do projeto
- Tenta atualizar tanto via propriedades de projeto (top-level/project) quanto via project.custom_fields
- Faz múltiplas tentativas de payload, incluindo diferentes formas para campos multivalorados

Uso:
    python customizados.py
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from typing import Dict, Tuple, Any, Iterable

import requests

from config import ZOHO_PORTAL_ID
from utils import obter_access_token, _zp_base, _zp_headers


PROJECT_ID = "2376502000005564224"

# Valores solicitados para inserção
BASE_FIELDS: Dict[str, Any] = {
    "havera_integracao": False,
    "solucoes_contratadas": "AnimatiPACS/netRIS",
    "link_do_google": "https://drive.google.com/drive/folders/1aWyEeRMoCN9zC_RkFTFgrFTxVOS02-49",
    "importacoes": [
        {"id": "2376502000005584872", "value": "Imagens"},
        {"id": "2376502000005584868", "value": "Cadastros"},
        {"id": "2376502000005584870", "value": "Laudos"},
    ],
    "havera_importacao": "Sim",
    "projects_cf_0001": "Não",
}


def get_project_details(access_token: str, project_id: str) -> dict:
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}?include=custom_fields"
    r = requests.get(url, headers=_zp_headers(access_token), timeout=30)
    try:
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException:
        url2 = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
        r2 = requests.get(url2, headers=_zp_headers(access_token), timeout=30)
        r2.raise_for_status()
        return r2.json()


def _attempt_put(url: str, headers: Dict[str, str], payload: dict, json_mode: bool = True) -> Tuple[bool, dict | str]:
    try:
        if json_mode:
            r = requests.put(url, headers={**headers, "Content-Type": "application/json"}, json=payload, timeout=40)
        else:
            r = requests.put(url, headers={**headers, "Content-Type": "application/x-www-form-urlencoded"}, data=payload, timeout=40)
        if r.ok:
            try:
                return True, r.json()
            except Exception:
                return True, r.text
        try:
            return False, r.json()
        except Exception:
            return False, r.text
    except Exception as e:
        return False, f"Exception: {e}"


def _variants_for_importacoes(values: Iterable[dict]) -> Iterable[Any]:
    values = list(values or [])
    ids = [v.get("id") for v in values if v.get("id")]
    labels = [v.get("value") for v in values if v.get("value")]
    yield values                         # lista de objetos {id,value}
    if ids:
        yield ids                        # apenas IDs
    if labels:
        yield labels                      # apenas labels/valores


def update_project_properties(access_token: str, project_id: str, fields: Dict[str, Any]) -> dict:
    """Tenta atualizar como propriedades do projeto (fora de custom_fields)."""
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = _zp_headers(access_token)

    # Gera variações para o campo multivalorado 'importacoes'
    importacoes = fields.get("importacoes")
    base_wo_imp = {k: v for k, v in fields.items() if k != "importacoes"}

    attempt_payloads = []
    if importacoes is None:
        variants = [None]
    else:
        variants = list(_variants_for_importacoes(importacoes))

    for imp_variant in variants:
        f = dict(base_wo_imp)
        if imp_variant is not None:
            f["importacoes"] = imp_variant
        # Tenta diferentes envelopamentos aceitos pela API
        attempt_payloads.extend([
            (True, {"project": f}, "JSON project={}"),
            (True, {"projects": [{"id": project_id, **f}]}, "JSON projects[0]={}"),
            (True, f, "JSON topo (sem wrapper)"),
            (False, {"JSONString": json.dumps({"project": f}, ensure_ascii=False)}, "Form-urlencoded JSONString project"),
            (False, {"JSONString": json.dumps({"projects": [{"id": project_id, **f}]}, ensure_ascii=False)}, "Form-urlencoded JSONString projects[0]"),
        ])

    last_error = None
    for is_json, payload, label in attempt_payloads:
        print(f"Tentando propriedades: {label} ...")
        ok, body = _attempt_put(url, headers, payload, json_mode=is_json)
        if ok:
            print("Atualização de propriedades OK.")
            return body if isinstance(body, dict) else {"result": body}
        else:
            print(f"Falha propriedades: {body}")
            last_error = body
            time.sleep(0.7)

    raise RuntimeError(f"Falha ao atualizar propriedades. Último erro: {last_error}")


def update_project_custom_fields(access_token: str, project_id: str, custom_fields: Dict[str, Any]) -> dict:
    """Atualiza via project.custom_fields com múltiplos formatos (inclui variações para 'importacoes')."""
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = _zp_headers(access_token)

    importacoes = custom_fields.get("importacoes")
    base_wo_imp = {k: v for k, v in custom_fields.items() if k != "importacoes"}
    if importacoes is None:
        imp_variants = [None]
    else:
        imp_variants = list(_variants_for_importacoes(importacoes))

    attempt_payloads = []
    for imp_variant in imp_variants:
        cf = dict(base_wo_imp)
        if imp_variant is not None:
            cf["importacoes"] = imp_variant
        attempt_payloads.extend([
            (True, {"custom_fields": cf}, "JSON simples custom_fields"),
            (True, {"project": {"custom_fields": cf}}, "JSON project.custom_fields"),
            (True, {"projects": [{"id": project_id, "custom_fields": cf}]}, "JSON projects[0].custom_fields"),
            (False, {"JSONString": json.dumps({"project": {"custom_fields": cf}}, ensure_ascii=False)}, "Form-urlencoded JSONString project.custom_fields"),
        ])

    last_error = None
    for is_json, payload, label in attempt_payloads:
        print(f"Tentando custom_fields: {label} ...")
        ok, body = _attempt_put(url, headers, payload, json_mode=is_json)
        if ok:
            print("Atualização via custom_fields OK.")
            return body if isinstance(body, dict) else {"result": body}
        else:
            print(f"Falha custom_fields: {body}")
            last_error = body
            time.sleep(0.7)

    raise RuntimeError(f"Falha ao atualizar custom_fields. Último erro: {last_error}")


def main():
    try:
        token = obter_access_token()
        print("Access token obtido.\n")

        print(f"Lendo dados atuais do projeto {PROJECT_ID}...")
        details = get_project_details(token, PROJECT_ID)
        try:
            proj = None
            if isinstance(details, dict):
                proj = details.get("project") or details.get("projects") or details
                if isinstance(proj, list) and proj:
                    proj = proj[0]
        except Exception:
            proj = details
        print("\nCampos atuais (recorte):")
        try:
            # Mostra apenas um recorte relevante se existir
            subset = {k: proj.get(k) for k in [
                "havera_integracao", "solucoes_contratadas", "link_do_google",
                "importacoes", "havera_importacao", "projects_cf_0001", "custom_fields"
            ] if isinstance(proj, dict) and k in proj}
            print(json.dumps(subset or proj, ensure_ascii=False, indent=2))
        except Exception:
            print(str(proj))

        # 1) Tenta atualizar como propriedades do projeto
        try:
            print("\n== Etapa 1: Atualizando propriedades do projeto ==")
            res_props = update_project_properties(token, PROJECT_ID, BASE_FIELDS)
            print(json.dumps(res_props, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"Etapa 1 falhou: {e}")

        # 2) Tenta atualizar via custom_fields (alguns tenants exigem isso)
        try:
            print("\n== Etapa 2: Atualizando via project.custom_fields ==")
            res_cfs = update_project_custom_fields(token, PROJECT_ID, BASE_FIELDS)
            print(json.dumps(res_cfs, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"Etapa 2 falhou: {e}")

        print("\nFinalizado.")

    except Exception as e:
        print(f"Erro: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()