# -*- coding: utf-8 -*-
"""
Utilitário para buscar os detalhes de uma Fase (Milestone) no Zoho Projects.

API utilizada (Zoho Projects v3):
GET /api/v3/portal/[PORTALID]/projects/[PROJECTID]/phases/[PHASEID]
Escopo OAuth: ZohoProjects.milestones.READ

Uso em linha de comando:
    python phases.py <PROJECT_ID> [PHASE_ID]

Exemplo:
    python phases.py 2376502000001234567 2376502000002328681

Observações:
- O script reutiliza o refresh_token salvo em zoho_refresh_token.txt e as
  credenciais do Zoho definidas em config.py (client_id/secret e portal id).
- A phase_id padrão utilizada é 2376502000002328681 (pode ser sobrescrita na CLI).
"""
from __future__ import annotations
import json
import sys
import requests

from config import ZOHO_PORTAL_ID
import utils  # Reutiliza autenticação e helpers de base/headers

# Phase ID solicitada
DEFAULT_PHASE_ID = "2376502000002328681"


def get_phase_detail(project_id: str, phase_id: str = DEFAULT_PHASE_ID) -> dict:
    """Busca os detalhes de uma fase específica em um projeto.

    Args:
        project_id: ID do projeto no Zoho Projects.
        phase_id: ID da fase (milestone) no Zoho Projects.

    Returns:
        dict com o JSON retornado pela API do Zoho.

    Raises:
        RuntimeError em caso de falha na autenticação ou requisição.
    """
    if not project_id:
        raise ValueError("project_id é obrigatório")
    if not phase_id:
        raise ValueError("phase_id é obrigatório")

    # Obtém access_token via refresh_token salvo localmente
    access_token = utils.obter_access_token()

    base = utils._zp_base()  # respeita o domínio configurado
    headers = utils._zp_headers(access_token)

    url = f"{base}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/phases/{phase_id}"

    try:
        resp = requests.get(url, headers=headers, timeout=25)
        if not resp.ok:
            # Tenta incluir corpo para facilitar diagnóstico
            try:
                body = resp.json()
            except Exception:
                body = resp.text
            raise RuntimeError(
                f"Falha ao buscar fase: status={resp.status_code} url={url} body={body}"
            )
        data = resp.json()
        # Retorna o JSON bruto para inspeção completa
        return data
    except requests.RequestException as e:
        raise RuntimeError(f"Erro de rede ao acessar Zoho Projects: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(
            "Uso: python phases.py <PROJECT_ID> [PHASE_ID]", file=sys.stderr
        )
        sys.exit(2)

    project_id_cli = sys.argv[1].strip()
    phase_id_cli = sys.argv[2].strip() if len(sys.argv) == 3 else DEFAULT_PHASE_ID

    try:
        result = get_phase_detail(project_id_cli, phase_id_cli)
        # Imprime JSON formatado para facilitar leitura
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)