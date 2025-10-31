import os
import json
import time
import threading
import traceback
import urllib.parse
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Tuple


from flask import session, jsonify, request, current_app
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build



class ZohoTokenError(RuntimeError):
    """Erros relacionados à obtenção do token de acesso Zoho."""

def _ler_refresh_token():
    """Lê o refresh token do Zoho a partir das variáveis de ambiente ou arquivo .env."""
    token = os.environ.get("ZOHO_REFRESH_TOKEN")
    if token:
        return token
    # fallback: tentar ler de arquivo .env ou outro local se necessário
    raise ZohoTokenError("Refresh token Zoho não encontrado nas variáveis de ambiente.")


def obter_access_token(force_refresh: bool = False) -> str:
    """Obtém o access token do Zoho Projects com cache in-memory."""
    global _ZOHO_TOKEN_CACHE
    now = time.time()

    if not force_refresh and _ZOHO_TOKEN_CACHE:
        token = _ZOHO_TOKEN_CACHE.get("token")
        expiry = _ZOHO_TOKEN_CACHE.get("expiry", 0)
        if token and expiry > now + 30:
            return token

    with _ZOHO_TOKEN_CACHE_LOCK:
        cache_data = _ZOHO_TOKEN_CACHE
        now_inside = time.time()
        if not force_refresh and cache_data:
            token = cache_data.get("token")
            expiry = cache_data.get("expiry", 0)
            if token and expiry > now_inside + 30:
                return token

        refresh_token = _ler_refresh_token()
        domain = _zoho_domain()
        token_host = f"https://accounts.zoho.{domain}" if domain != "com" else "https://accounts.zoho.com"
        token_url = f"{token_host}/oauth/v2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "refresh_token": refresh_token,
            "client_id": ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "grant_type": "refresh_token",
        }
        resp = requests.post(
            token_url,
            headers=headers,
            data=payload,
            timeout=30,
        )
        if not resp.ok:
            raise ZohoTokenError(
                f"Falha ao obter access token Zoho: {resp.status_code} {resp.text[:300]}"
            )
        data = resp.json() or {}
        access_token = data.get("access_token")
        expires_in = data.get("expires_in")
        if not access_token:
            raise ZohoTokenError("Resposta do Zoho sem access_token")
        try:
            expires_in_int = int(expires_in)
        except Exception:
            expires_in_int = 3600
        expiry_ts = now_inside + max(60, expires_in_int)
        _ZOHO_TOKEN_CACHE = {"token": access_token, "expiry": expiry_ts}
        return access_token
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import docx
import io
import re
from config import *

_ZOHO_TOKEN_CACHE: dict | None = None
_ZOHO_TOKEN_CACHE_LOCK = threading.Lock()

_MAPPINGS_CACHE = None


@lru_cache(maxsize=1)
def carregar_mapeamento_colunas() -> Dict[str, Dict[str, Any]]:
    """Carrega o arquivo JSON de mapeamento de colunas com cache em memória."""
    caminho = os.path.join(BASE_DIR, "mapeamento_colunas.json")
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo de mapeamento não encontrado: {caminho}")

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Arquivo de mapeamento inválido: {exc}")

    if not isinstance(dados, dict):
        raise ValueError("Estrutura do mapeamento deve ser um objeto JSON")

    return dados

# ====== UTILITÁRIOS: Atualização tolerante de planilha por coluna ======
def _get_sheet_headers(sheets_service, spreadsheet_id: str, sheet_name: str, header_row: int = 1):
    rng = f"'{sheet_name}'!A{header_row}:ZZ{header_row}"
    vals = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=rng
    ).execute().get('values', [[]])
    headers = (vals[0] if vals else [])
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"[DEBUG:_get_sheet_headers] range={rng}")
    logger.debug(f"[DEBUG:_get_sheet_headers] headers encontrados ({len(headers)}): {headers}")
    return headers, {h: i for i, h in enumerate(headers)}

def _find_row_by_cliente_tolerant(sheets_service, spreadsheet_id: str, sheet_name: str, header_cliente: str, chave: str):
    headers, hmap = _get_sheet_headers(sheets_service, spreadsheet_id, sheet_name, header_row=LINHA_CABECALHO)
    if header_cliente not in hmap:
        raise RuntimeError(f"Cabeçalho '{header_cliente}' não encontrado em {sheet_name}")
    col_letter = indice_para_letra_coluna(hmap[header_cliente])
    rng = f"'{sheet_name}'!{col_letter}{LINHA_CABECALHO+1}:{col_letter}"
    col_vals = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=rng
    ).execute().get('values', [])
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"[DEBUG:_find_row_by_cliente_tolerant] header_cliente='{header_cliente}', col_letter={col_letter}")
    logger.debug(f"[DEBUG:_find_row_by_cliente_tolerant] chave de busca='{chave}' (normalizada='{(chave or '').strip().lower()}')")
    alvo_norm = (chave or '').strip().lower()
    for idx, row in enumerate(col_vals, start=LINHA_CABECALHO+1):
        v = (row[0] if row else '').strip()
        if not v:
            continue
        txt = v.lower()
        if alvo_norm and (txt == alvo_norm or alvo_norm in txt or txt in alvo_norm):
            return idx
    # tentativa por código numérico antes do ' - '
    try:
        codigo = (chave or '').split(' - ')[0].strip()
        if codigo:
            for idx, row in enumerate(col_vals, start=LINHA_CABECALHO+1):
                v = (row[0] if row else '').strip()
                if v.startswith(codigo):
                    return idx
    except Exception:
        pass
    return None

def update_col_value_by_cliente_tolerant(sheets_service, cliente_chave: str, nome_coluna: str, valor):
    headers, hmap = _get_sheet_headers(sheets_service, ID_PLANILHA_PROJETOS, NOME_ABA_PLANILHA)
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"[DEBUG:update_col_value_by_cliente_tolerant] nome_coluna='{nome_coluna}', valor='{valor}'")
    logger.debug(f"[DEBUG:update_col_value_by_cliente_tolerant] cabeçalhos disponíveis: {headers}")
    if nome_coluna not in hmap:
        raise RuntimeError(f"Coluna '{nome_coluna}' não existe na planilha principal")
    linha = _find_row_by_cliente_tolerant(
        sheets_service, ID_PLANILHA_PROJETOS, NOME_ABA_PLANILHA, COLUNA_REFERENCIA_PARA_CONTAR_LINHAS, cliente_chave
    )
    if not linha:
        raise RuntimeError(f"Linha do cliente não encontrada para chave '{cliente_chave}'")
    col_letter = indice_para_letra_coluna(hmap[nome_coluna])
    rng = f"'{NOME_ABA_PLANILHA}'!{col_letter}{linha}"
    body = {'values': [[valor]]}
    logger.debug(f"[DEBUG:update_col_value_by_cliente_tolerant] range={rng}, body={body}")
    sheets_service.spreadsheets().values().update(
        spreadsheetId=ID_PLANILHA_PROJETOS, range=rng, valueInputOption='USER_ENTERED', body=body
    ).execute()

# ====== UTILITÁRIOS: Buscar IPv6 no Drive (via pasta Infraestrutura) ======
def buscar_ipv6_por_pasta(drive_service, pasta_cliente_id: str) -> str | None:
    """Procura subpasta 'Infraestrutura', encontra .docx sem 'broker' e extrai IPv6 (fd...)."""
    # 1) Encontrar subpasta Infraestrutura
    q_infra = (
        f"name = 'Infraestrutura' and mimeType = 'application/vnd.google-apps.folder' and '{pasta_cliente_id}' in parents and trashed = false"
    )
    res_infra = drive_service.files().list(q=q_infra, fields="files(id,name)").execute()
    items = res_infra.get('files', [])
    if not items:
        return None
    pasta_infra_id = items[0]['id']

    # 2) Listar .docx na pasta
    q_docx = (
        f"mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' and '{pasta_infra_id}' in parents and trashed = false"
    )
    res_docx = drive_service.files().list(q=q_docx, fields="files(id,name)").execute()
    files_docx = res_docx.get('files', [])
    alvo = None
    for f in files_docx:
        if 'broker' not in (f.get('name','').lower()):
            alvo = f
            break
    if not alvo:
        return None

    # 3) Baixar e ler .docx
    req = drive_service.files().get_media(fileId=alvo['id'])
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, req)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)

    document = docx.Document(fh)

    # 4) Procurar IPv6 nos parágrafos
    for para in document.paragraphs:
        txt = para.text or ''
        if 'vpn animati' in txt.lower():
            m = re.search(r'(fd[0-9a-fA-F:]+)', txt)
            if m:
                return m.group(1)

    # 5) Procurar IPv6 nas tabelas
    for t in document.tables:
        for row in t.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    txt = para.text or ''
                    if 'vpn animati' in txt.lower():
                        m = re.search(r'(fd[0-9a-fA-F:]+)', txt)
                        if m:
                            return m.group(1)
    return None

ZP_MENTION_PATTERN = re.compile(r'@\{([^}]+)\}')

def zoho_mention_token(usernum: str, name: str) -> str:
    return f"zp[@zpuser#{usernum}#{name}]zp"

def zoho_mention_by_name(name: str) -> str:
    info = ZOHO_MENTION_USERS.get(name)
    if not info:
        return name
    return zoho_mention_token(info.get("usernum", ""), info.get("name", name))

def zoho_mentions(names):
    if not names:
        return ""
    try:
        if isinstance(names, str):
            iterable = [names]
        else:
            iterable = list(names)
        tokens = []
        for n in iterable:
            if not n:
                continue
            tokens.append(zoho_mention_by_name(str(n).strip()))
        return " ".join(t for t in tokens if t)
    except Exception:
        return ""

def zoho_apply_mentions(template: str) -> str:
    if not template:
        return template
    def _replace(match):
        name = match.group(1).strip()
        token = zoho_mention_by_name(name)
        return token or name
    return ZP_MENTION_PATTERN.sub(_replace, template)

def build_google_credentials_from_session():
    info = session.get('credentials')
    if not info or not isinstance(info, dict):
        raise RuntimeError("Credenciais Google ausentes na sessão. Faça login novamente.")

    client_cfg = {}
    try:
        with open(CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f) or {}
            client_cfg = (data.get('installed') or data.get('web') or {})
    except Exception:
        client_cfg = {}

    info = dict(info)
    if not info.get('token_uri'):
        info['token_uri'] = 'https://oauth2.googleapis.com/token'
    if client_cfg:
        cid = client_cfg.get('client_id')
        csecret = client_cfg.get('client_secret')
        if cid and not info.get('client_id'):
            info['client_id'] = cid
        if csecret and not info.get('client_secret'):
            info['client_secret'] = csecret

    if 'token' not in info:
        info['token'] = None

    creds = Credentials(**info)

    try:
        if not creds.valid:
            if not creds.refresh_token:
                raise RuntimeError(
                    'As credenciais não contêm refresh_token. Refaça o login (com access_type="offline" e prompt="consent").'
                )
            creds.refresh(Request())
            session['credentials'] = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes,
            }
    except Exception as e:
        raise RuntimeError(f"Falha ao atualizar token Google: {e}")

    return creds

def _zoho_domain() -> str:
    return (os.environ.get("ZOHO_DOMAIN") or "com").strip()

def _zp_base() -> str:
    return f"https://projectsapi.zoho.{_zoho_domain()}/api/v3"

def _zp_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Accept": "application/json"
    }

def _portal_web_base(access_token: str) -> str | None:
    headers = _zp_headers(access_token)
    try:
        u1 = f"{_zp_base()}/portals"
        r = requests.get(u1, headers=headers, timeout=15)
        if r.ok:
            data = r.json()
            portals = data.get('portals') if isinstance(data, dict) else data
            for p in (portals or []):
                pid = str(p.get('id') or '')
                if pid == str(ZOHO_PORTAL_ID):
                    try:
                        web = (p.get('link') or {}).get('web') or None
                        if web:
                            return web if web.endswith('/') else web + '/'
                    except Exception:
                        pass
    except Exception:
        pass
    try:
        u2 = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}"
        r = requests.get(u2, headers=headers, timeout=15)
        if r.ok:
            data = r.json()
            portal = data.get('portal') if isinstance(data, dict) else None
            if isinstance(portal, dict):
                try:
                    web = (portal.get('link') or {}).get('web') or None
                    if web:
                        return web if web.endswith('/') else web + '/'
                except Exception:
                    return None
    except Exception:
        pass
    return None

def _projects_web_root() -> str:
    host = (ZOHO_PROJECTS_CUSTOM_WEB_HOST or '').strip().rstrip('/')
    if host:
        return f"{host}/portal/"
    base_api = _zp_base()
    if 'projectsapi.zoho.eu' in base_api:
        return 'https://projects.zoho.eu/portal/'
    if 'projectsapi.zoho.in' in base_api:
        return 'https://projects.zoho.in/portal/'
    if 'projectsapi.zoho.com.au' in base_api:
        return 'https://projects.zoho.com.au/portal/'
    if 'projectsapi.zoho.com.cn' in base_api:
        return 'https://projects.zoho.com.cn/portal/'
    return 'https://projects.zoho.com/portal/'

def _compose_tasklist_web_url(base_web: str, project_id: str, tasklist_id: str, custom_view_id: str | None = None) -> str:
    if not base_web.endswith('/'):
        base_web += '/'
    if custom_view_id:
        return (
            f"{base_web}#zp/projects/{project_id}/tasks/custom-view/{custom_view_id}/gantt/tasklist-detail/{tasklist_id}?group_by=milestone"
        )
    return f"{base_web}#myprojects/{project_id}/tasklists/{tasklist_id}"

def _parse_date_any(s: str | None):
    if not s:
        return None
    s = str(s).strip()
    if not s:
        return None
    try:
        # ISO formats with Z or offset
        if 'T' in s:
            iso = s.replace('Z', '+00:00')
            return datetime.fromisoformat(iso).date()
        # YYYY-MM-DD
        if len(s) == 10 and s[4] == '-' and s[7] == '-':
            return datetime.strptime(s, '%Y-%m-%d').date()
        # Try dd/mm/yyyy
        if '/' in s and len(s) >= 10:
            return datetime.strptime(s[:10], '%d/%m/%Y').date()
    except Exception:
        return None
    return None


def _fmt_dias(qtd: int | None) -> str:
    if qtd is None:
        return 'N/D'
    d = max(0, int(qtd))
    return f"{d} dia" if d == 1 else f"{d} dias"


def calcular_dias_total_projeto(start_date: str | None, created_time: str | None) -> str:
    base = _parse_date_any(start_date) or _parse_date_any(created_time)
    if not base:
        return 'N/D'
    today = date.today()
    return _fmt_dias((today - base).days)


def calcular_dias_na_fase(info_min: dict | None, coluna_hint: str | None = None) -> str:
    """
    DEPRECATED: Esta função calcula dias baseada em datas específicas de cada fase.
    Use calcular_dias_na_fase_from_status() para cálculo preciso baseado em data_mudanca_status.
    """
    info_min = info_min or {}
    # Escolhe a melhor data conforme a coluna quando disponível
    cand = None
    h = (coluna_hint or '').strip().lower()
    if h == 'em homologação':
        cand = _parse_date_any(info_min.get('data_homologacao'))
    elif h == 'em virada':
        cand = _parse_date_any(info_min.get('data_virada'))
    elif h == 'em operação assistida':
        cand = _parse_date_any(info_min.get('data_inicio_oa'))
    elif h == 'aguardando cronograma' or h == 'em andamento - implantação':
        cand = _parse_date_any(info_min.get('data_inicio_implantacao')) or _parse_date_any(info_min.get('data_inicio'))
    elif h == 'aguardando encerramento':
        cand = _parse_date_any(info_min.get('data_homologacao'))
    elif h == 'falta liberar servidor infra' or h == 'aguardando onboarding':
        cand = _parse_date_any(info_min.get('data_criacao'))

    # Fallback genérico
    if not cand:
        cand = _parse_date_any(info_min.get('data_inicio')) or _parse_date_any(info_min.get('data_criacao'))
    if not cand:
        return 'N/D'
    today = date.today()
    return _fmt_dias((today - cand).days)


def calcular_dias_na_fase_from_status(data_mudanca_status: str | None) -> str:
    """
    Calcula dias na fase atual baseado na data_mudanca_status.
    Esta é a função RECOMENDADA para cálculo preciso de dias na fase.
    
    Args:
        data_mudanca_status: Data da última mudança de status (formato: YYYY-MM-DD)
    
    Returns:
        String formatada: "Hoje", "1d", "2d", etc. ou "N/D" se data não disponível
    
    Examples:
        >>> calcular_dias_na_fase_from_status("2025-10-13")  # Se hoje é 2025-10-13
        "Hoje"
        >>> calcular_dias_na_fase_from_status("2025-10-12")  # Se hoje é 2025-10-13
        "1d"
        >>> calcular_dias_na_fase_from_status("2025-10-11")  # Se hoje é 2025-10-13
        "2d"
    """
    if not data_mudanca_status:
        return 'N/D'
    
    data_base = _parse_date_any(data_mudanca_status)
    if not data_base:
        return 'N/D'
    
    hoje = date.today()
    dias = (hoje - data_base).days
    
    if dias < 0:
        return 'Futuro'
    elif dias == 0:
        return 'Hoje'
    else:
        return f"{dias}d"


def determinar_coluna_projeto(projeto: dict) -> str:
    try:
        status_id = str(((projeto or {}).get('status') or {}).get('id') or '')
        status_nm = str(((projeto or {}).get('status') or {}).get('name') or '').strip().lower()
        tags = [str(t.get('id') or '') for t in (projeto.get('tags') or [])]

        # Estados finais primeiro
        if status_id == STATUS_CANCELADO_ID or status_nm == 'cancelado':
            return 'Cancelado'
        if status_id == STATUS_FINALIZADO_ID or status_nm == 'finalizado' or (projeto.get('is_completed') is True):
            return 'Finalizado'

        # Tags de controle de fase
        if TAG_PARADO_ID in tags:
            return 'Projeto Parado'
        if TAG_AGUARDANDO_ENCERRAMENTO_ID in tags:
            return 'Aguardando Encerramento'
        if status_id == STATUS_OPERACAO_ASSISTIDA_ID:
            return 'Em Operação Assistida'
        if TAG_EM_VIRADA_ID in tags:
            return 'Em Virada'
        if TAG_EM_HOMOLOGACAO_ID in tags:
            return 'Em Homologação'
        if TAG_AGUARDANDO_INFRA_ID in tags:
            return 'Falta Liberar Servidor Infra'
        if TAG_AGUARDANDO_ONBOARDING_ID in tags:
            return 'Aguardando Onboarding'

        # Status padrão
        if status_id in {STATUS_EM_ANDAMENTO_ID, STATUS_ABERTO_ID} or status_nm in {'aguardando cronograma', 'aberto'}:
            return 'Aguardando Cronograma'
    except Exception:
        pass
    return 'Status Desconhecido'


def _zp_project_url(project_id: str) -> str:
    return f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"


def _zp_project_custom_fields_url(project_id: str) -> str:
    return f"{_zp_project_url(project_id)}/customfields"


def _zp_project_tags_url(project_id: str) -> str:
    return f"{_zp_project_url(project_id)}/tags"


def set_project_status(project_id: str, status_id: str, access_token: str) -> bool:
    if not project_id or not status_id:
        raise ValueError("project_id e status_id são obrigatórios")
    url = _zp_project_url(project_id)
    payload = {"custom_status": status_id}
    headers = _zp_headers(access_token)
    headers["Content-Type"] = "application/json"
    import logging
    logger = logging.getLogger(__name__)
    try:
        resp = requests.patch(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            logger.info(f"Status do projeto {project_id} atualizado para {status_id}")
            return True
        logger.warning(f"Falha ao atualizar status do projeto {project_id}: {resp.status_code} - {resp.text[:400]}")
    except Exception as exc:
        logger.error(f"Exceção ao atualizar status do projeto {project_id}: {exc}")
    return False


def set_project_custom_fields(project_id: str, custom_fields: Dict[str, Any], access_token: str) -> bool:
    if not project_id or not custom_fields:
        return True
    url = _zp_project_custom_fields_url(project_id)
    headers = _zp_headers(access_token)
    headers["Content-Type"] = "application/json"
    payload = {"custom_fields": custom_fields}
    import logging
    logger = logging.getLogger(__name__)
    try:
        resp = requests.put(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            logger.info(f"Custom fields do projeto {project_id} atualizados: {list(custom_fields.keys())}")
            return True
        logger.warning(f"Falha ao atualizar custom fields do projeto {project_id}: {resp.status_code} - {resp.text[:400]}")
    except Exception as exc:
        logger.error(f"Exceção ao atualizar custom fields do projeto {project_id}: {exc}")
    return False


def set_project_tags_exact(project_id: str, tags_to_add: List[str], access_token: str) -> bool:
    tags_to_add = [str(t).strip() for t in (tags_to_add or []) if str(t).strip()]
    url = _zp_project_tags_url(project_id)
    headers = _zp_headers(access_token)
    headers["Content-Type"] = "application/json"
    payload = {"tags": tags_to_add}
    import logging
    logger = logging.getLogger(__name__)
    try:
        resp = requests.put(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            logger.info(f"Tags do projeto {project_id} definidas como: {tags_to_add}")
            return True
        logger.warning(f"Falha ao definir tags do projeto {project_id}: {resp.status_code} - {resp.text[:400]}")
    except Exception as exc:
        logger.error(f"Exceção ao definir tags do projeto {project_id}: {exc}")
    return False


def sync_project_tags_delta(project_id: str, tags_to_add: List[str], tags_to_remove: List[str], access_token: str) -> bool:
    add = [str(t).strip() for t in (tags_to_add or []) if str(t).strip()]
    remove = [str(t).strip() for t in (tags_to_remove or []) if str(t).strip()]
    if not add and not remove:
        return True
    url = _zp_project_tags_url(project_id)
    headers = _zp_headers(access_token)
    headers["Content-Type"] = "application/json"
    payload = {"tags_to_add": add, "tags_to_remove": remove}
    import logging
    logger = logging.getLogger(__name__)
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            logger.info(f"Tags do projeto {project_id} atualizadas (add={add}, remove={remove})")
            return True
        logger.warning(f"Falha ao atualizar tags do projeto {project_id}: {resp.status_code} - {resp.text[:400]}")
    except Exception as exc:
        logger.error(f"Exceção ao atualizar tags do projeto {project_id}: {exc}")
    return False


def post_project_comment(project_id: str, message: str, access_token: str) -> bool:
    if not project_id or not message:
        return False
    url = f"{_zp_project_url(project_id)}/comments"
    headers = _zp_headers(access_token)
    headers.update({"Content-Type": "application/json", "Accept": "application/json"})
    payload = {"content": str(message)}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            print(f"INFO: Comentário de projeto criado para {project_id}")
            return True
        print(f"WARN: Falha ao comentar projeto {project_id}: {resp.status_code} - {resp.text[:400]}")
    except Exception as exc:
        print(f"ERROR: Exceção ao comentar projeto {project_id}: {exc}")
    return False


def post_task_comment(project_id: str, task_id: str, message: str, access_token: str) -> bool:
    if not project_id or not task_id or not message:
        return False
    base = _zp_project_url(project_id)
    url = f"{base}/tasks/{task_id}/comments"
    headers = _zp_headers(access_token)
    headers.update({"Content-Type": "application/json", "Accept": "application/json"})
    payload = {"content": str(message)}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            print(f"INFO: Comentário adicionado na tarefa {task_id} do projeto {project_id}")
            return True
        print(f"WARN: Falha ao comentar tarefa {task_id} do projeto {project_id}: {resp.status_code} - {resp.text[:400]}")
    except Exception as exc:
        print(f"ERROR: Exceção ao comentar tarefa {task_id} do projeto {project_id}: {exc}")
    return False


def disparar_workflow(project_id: str, workflow_name: str, payload: dict | None, access_token: str) -> bool:
    if not project_id or not workflow_name:
        return False
    url = f"{_zp_project_url(project_id)}/workflows/{workflow_name}/trigger"
    headers = _zp_headers(access_token)
    headers["Content-Type"] = "application/json"
    try:
        resp = requests.post(url, headers=headers, json=payload or {}, timeout=30)
        if resp.status_code in (200, 201, 202):
            print(f"INFO: Workflow '{workflow_name}' disparado para projeto {project_id}")
            return True
        print(f"WARN: Falha ao disparar workflow '{workflow_name}' no projeto {project_id}: {resp.status_code} - {resp.text[:400]}")
    except Exception as exc:
        print(f"ERROR: Exceção ao disparar workflow '{workflow_name}' no projeto {project_id}: {exc}")
    return False


def obter_task_id_por_nome(project_id: str, task_name: str, access_token: str) -> str | None:
    if not project_id or not task_name:
        return None
    url = f"{_zp_project_url(project_id)}/tasks"
    headers = _zp_headers(access_token)
    params = {
        "status": "all",
        "range": "1-200",
        "sort_column": "created_time",
        "sort_order": "ascending",
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        tasks = data.get("tasks") if isinstance(data, dict) else []
        normalized_target = _normalize_task_name(task_name)
        for task in tasks or []:
            nome = (task.get("name") or "").strip()
            if not nome:
                continue
            if _normalize_task_name(nome) == normalized_target:
                return str(task.get("id")) if task.get("id") is not None else None
    except Exception as exc:
        print(f"WARN: Falha ao localizar task '{task_name}' no projeto {project_id}: {exc}")
    return None


def _normalize_task_name(name: str) -> str:
    try:
        base = (name or "").strip().lower()
        base = re.sub(r"^\s*\d+(?:\.\d+)*\s*-\s*", "", base)
        base = " ".join(base.split())
        return base
    except Exception:
        return name or ""


def obter_access_token() -> str:
    if not os.path.exists(ZOHO_TOKEN_PATH):
        raise FileNotFoundError(f"Arquivo de refresh token não encontrado: {ZOHO_TOKEN_PATH}")
    refresh_token = (open(ZOHO_TOKEN_PATH, 'r', encoding='utf-8').read()).strip()
    if not refresh_token:
        raise RuntimeError("Refresh token vazio em zoho_refresh_token.txt")
    if not ZOHO_CLIENT_ID or not ZOHO_CLIENT_SECRET:
        raise RuntimeError("ZOHO_CLIENT_ID/ZOHO_CLIENT_SECRET não definidos")

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


def obter_access_token_zoho() -> str:
    # Alias compatível com chamadas existentes
    return obter_access_token()


def avaliar_campos_personalizados(info_dest: dict | None) -> dict:
    """Resolve marcadores especiais como CURRENT_DATE antes de enviar ao Zoho."""
    resolved: dict[str, Any] = {}
    for chave, valor in (info_dest or {}).items():
        if not chave:
            continue
        if isinstance(valor, str) and valor.upper() == "CURRENT_DATE":
            resolved[chave] = date.today().strftime("%Y-%m-%d")
        else:
            resolved[chave] = valor
    return resolved

def criar_estrutura_no_drive(drive_service, dados):
    try:
        produto_map = {"netRIS": "1", "AnimatiPACS": "2", "netRIS e AnimatiPACS": "3"}
        produto_id = produto_map.get(dados['produto'], "2")
        id_pasta_pai = ID_PASTA_PAI_NETRIS if produto_id in ['1', '3'] else ID_PASTA_PAI_ANIMATIPACS
        nome_pasta_cliente = construir_titulo_projeto(dados)
        print(f"INFO: Criando pasta no Drive: {nome_pasta_cliente}")
        query = (
            "name = '" + nome_pasta_cliente.replace("'", "'" ) + "' and "
            "mimeType = 'application/vnd.google-apps.folder' and "
            f"'{id_pasta_pai}' in parents and trashed = false"
        )
        existentes = drive_service.files().list(q=query, fields="files(id, webViewLink)",pageSize=1).execute().get('files', [])
        if existentes:
            print("AVISO: Pasta já existe. Reutilizando pasta existente.")
            id_pasta_cliente, link_pasta_cliente = existentes[0]['id'], existentes[0]['webViewLink']
        else:
            file_metadata = {'name': nome_pasta_cliente, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [id_pasta_pai]}
            pasta_cliente = drive_service.files().create(body=file_metadata, fields='id, webViewLink').execute()
            id_pasta_cliente, link_pasta_cliente = pasta_cliente.get('id'), pasta_cliente.get('webViewLink')
        dados['link_google'] = link_pasta_cliente
        subpastas = {'Implantação': '', 'Infraestrutura': '', 'Suporte': '', 'CS': ''}
        if dados['importacao'] == 's':
            subpastas['Importação'] = ''
        for nome_subpasta in subpastas:
            q_sub = (
                "name = '" + nome_subpasta.replace("'", "'" ) + "' and "
                "mimeType = 'application/vnd.google-apps.folder' and "
                f"'{id_pasta_cliente}' in parents and trashed = false"
            )
            existentes_sub = drive_service.files().list(q=q_sub, fields="files(id)",pageSize=1).execute().get('files', [])
            if existentes_sub:
                subpastas[nome_subpasta] = existentes_sub[0]['id']
            else:
                subpasta_metadata = {'name': nome_subpasta, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [id_pasta_cliente]}
                subpasta = drive_service.files().create(body=subpasta_metadata, fields='id').execute()
                subpastas[nome_subpasta] = subpasta.get('id')
        print("INFO: Fazendo upload dos arquivos para o Google Drive...")
        media_deip = MediaFileUpload(dados['caminho_deip'], mimetype='application/pdf')
        deip_metadata = {'name': os.path.basename(dados['caminho_deip_original']), 'parents': [subpastas['Implantação']]} 
        drive_service.files().create(body=deip_metadata, media_body=media_deip, fields='id').execute()
        nome_cliente = dados['nome_cliente']
        templates_para_upload = {
            "Protocolo de Implantação.docx": {'pasta': 'Implantação', 'nome_final': f"Protocolo de Implantação - {nome_cliente}.docx"},
            "Documento DPI.docx": {'pasta': 'Implantação', 'nome_final': f"Documento DPI - {nome_cliente}.docx"},
            "Definição_Cronograma_Homologação.docx": {'pasta': 'Implantação', 'nome_final': f"Definição_Cronograma_Homologação - {nome_cliente}.docx"},
        }
        if dados['importacao'] == 's':
            templates_para_upload["Formulário de Importação.docx"] = {'pasta': 'Importação', 'nome_final': f"Formulário de Importação - {nome_cliente}.docx"}
        for template_original, info in templates_para_upload.items():
            caminho_template = os.path.join(TEMPLATE_DOCS_PATH, template_original)
            if os.path.exists(caminho_template):
                try:
                    metadata = {'name': info['nome_final'], 'parents': [subpastas[info['pasta']]]}
                    media = MediaFileUpload(caminho_template, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    created = drive_service.files().create(body=metadata, media_body=media, fields='id, name, parents').execute()
                    print(f"INFO: Template upado: {template_original} -> {info['pasta']} ({created.get('id')})")
                except HttpError as e:
                    print(f"AVISO: Falha ao upar template '{template_original}': {e}")
            else:
                print(f"AVISO: Arquivo de template não encontrado: {caminho_template}")
        return link_pasta_cliente
    except (HttpError, FileNotFoundError) as error:
        raise Exception(f"Erro no Google Drive: {error}")

def indice_para_letra_coluna(n):
    string = ""
    while n >= 0:
        string = chr(n % 26 + 65) + string
        n = n // 26 - 1
    return string

def atualizar_planilha_principal(sheets_service, dados, url_pasta_drive):
    try:
        print("INFO: Atualizando planilha principal...")
        range_cabecalho = f"'{NOME_ABA_PLANILHA}'!A{LINHA_CABECALHO}:ZZ{LINHA_CABECALHO}"
        cabecalhos = sheets_service.spreadsheets().values().get(spreadsheetId=ID_PLANILHA_PROJETOS, range=range_cabecalho).execute().get('values', [[]])[0]
        mapa_colunas = {cabecalho: i for i, cabecalho in enumerate(cabecalhos)}
        primeiro_nome_gp = dados['gp_selecionado'].split()[0]
        letra_coluna_ref = indice_para_letra_coluna(mapa_colunas[COLUNA_REFERENCIA_PARA_CONTAR_LINHAS])
        range_coluna_ref = f"'{NOME_ABA_PLANILHA}'!{letra_coluna_ref}{LINHA_CABECALHO+1}:{letra_coluna_ref}"
        valores_col_ref = sheets_service.spreadsheets().values().get(
            spreadsheetId=ID_PLANILHA_PROJETOS,
            range=range_coluna_ref
        ).execute().get('values', [])
        proxima_linha_vazia = (LINHA_CABECALHO + len(valores_col_ref) + 1)

        data_selecionada_formatada = dados['start_date'].replace('-', '/')
        if dados.get('integracao_status') == 's':
            integracao_texto = dados.get('integracao_nome') or 'Possui'
        else:
            integracao_texto = 'Não possui'

        # Ajuste do valor exibido na coluna Produtos mantendo o dropdown: usar o texto "AnimatiPACS/netRIS" quando houver ambos
        produtos_display = dados.get('produto')
        if produtos_display == 'netRIS e AnimatiPACS':
            produtos_display = 'AnimatiPACS/netRIS'

        dados_para_inserir = {
            "Cliente": dados['codigo_contrato_numero'] + ' - ' + dados['nome_cliente'],
            "Cidade": dados['cidade'],
            "Estado": dados['estado'],
            "Link": f'=HYPERLINK("{url_pasta_drive}"; "DOC")',
            "GP": primeiro_nome_gp,
            "Produtos": produtos_display,
            "Projetos": "Cliente Novo",
            "Status Principal": "Aguardando Onboarding",
            "Rec. DEIP": data_selecionada_formatada,
            "Integração": integracao_texto,
            "Importação": "Contratado" if dados['importacao'] == 's' else "Não Contratado"
        }
        data_to_update = []
        for nome_coluna, valor in dados_para_inserir.items():
            if nome_coluna in mapa_colunas:
                letra_coluna = indice_para_letra_coluna(mapa_colunas[nome_coluna])
                range_celula = f"'{NOME_ABA_PLANILHA}'!{letra_coluna}{proxima_linha_vazia}"
                data_to_update.append({'range': range_celula, 'values': [[valor]]})
        body = {'valueInputOption': 'USER_ENTERED', 'data': data_to_update}
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=ID_PLANILHA_PROJETOS, body=body).execute()
        return True
    except HttpError as error:
        raise Exception(f"Erro no Google Sheets: {error}")

def atualizar_planilha_secundaria(sheets_service, dados):
    try:
        print("INFO: Atualizando planilha secundária...")
        sheet_id, sheet_name = ID_PLANILHA_PROJETOS_SECUNDARIA, NOME_ABA_PLANILHA_SECUNDARIA
        range_cabecalho = f"'{sheet_name}'!1:1"
        cabecalhos = sheets_service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_cabecalho).execute().get('values', [[]])[0]
        mapa_colunas = {cabecalho: i for i, cabecalho in enumerate(cabecalhos)}
        letra_coluna_ref = indice_para_letra_coluna(mapa_colunas[COLUNA_REFERENCIA_SECUNDARIA])
        range_coluna_ref = f"'{sheet_name}'!{letra_coluna_ref}:{letra_coluna_ref}"
        proxima_linha_vazia = len(sheets_service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_coluna_ref).execute().get('values', [])) + 1
        novo_num_sequencial = proxima_linha_vazia - 1
        sistema = 'NR/AP' if dados['produto'] == 'netRIS e AnimatiPACS' else ('NR' if dados['produto'] == 'netRIS' else 'AP')
        mapeamento = {
            COLUNA_SEQUENCIAL_SECUNDARIA: novo_num_sequencial,
            "Recebido": dados['start_date'].replace('-', '/'),
            "Cód CS": dados['codigo_contrato'],
            "Cliente": dados['nome_cliente'],
            "Cidade": f"{dados['cidade']} - {dados['estado']}",
            "Sistema": sistema,
            "GP": dados['gp_selecionado'].split()[0],
            "Concorrente": dados['concorrente'],
        }
        linha_final = [''] * len(cabecalhos)
        for nome_coluna, valor in mapeamento.items():
            if nome_coluna in mapa_colunas:
                linha_final[mapa_colunas[nome_coluna]] = valor
        body = {'values': [linha_final]}
        range_para_escrever = f"'{sheet_name}'!A{proxima_linha_vazia}"
        sheets_service.spreadsheets().values().append(spreadsheetId=sheet_id, range=range_para_escrever, valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS", body=body).execute()
        return True
    except HttpError as error:
        raise Exception(f"Erro na Planilha Secundária: {error}")

def obter_access_token_zoho():
    return obter_access_token()

def sincronizar_projeto_individual(access_token: str, project_id: str) -> dict | None:
    """Busca um projeto específico no Zoho e aplica o mesmo formato usado no Kanban."""
    if not project_id:
        return None

    try:
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
        params = {
            "fields": "id,name,owner,client_company,client,start_date,created_time,status,tags"
        }
        resp = requests.get(url, headers=_zp_headers(access_token), params=params, timeout=25)
        resp.raise_for_status()
        projeto = resp.json() if resp.text else {}
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao buscar projeto {project_id}: {e.response.text if e.response else e}")
        return None
    except Exception as e:
        print(f"ERRO inesperado ao sincronizar projeto {project_id}: {e}")
        return None

    if not isinstance(projeto, dict) or not projeto.get('id'):
        print(f"AVISO: Resposta do Zoho sem dados válidos para o projeto {project_id}: {projeto}")
        return None

    cliente = (
        (projeto.get('client_company') or {}).get('name')
        or (projeto.get('client') or {}).get('name')
        or projeto.get('client_name')
        or "Cliente não informado"
    )

    status_kanban = determinar_coluna_projeto(projeto)
    nome_projeto = projeto.get('name', '')
    produto_info = ''
    if ' - NR/AP' in nome_projeto:
        produto_info = 'netRIS e AnimatiPACS'
    elif ' - NR' in nome_projeto:
        produto_info = 'netRIS'
    elif ' - AP' in nome_projeto:
        produto_info = 'AnimatiPACS'

    info_projeto = {
        'id': str(projeto.get('id')) if projeto.get('id') is not None else None,
        'nome': nome_projeto,
        'cliente': cliente,
        'gp': (projeto.get('owner') or {}).get('name', 'GP não informado'),
        'data_inicio': projeto.get('start_date', ''),
        'data_criacao': projeto.get('created_time', ''),
        'data_inicio_formatada': projeto.get('start_date', ''),
        'dias_total': calcular_dias_total_projeto(projeto.get('start_date', ''), projeto.get('created_time', '')),
        'status_atual': status_kanban,
        'produto': produto_info
    }

    # Calcula dias na fase usando os mesmos critérios do carregamento completo
    try:
        info_projeto['dias_na_fase'] = calcular_dias_na_fase(
            info_projeto,
            status_kanban,
            project_id=project_id,
            access_token=access_token
        )
    except TypeError:
        # Compatibilidade com versões anteriores que usavam uma assinatura menor
        try:
            info_projeto['dias_na_fase'] = calcular_dias_na_fase(info_projeto, status_kanban)
        except Exception as e:
            print(f"AVISO: Falha ao calcular dias na fase para {project_id}: {e}")
            info_projeto['dias_na_fase'] = 'N/D'
    except Exception as e:
        print(f"AVISO: Falha ao calcular dias na fase para {project_id}: {e}")
        info_projeto['dias_na_fase'] = 'N/D'

    return info_projeto

def construir_titulo_projeto(dados):
    sufixo_map = {
        "netRIS": "NR",
        "AnimatiPACS": "AP",
        "netRIS e AnimatiPACS": "NR/AP",
        "AnimatiPACS/netRIS": "NR/AP",
    }
    sufixo = sufixo_map.get(dados['produto'], "")
    return f"{dados['codigo_contrato_numero']} - {dados['nome_cliente']} - {sufixo}"

def construir_descricao(dados):
    pacs_check = "[X]" if 'PACS' in dados['produto'] else "[ ]"; ris_check = "[X]" if 'RIS' in dados['produto'] else "[ ]"
    servidor_local = "(X)" if dados['servidor'] == 'Local' else "( )"; servidor_cloud_animati = "(X)" if dados['servidor'] == 'Cloud Animati' else "( )"; servidor_cloud_terceiros = "(X)" if dados['servidor'] == 'Cloud Terceiros' else "( )"
    integracao_sim = "(X)" if dados['integracao_status'] == 's' else "( )"; integracao_nao = "( )" if dados['integracao_status'] == 's' else "(X)"
    importacao_sim = "(X)" if dados['importacao'] == 's' else "( )"; importacao_nao = "( )" if dados['importacao'] == 's' else "(X)"
    detalhes_integracao = ""
    if dados['integracao_status'] == 's':
        worklist_check = "[X]" if dados['integ_worklist'] else "[ ]";
        laudos_check = "[X]" if dados['integ_laudos'] else "[ ]";
        lab_check = "[X]" if dados['integ_lab'] else "[ ]";
        telerad_check = "[X]" if dados.get('integ_teleradiologia') else "[ ]";
        outros_check = "[X]" if dados['integ_outros'] else "[ ]";
        detalhes_integracao = f"<p><b>Se Sim, selecione as integrações:</b></p><ul><li>{worklist_check} Worklist</li><li>{laudos_check} Retorno de Laudo</li><li>{lab_check} Laboratório</li><li>{telerad_check} Teleradiologia</li><li>{outros_check} Outros</li></ul>"
    detalhes_importacao = ""
    if dados['importacao'] == 's':
        cadastros_check = "[X]" if dados['import_cadastros'] else "[ ]"; prontuarios_check = "[X]" if dados['import_prontuarios'] else "[ ]"; laudos_check = "[X]" if dados['import_laudos'] else "[ ]"; imagens_check = "[X]" if dados['import_imagens'] else "[ ]"
        detalhes_importacao = f"<p><b>Se Sim, selecione os itens para importação:</b></p><ul><li>{cadastros_check} Cadastros</li><li>{prontuarios_check} Prontuários</li><li>{laudos_check} Laudos</li><li>{imagens_check} Imagens</li></ul>"
    obs_texto = ""
    if dados['observacoes'] and dados['observacoes'].strip():
        obs_formatado = dados['observacoes'].strip().replace('\\n', '<br>')
        obs_texto = f"<p><b>Observações Adicionais:</b></p><p>{obs_formatado}</p>"
    descricao_html = f"<h2>Descrição do Projeto</h2><p><b>Ferramentas Contratadas:</b></p><ul><li>{pacs_check} AnimatiPACS</li><li>{ris_check} netRIS</li><li>[ ] netPACS</li></ul><p><b>Servidor:</b></p><ul><li>{servidor_local} Local</li><li>{servidor_cloud_animati} Cloud Animati</li><li>{servidor_cloud_terceiros} Cloud Terceiros</li></ul><p><b>Haverá integração?</b></p><ul><li>{integracao_sim} Sim</li><li>{integracao_nao} Não</li></ul>{detalhes_integracao}<p><b>Haverá importação?</b></p><ul><li>{importacao_sim} Sim</li><li>{importacao_nao} Não</li></ul>{detalhes_importacao}<p><b>Link da pasta do Google:</b></p><p>{dados.get('link_google', 'Link não gerado')}</p>{obs_texto}"
    return " ".join(descricao_html.split())

def escolher_template_zoho(dados):
    produto, importacao, integracao = dados['produto'], dados['importacao'] == 's', dados['integracao_status'] == 's'
    print(f"INFO: Selecionando modelo para: {produto}, Importação={importacao}, Integração={integracao}")
    if produto == 'netRIS':
        if importacao and integracao: return MODELOS_ZOHO.get("Implantação RIS (COM importação e COM integração)")
        if importacao and not integracao: return MODELOS_ZOHO.get("Implantação RIS (COM importação e SEM integração)")
        return MODELOS_ZOHO.get("Implantação RIS (SEM importação e SEM integração)")
    if produto == 'AnimatiPACS':
        if importacao and integracao: return MODELOS_ZOHO.get("Implantação PACS ( IMPORTAÇÃO + INTEGRAÇÃO) - UNIFICADO FINAL")
        if importacao and not integracao: return MODELOS_ZOHO.get("Implantação PACS (COM importação e SEM integração) - UNIFICADO FINAL")
        if not importacao and integracao: return MODELOS_ZOHO.get("Implantação PACS (COM integração e SEM importação) - Unificado FINAL")
        return MODELOS_ZOHO.get("Implantação PACS (SEM importação e SEM integração) - UNIFICADO FINAL")
    if produto in ('netRIS e AnimatiPACS', 'AnimatiPACS/netRIS'):
        if importacao: return MODELOS_ZOHO.get("Implantação RIS + PACS (COM importação) - UNIFICADO Final")
        return MODELOS_ZOHO.get("Implantação RIS + PACS (SEM importação ) - UNIFICADO FINAL")
    print("AVISO: Nenhum modelo Zoho para este cenário.")
    return None

def criar_projeto_no_zoho(access_token, dados, template_id):
    print(f"INFO: Criando projeto Zoho para '{dados['nome_cliente']}'...")
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    # Converte a data de início para o formato da API
    try:
        start_date_obj = datetime.strptime(dados['start_date'], '%d-%m-%Y')
        start_date_api_format = start_date_obj.strftime('%Y-%m-%d')
    except ValueError:
        start_date_api_format = date.today().strftime("%Y-%m-%d")

    # Mapeia soluções contratadas para o texto esperado
    produto = dados.get('produto', '')
    if produto in ('netRIS e AnimatiPACS', 'AnimatiPACS/netRIS'):
        solucoes_contratadas = 'AnimatiPACS/netRIS'
    elif produto == 'netRIS':
        solucoes_contratadas = 'netRIS'
    elif produto == 'AnimatiPACS':
        solucoes_contratadas = 'AnimatiPACS'
    else:
        solucoes_contratadas = str(produto or '')

    # Monta lista de importações selecionadas (multi-select)
    importacoes_list = []
    if dados.get('import_imagens'):
        importacoes_list.append({"id": "2376502000005584872", "value": "Imagens"})
    if dados.get('import_prontuarios'):
        importacoes_list.append({"id": "2376502000005584866", "value": "Prontuários"})
    if dados.get('import_cadastros'):
        importacoes_list.append({"id": "2376502000005584868", "value": "Cadastros"})
    if dados.get('import_laudos'):
        importacoes_list.append({"id": "2376502000005584870", "value": "Laudos"})

    # Converte data de virada (se informada no formulário)
    data_virada_fmt = None
    raw_virada = dados.get('data_de_virada') or dados.get('data_virada')
    if raw_virada:
        for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y'):
            try:
                data_vir = datetime.strptime(raw_virada, fmt)
                data_virada_fmt = data_vir.strftime('%Y-%m-%d')
                break
            except Exception:
                continue

    # Campos customizados do projeto
    custom_fields = {
        "havera_integracao": bool(dados.get('integracao_status') == 's'),
        "solucoes_contratadas": solucoes_contratadas,
        "link_do_google": dados.get('link_google') or dados.get('link_google_drive') or dados.get('link'),
        "importacoes": importacoes_list,
        "havera_importacao": "Sim" if dados.get('importacao') == 's' else "Não",
    }
    if data_virada_fmt:
        custom_fields["data_de_virada"] = data_virada_fmt

    # Integrações (multi-select)
    if dados.get('integracao_status') == 's':
        integracoes_list = []
        if dados.get('integ_worklist'):
            integracoes_list.append({"id": "2376502000005584852", "value": "Worklist"})
        if dados.get('integ_laudos'):
            integracoes_list.append({"id": "2376502000005584854", "value": "Retorno de Laudo"})
        if dados.get('integ_lab'):
            integracoes_list.append({"id": "2376502000005584856", "value": "Laboratório"})
        if dados.get('integ_teleradiologia'):
            integracoes_list.append({"id": "2376502000005584858", "value": "Teleradiologia"})
        if dados.get('integ_outros'):
            integracoes_list.append({"id": "2376502000005584860", "value": "Outros"})
        custom_fields["integracoes"] = integracoes_list

    payload = {
        "name": construir_titulo_projeto(dados),
        "description": construir_descricao(dados),
        "start_date": start_date_api_format,
        "copy_from": str(template_id),
        "project_type": "active",
        "project_group": {
            "id": GRUPOS_ZOHO.get(
                "Hibrido" if ("e" in dados.get('produto', '') or dados.get('produto') == 'AnimatiPACS/netRIS') else ("RIS" if "RIS" in dados.get('produto', '') else "PACS")
            )
        },
        "layout": {"id": "2376502000005584766"},
        "owner": {"zpuid": DONOS_PROJETO[dados['gp_selecionado']]},
        "is_rollup_project": True,
        "tags": [{"id": 2376502000001291513}],
        "custom_fields": custom_fields,
    }

    try:
        # 1) Cria o projeto já com campos customizados
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        projeto_criado = response.json() if response.text else {}
        id_do_projeto = projeto_criado.get('id')
        if not id_do_projeto:
            raise Exception(f"Resposta do Zoho OK, mas sem ID do projeto: {projeto_criado}")
        print(f"INFO: Projeto Zoho '{projeto_criado.get('name')}' criado!")

        # 2) Reforço: aplica/atualiza custom fields via PATCH (alguns tenants exigem update separado)
        try:
            url_patch = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{id_do_projeto}"
            patch_payload = {"custom_fields": custom_fields}
            resp_patch = requests.patch(url_patch, headers=headers, json=patch_payload, timeout=30)
            if resp_patch.status_code not in (200, 201):
                print(f"AVISO: PATCH de custom_fields retornou {resp_patch.status_code}: {resp_patch.text[:500]}")
        except Exception as e:
            print(f"AVISO: Falha no PATCH de custom_fields: {e}")

        # A aplicação de tags complementares será garantida posteriormente via ensure_project_tags
        return id_do_projeto
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro da API Zoho: {e.response.text if e.response else e}")

def processar_tarefas_iniciais(access_token, project_id, gp_zpuid):
    """
    - Conclui tarefas iniciais definidas em TAREFAS_PARA_CONCLUIR
    - Atribui o dono (GP) para tarefas definidas em TAREFAS_PARA_ATRIBUIR
    - Tenta garantir a tag de 'Aguardando Onboarding' no projeto
    """
    try:
        # Concluir tarefas específicas
        for nome in TAREFAS_PARA_CONCLUIR:
            try:
                tid = find_task_by_name(access_token, project_id, nome)
                if tid:
                    concluir_tarefa(access_token, project_id, tid)
                    tempo = TEMPO_RELATO.get(nome)
                    if tempo:
                        try:
                            add_comment_to_task(access_token, project_id, tid, f"Tarefa concluída automaticamente. Tempo estimado: {tempo}.")
                        except Exception:
                            pass
            except Exception as e:
                print(f"AVISO: Falha ao concluir '{nome}': {e}")

        # Atribuir GP às tarefas específicas
        for nome in TAREFAS_PARA_ATRIBUIR:
            try:
                tid = find_task_by_name(access_token, project_id, nome)
                if tid:
                    atribuir_dono_tarefa(access_token, project_id, tid, gp_zpuid)
            except Exception as e:
                print(f"AVISO: Falha ao atribuir dono em '{nome}': {e}")

        # Garantir tag principal de onboarding
        try:
            ensure_project_tags(access_token, project_id, [TAG_AGUARDANDO_ONBOARDING_ID])
        except Exception as e:
            print(f"AVISO: Falha ao garantir tag no projeto: {e}")

        return True
    except Exception as e:
        print(f"AVISO: Erro em processar_tarefas_iniciais: {e}")
        return False


def listar_tarefas_do_projeto(access_token, project_id):
    print(f"INFO: Listando tarefas do projeto {project_id}...")
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
    headers = _zp_headers(access_token)
    todas_as_tarefas, page_number = [], 1
    while True:
        params = {"page": page_number, "per_page": 100}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            tarefas_da_pagina = response.json().get('tasks', [])
            if not tarefas_da_pagina: break
            todas_as_tarefas.extend(tarefas_da_pagina)
            if len(tarefas_da_pagina) < 100: break
            page_number += 1
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao listar tarefas: {e.response.text}")
    print(f"INFO: Lista de tarefas obtida ({len(todas_as_tarefas)} total).")
    return todas_as_tarefas

def atribuir_dono_tarefa(access_token, project_id, task_id, gp_zpuid):
    url = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}/"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"person_responsible": str(gp_zpuid)}
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"AVISO: Erro ao atribuir dono à tarefa {task_id}: {e.response.text}")
        return False

def _zp_rest_base():
    return f"https://projectsapi.zoho.{_zoho_domain()}/restapi"

def concluir_tarefa(access_token, project_id, task_id):
    url = f"{_zp_rest_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}/"
    headers = _zp_headers(access_token)
    payload = {"custom_status": STATUS_CONCLUIDO_ID}
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"AVISO: Erro ao concluir tarefa {task_id}: {e.response.text}")
        return False

def aplicar_tag_ao_projeto(access_token, project_id, tag_id_num):
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = _zp_headers(access_token)
    try:
        payload = {
            "tags": {
                "add": [
                    {"id": int(tag_id_num)}
                ]
            }
        }
        r_patch = requests.patch(url, headers=headers, json=payload)
        r_patch.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        raise Exception(e.response.text if e.response else str(e))

def remover_tag_do_projeto(access_token, project_id, tag_id_num):
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = _zp_headers(access_token)
    try:
        payload = {"tags": {"remove": [{"id": int(tag_id_num)}]}}
        r_patch = requests.patch(url, headers=headers, json=payload)
        r_patch.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        raise Exception(e.response.text if e.response else str(e))

def obter_detalhes_projeto(access_token, project_id):
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = _zp_headers(access_token)
    try:
        print(f"[obter_detalhes_projeto] URL={url}")
        r = requests.get(url, headers=headers)
        print(f"[obter_detalhes_projeto] status={r.status_code} body={r.text[:500]}")
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and data.get('id'):
            return data
        projects = (data or {}).get('projects', []) if isinstance(data, dict) else []
        if projects:
            return projects[0]
        return {}
    except requests.exceptions.RequestException as e:
        raise Exception(e.response.text if e.response else str(e))

def comentar_na_tarefa(access_token, project_id, task_id, conteudo):
    url = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}/comments/"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"content": conteudo}
    try:
        r = requests.post(url, headers=headers, data=payload)
        r.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"AVISO: Falha ao comentar na tarefa {task_id}: {e.response.text if e.response else e}")
        return False

def atualizar_status_principal_planilha_por_cliente(sheets_service, valor_cliente, novo_status):
    range_cabecalho = f"'{NOME_ABA_PLANILHA}'!A{LINHA_CABECALHO}:ZZ{LINHA_CABECALHO}"
    cabecalhos = sheets_service.spreadsheets().values().get(
        spreadsheetId=ID_PLANILHA_PROJETOS, range=range_cabecalho
    ).execute().get('values', [[]])[0]
    mapa_colunas = {cabecalho: i for i, cabecalho in enumerate(cabecalhos)}
    if 'Cliente' not in mapa_colunas or 'Status Principal' not in mapa_colunas:
        raise Exception("Colunas necessárias não encontradas na planilha")

    def _norm(s):
        import unicodedata
        if not isinstance(s, str):
            s = '' if s is None else str(s)
        s = unicodedata.normalize('NFD', s)
        s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
        s = s.strip().lower().replace('–', '-').replace('—', '-')
        s = ' '.join(s.split())
        return s

    letra_cliente = indice_para_letra_coluna(mapa_colunas['Cliente'])
    letra_status = indice_para_letra_coluna(mapa_colunas['Status Principal'])
    range_coluna_cliente = f"'{NOME_ABA_PLANILHA}'!{letra_cliente}{LINHA_CABECALHO+1}:{letra_cliente}"
    valores = sheets_service.spreadsheets().values().get(
        spreadsheetId=ID_PLANILHA_PROJETOS, range=range_coluna_cliente
    ).execute().get('values', [])

    alvo_norm = _norm(valor_cliente)
    print(f"[atualizar_planilha] Procurando cliente: '{valor_cliente}' (norm='{alvo_norm}')")
    linha_encontrada = None

    for idx, row in enumerate(valores):
        cel = (row[0] if row else '')
        if _norm(cel) == alvo_norm:
            linha_encontrada = LINHA_CABECALHO + 1 + idx
            print(f"[atualizar_planilha] Match exato na linha {linha_encontrada}: '{cel}'")
            break

    if not linha_encontrada:
        try:
            partes = valor_cliente.split(' - ', 1)
            nome_parte = _norm(partes[1] if len(partes) > 1 else valor_cliente)
        except Exception:
            nome_parte = alvo_norm
        for idx, row in enumerate(valores):
            cel = (row[0] if row else '')
            if nome_parte and nome_parte in _norm(cel):
                linha_encontrada = LINHA_CABECALHO + 1 + idx
                print(f"[atualizar_planilha] Match parcial na linha {linha_encontrada}: '{cel}'")
                break

    if not linha_encontrada:
        raise Exception("Linha do cliente não encontrada na planilha")

    range_status_cell = f"'{NOME_ABA_PLANILHA}'!{letra_status}{linha_encontrada}"
    print(f"[atualizar_planilha] Atualizando célula {range_status_cell} para '{novo_status}'")
    sheets_service.spreadsheets().values().update(
        spreadsheetId=ID_PLANILHA_PROJETOS,
        range=range_status_cell,
        valueInputOption='USER_ENTERED',
        body={"values": [[novo_status]]}
    ).execute()
    print("[atualizar_planilha] Atualização concluída")
    return True

def atualizar_coluna_planilha_por_cliente(sheets_service, valor_cliente, coluna_nome, novo_valor):
    range_cabecalho = f"'{NOME_ABA_PLANILHA}'!A{LINHA_CABECALHO}:ZZ{LINHA_CABECALHO}"
    cabecalhos = sheets_service.spreadsheets().values().get(
        spreadsheetId=ID_PLANILHA_PROJETOS, range=range_cabecalho
    ).execute().get('values', [[]])[0]
    mapa_colunas = {cabecalho: i for i, cabecalho in enumerate(cabecalhos)}
    if 'Cliente' not in mapa_colunas or coluna_nome not in mapa_colunas:
        raise Exception(f"Colunas necessárias não encontradas na planilha: Cliente ou {coluna_nome}")

    def _norm(s):
        import unicodedata
        if not isinstance(s, str):
            s = '' if s is None else str(s)
        s = unicodedata.normalize('NFD', s)
        s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
        s = s.strip().lower().replace('–', '-').replace('—', '-')
        s = ' '.join(s.split())
        return s

    letra_cliente = indice_para_letra_coluna(mapa_colunas['Cliente'])
    letra_coluna = indice_para_letra_coluna(mapa_colunas[coluna_nome])
    range_coluna_cliente = f"'{NOME_ABA_PLANILHA}'!{letra_cliente}{LINHA_CABECALHO+1}:{letra_cliente}"
    valores = sheets_service.spreadsheets().values().get(
        spreadsheetId=ID_PLANILHA_PROJETOS, range=range_coluna_cliente
    ).execute().get('values', [])

    alvo_norm = _norm(valor_cliente)
    print(f"[atualizar_planilha] Procurando cliente: '{valor_cliente}' (norm='{alvo_norm}')")
    linha_encontrada = None

    for idx, row in enumerate(valores):
        cel = (row[0] if row else '')
        if _norm(cel) == alvo_norm:
            linha_encontrada = LINHA_CABECALHO + 1 + idx
            print(f"[atualizar_planilha] Match exato na linha {linha_encontrada}: '{cel}'")
            break

    if not linha_encontrada:
        try:
            partes = valor_cliente.split(' - ', 1)
            nome_parte = _norm(partes[1] if len(partes) > 1 else valor_cliente)
        except Exception:
            nome_parte = alvo_norm
        for idx, row in enumerate(valores):
            cel = (row[0] if row else '')
            if nome_parte and nome_parte in _norm(cel):
                linha_encontrada = LINHA_CABECALHO + 1 + idx
                print(f"[atualizar_planilha] Match parcial na linha {linha_encontrada}: '{cel}'")
                break

    if not linha_encontrada:
        raise Exception("Linha do cliente não encontrada na planilha")

    range_cell = f"'{NOME_ABA_PLANILHA}'!{letra_coluna}{linha_encontrada}"
    print(f"[atualizar_planilha] Atualizando célula {range_cell} para '{novo_valor}'")
    sheets_service.spreadsheets().values().update(
        spreadsheetId=ID_PLANILHA_PROJETOS,
        range=range_cell,
        valueInputOption='USER_ENTERED',
        body={"values": [[novo_valor]]}
    ).execute()
    print("[atualizar_planilha] Atualização concluída")
    return True

def determinar_coluna_projeto(projeto):
    status = projeto.get('status', {})
    status_id = str(status.get('id', ''))
    tags = projeto.get('tags', [])
    tag_ids = [str(tag.get('id', '')) for tag in tags]
    if status_id == STATUS_ABERTO_ID and TAG_AGUARDANDO_ONBOARDING_ID in tag_ids:
        return "Aguardando Onboarding"
    if status_id == STATUS_ABERTO_ID and TAG_AGUARDANDO_INFRA_ID in tag_ids:
        return "Falta Liberar Servidor Infra"
    if status_id == STATUS_EM_ANDAMENTO_ID and TAG_EM_HOMOLOGACAO_ID in tag_ids:
        return "Em Homologação"
    if status_id == STATUS_EM_ANDAMENTO_ID and TAG_EM_VIRADA_ID in tag_ids:
        return "Em Virada"
    if status_id == STATUS_OPERACAO_ASSISTIDA_ID and TAG_AGUARDANDO_ENCERRAMENTO_ID in tag_ids:
        return "Aguardando Encerramento"
    if status_id == STATUS_AGUARDANDO_CLIENTE_ID and TAG_PARADO_ID in tag_ids:
        return "Projeto Parado"
    if status_id == STATUS_PENDENCIA_ID and TAG_PARADO_ID in tag_ids:
        return "Projeto Parado"
    status_map = {
        STATUS_EM_ANDAMENTO_ID: "Aguardando Cronograma",
        STATUS_FINALIZADO_ID: "Finalizado",
        STATUS_OPERACAO_ASSISTIDA_ID: "Em Operação Assistida"
    }
    return status_map.get(status_id, "Status Desconhecido")

def formatar_data_brasileira(data_str):
    try:
        if not data_str:
            return "N/D"
        formatos_entrada = [
            '%Y-%m-%d','%m-%d-%Y','%d-%m-%Y','%Y-%m-%d %H:%M:%S','%m-%d-%Y %H:%M:%S'
        ]
        for formato in formatos_entrada:
            try:
                data_obj = datetime.strptime(data_str[:10], formato)
                return data_obj.strftime('%d-%m-%Y')
            except ValueError:
                continue
        return "N/D"
    except Exception as e:
        print(f"Erro na formatação de data: {e}")
        return "N/D"

def atualizar_custom_field_projeto(access_token, project_id, field_key, field_value):
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = _zp_headers(access_token)
    try:
        payload = {"custom_fields": {field_key: field_value}}
        r_patch = requests.patch(url, headers=headers, json=payload)
        r_patch.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        raise Exception(e.response.text if e.response else str(e))

def obter_data_ultima_mudanca_status_ou_tag(project_id, access_token):
    try:
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/edits"
        headers = _zp_headers(access_token)
        params = {"index": 1, "range": 50}
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            for key in ["edits", "data", "activities", "logs", "history", "items"]:
                if isinstance(data.get(key), list):
                    items = data[key]
                    break
            if not items and isinstance(data.get("project"), dict):
                proj = data["project"]
                for key in ["edits", "data", "activities", "logs", "history", "items"]:
                    if isinstance(proj.get(key), list):
                        items = proj[key]
                        break

        def parse_date_str(s):
            if not s:
                return None
            s = str(s)
            if s.endswith('Z'):
                for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
                    try:
                        dt = datetime.strptime(s, fmt)
                        return dt.date()
                    except Exception:
                        pass
            fmts = [
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d-%m-%Y",
            ]
            for fmt in fmts:
                try:
                    dt = datetime.strptime(s, fmt)
                    return dt.date()
                except Exception:
                    continue
            try:
                dt = datetime.strptime(s[:10], "%Y-%m-%d")
                return dt.date()
            except Exception:
                return None

        last_date = None
        for item in items or []:
            try:
                item_text = json.dumps(item, ensure_ascii=False).lower()
            except Exception:
                item_text = str(item).lower()
            if ("status" in item_text) or ("tag" in item_text) or ("tags" in item_text):
                ts = None
                if isinstance(item, dict):
                    ts = item.get('action_time') or item.get('time')
                if ts is None:
                    for key in [
                        "updated_time", "modified_time", "modified_at", "time", "date", "created_time", "log_time", "timestamp"
                    ]:
                        if isinstance(item, dict) and key in item:
                            ts = item[key]
                            break
                if ts is None and isinstance(item, dict):
                    for sub in ["details", "edit", "activity"]:
                        if isinstance(item.get(sub), dict):
                            for key in [
                                "updated_time", "modified_time", "modified_at", "time", "date", "created_time", "log_time", "timestamp"
                            ]:
                                if key in item[sub]:
                                    ts = item[sub][key]
                                    break
                        if ts:
                            break
                d = parse_date_str(ts) if ts else None
                if d and (last_date is None or d > last_date):
                    last_date = d
        return last_date
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar edits do projeto {project_id}: {e.response.text if e.response else e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao processar edits do projeto {project_id}: {e}")
        return None

def map_status_to_coluna(status_nome: str) -> str:
    if not status_nome:
        return None
    s = str(status_nome).strip().lower()
    mapa = {
        'aguardando cronograma': 'Aguardando Cronograma',
        'finalizado': 'Finalizado',
        'operação assistida': 'Em Operação Assistida',
        'em operação assistida': 'Em Operação Assistida',
        'cancelado': 'Cancelado',
        'ativo': 'Aguardando Cronograma',
    }
    return mapa.get(s)

def map_etiquetas_to_coluna_por_ids(tags_str: str) -> str:
    if not tags_str:
        return None

    nome_tag_para_id = {
        'aguardando onboarding': TAG_AGUARDANDO_ONBOARDING_ID,
        'aguardando infra': TAG_AGUARDANDO_INFRA_ID,
        'falta liberar servidor infra': TAG_AGUARDANDO_INFRA_ID,
        'em homologação': TAG_EM_HOMOLOGACAO_ID,
        'homologação': TAG_EM_HOMOLOGACAO_ID,
        'em virada': TAG_EM_VIRADA_ID,
        'virada': TAG_EM_VIRADA_ID,
        'parado': TAG_PARADO_ID,
        'projeto parado': TAG_PARADO_ID,
        'aguardando encerramento': TAG_AGUARDANDO_ENCERRAMENTO_ID,
    }

    mapeamento = get_mapeamento_colunas()
    colunas_por_tag_id = {}
    for coluna, cfg in (mapeamento or {}).items():
        for tag_id in cfg.get('zohoTagsToAdd', []) or []:
            colunas_por_tag_id[str(tag_id)] = coluna

    try:
        s = str(tags_str).strip()
        if s.startswith('[') and s.endswith(']'):
            s = s[1:-1]
        nomes = [p.strip().lower() for p in s.split(',') if p.strip()]
    except Exception:
        nomes = [str(tags_str).strip().lower()]

    for nome in nomes:
        tag_id = nome_tag_para_id.get(nome)
        if not tag_id:
            continue
        coluna = colunas_por_tag_id.get(str(tag_id))
        if coluna:
            return coluna
    return None

def obter_data_ultima_mudanca_etiqueta_para_coluna(project_id, access_token, coluna_alvo: str):
    try:
        # Usa o cache interno e paginação moderada para respeitar rate limit
        items = _fetch_project_edits(access_token, project_id, max_pages=6)

        def parse_action_time(s):
            if not s:
                return None
            s = str(s)
            if s.endswith('Z'):
                for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
                    try:
                        return datetime.strptime(s, fmt).date()
                    except Exception:
                        pass
            for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt).date()
                except Exception:
                    pass
            try:
                return datetime.strptime(s[:10], "%Y-%m-%d").date()
            except Exception:
                return None

        coluna_alvo_norm = (coluna_alvo or '').strip()
        best_date = None
        for item in items or []:
            if not isinstance(item, dict):
                continue
            edits = item.get('edits') or []
            if not isinstance(edits, list):
                continue
            for ed in edits:
                if not isinstance(ed, dict):
                    continue
                field_name = str(ed.get('field_name', '')).strip().lower()
                if field_name != 'etiquetas':
                    continue
                coluna_resultante = map_etiquetas_to_coluna_por_ids(ed.get('new_value'))
                if not coluna_resultante:
                    continue
                if coluna_resultante != coluna_alvo_norm:
                    continue
                d = parse_action_time(item.get('action_time') or item.get('time'))
                if d and (best_date is None or d > best_date):
                    best_date = d
        return best_date
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar edits/etiquetas do projeto {project_id}: {e.response.text if e.response else e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao processar edits/etiquetas do projeto {project_id}: {e}")
        return None


def _normalize_edits_response(data):
    items = []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["edits", "data", "activities", "logs", "history", "items"]:
            if isinstance(data.get(key), list):
                return data[key]
        if isinstance(data.get("project"), dict):
            proj = data["project"]
            for key in ["edits", "data", "activities", "logs", "history", "items"]:
                if isinstance(proj.get(key), list):
                    return proj[key]
    return items

def _fetch_project_edits(access_token, project_id, max_pages: int = 3):
    # Cache leve para reduzir chamadas repetitivas ao Zoho
    now = int(time.time())
    cache_entry = _EDITS_CACHE.get(str(project_id))
    if cache_entry and (now - cache_entry.get('ts', 0) <= _EDITS_TTL_SECONDS):
        return cache_entry.get('items', [])

    headers = _zp_headers(access_token)
    base_url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/edits"
    # Tenta intervalos menores primeiro para evitar 400
    ranges = [10, 5, 20]
    collected = []
    for rg in ranges:
        try:
            for page in range(1, max_pages + 1):
                params = {"index": page, "range": rg}
                resp = requests.get(base_url, headers=headers, params=params, timeout=20)
                if resp.status_code == 400:
                    print(f"[edits] 400 com range={rg} page={page} -> tentando range menor")
                    collected = []
                    break
                resp.raise_for_status()
                items = _normalize_edits_response(resp.json())
                if not isinstance(items, list) or not items:
                    break
                collected.extend(items)
                # Se trouxe menos que o range, provavelmente acabaram os itens nesta paginação
                if len(items) < rg:
                    break
            if collected:
                break
        except Exception as e:
            print(f"[edits] falha range={rg}: {e}")
            continue

    # Atualiza cache (mesmo vazio) para evitar bater na API em loop
    _EDITS_CACHE[str(project_id)] = { 'items': collected, 'ts': now }
    return collected

def obter_data_ultima_mudanca_status_ou_tag(project_id, access_token):
    try:
        # Usa o cache interno e paginação moderada para respeitar rate limit
        items = _fetch_project_edits(access_token, project_id, max_pages=6)
        if not items:
            return None
        def parse_action_time(s):
            if not s:
                return None
            s = str(s)
            if s.endswith('Z'):
                for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
                    try:
                        return datetime.strptime(s, fmt).date()
                    except Exception:
                        pass
            for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt).date()
                except Exception:
                    pass
            try:
                return datetime.strptime(s[:10], "%Y-%m-%d").date()
            except Exception:
                return None
        best_date = None
        for item in items:
            if not isinstance(item, dict):
                continue
            edits = item.get('edits') or []
            if not isinstance(edits, list):
                continue
            for ed in edits:
                if not isinstance(ed, dict):
                    continue
                fname = str(ed.get('field_name', '')).strip().lower()
                if fname not in ("status", "etiquetas"):
                    continue
                d = parse_action_time(item.get('action_time') or item.get('time'))
                if d and (best_date is None or d > best_date):
                    best_date = d
        return best_date
    except Exception as e:
        print(f"[edits] obter_data_ultima_mudanca_status_ou_tag falhou: {e}")
        return None

def get_mapeamento_colunas():
    global _MAPPINGS_CACHE
    if _MAPPINGS_CACHE is not None:
        return _MAPPINGS_CACHE
    try:
        path = os.path.join(os.path.dirname(__file__), 'mapeamento_colunas.json')
        with open(path, 'r', encoding='utf-8') as f:
            _MAPPINGS_CACHE = json.load(f)
    except Exception as e:
        print(f"ERRO ao carregar mapeamento_colunas.json: {e}")
        _MAPPINGS_CACHE = {}
    return _MAPPINGS_CACHE

def obter_data_ultima_mudanca_status_para_coluna(project_id, access_token, coluna_alvo: str):
    try:
        mapeamento = get_mapeamento_colunas()
        cfg = mapeamento.get(coluna_alvo or '') or {}
        status_id_alvo = str(cfg.get('zohoStatusId') or '')
        if not status_id_alvo:
            return None

        nome_status_para_id = {
            'aberto': STATUS_ABERTO_ID,
            'ativo': STATUS_ABERTO_ID,
            'aguardando cronograma': STATUS_EM_ANDAMENTO_ID,
            'finalizado': STATUS_FINALIZADO_ID,
            'operação assistida': STATUS_OPERACAO_ASSISTIDA_ID,
            'em operação assistida': STATUS_OPERACAO_ASSISTIDA_ID,
            'cancelado': STATUS_CANCELADO_ID,
        }

        items = _fetch_project_edits(access_token, project_id, max_pages=3)

        def parse_action_time(s):
            if not s:
                return None
            s = str(s)
            if s.endswith('Z'):
                for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
                    try:
                        return datetime.strptime(s, fmt).date()
                    except Exception:
                        pass
            for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt).date()
                except Exception:
                    pass
            try:
                return datetime.strptime(s[:10], "%Y-%m-%d").date()
            except Exception:
                return None

        best_date = None
        for item in items or []:
            if not isinstance(item, dict):
                continue
            edits = item.get('edits') or []
            if not isinstance(edits, list):
                continue
            for ed in edits:
                if not isinstance(ed, dict):
                    continue
                field_name = str(ed.get('field_name', '')).strip().lower()
                if field_name != 'status':
                    continue
                new_val = str(ed.get('new_value', '')).strip().lower()
                status_id_do_evento = nome_status_para_id.get(new_val)
                if not status_id_do_evento:
                    continue
                if str(status_id_do_evento) != status_id_alvo:
                    continue
                d = parse_action_time(item.get('action_time') or item.get('time'))
                if d and (best_date is None or d > best_date):
                    best_date = d
        return best_date
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar edits/status do projeto {project_id}: {e.response.text if e.response else e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao processar edits/status do projeto {project_id}: {e}")
        return None

def calcular_dias_na_fase(info_projeto, status_atual, project_id=None, access_token=None):
    try:
        if project_id and access_token:
            ultima_data = obter_data_ultima_mudanca_status_ou_tag(project_id, access_token)
            if ultima_data:
                dias = (date.today() - ultima_data).days
                if str(project_id) == "2376502000000213310":
                    print(f"DEBUG dias_na_fase: projeto={project_id} ultima_data={ultima_data} dias={dias}")
                if dias < 0:
                    return "Futuro"
                elif dias == 0:
                    return "Hoje"
                else:
                    return f"{dias}d"

        data_inicio_str = info_projeto.get('data_inicio') or info_projeto.get('data_criacao', '')
        if not data_inicio_str:
            return "N/D"
        formatos_data = [
            '%Y-%m-%d','%m-%d-%Y','%d-%m-%Y','%Y-%m-%d %H:%M:%S','%m-%d-%Y %H:%M:%S'
        ]
        data_inicio = None
        for formato in formatos_data:
            try:
                data_inicio = datetime.strptime(data_inicio_str[:10], formato).date()
                break
            except ValueError:
                continue
        if not data_inicio:
            return "N/D"
        dias_na_fase = (date.today() - data_inicio).days
        if dias_na_fase < 0:
            return "Futuro"
        elif dias_na_fase == 0:
            return "Hoje"
        else:
            return f"{dias_na_fase}d"
    except Exception as e:
        print(f"Erro no cálculo de dias: {e}")
        return "N/D"

def calcular_dias_total_projeto(data_inicio_str: str, data_criacao_str: str) -> str:
    try:
        def parse_date(s):
            if not s:
                return None
            s = str(s).strip()
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(s[:19], fmt).date() if 'T' in s or ' ' in s else datetime.strptime(s, fmt).date()
                except Exception:
                    continue
            try:
                return datetime.strptime(s[:10], "%Y-%m-%d").date()
            except Exception:
                return None
        d_inicio = parse_date(data_inicio_str)
        if not d_inicio:
            d_inicio = parse_date(data_criacao_str)
        if not d_inicio:
            return "N/D"
        dias = (date.today() - d_inicio).days
        if dias < 0:
            dias = 0
        return f"{dias}d"
    except Exception:
        return "N/D"

def atualizar_status_principal_planilha_por_cliente(sheets_service, cliente_sheet, novo_status):
    """Alias para _update_status_planilha_principal"""
    return _update_status_planilha_principal(sheets_service, cliente_sheet, novo_status)

def atualizar_coluna_planilha_por_cliente(sheets_service, cliente_sheet, coluna, valor):
    """Alias para update_col_value_by_cliente_tolerant"""
    return update_col_value_by_cliente_tolerant(sheets_service, cliente_sheet, coluna, valor)

def obter_custom_fields_projeto(access_token, project_id):
    """Obtém os custom fields definidos no layout do projeto no Zoho."""
    # Primeiro, obter o layout_id do projeto
    project_url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = _zp_headers(access_token)
    resp = requests.get(project_url, headers=headers, timeout=30)
    resp.raise_for_status()
    project_data = resp.json()
    # Verificar se é nested ou direto
    if 'project' in project_data:
        project = project_data['project']
    else:
        project = project_data
    layout_id = project.get('layout', {}).get('id')
    if not layout_id:
        print("[WARN] Layout ID não encontrado no projeto, retornando lista vazia")
        return []

    # Tentar diferentes endpoints para obter custom fields
    possible_urls = [
        f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/layouts/{layout_id}/customfields",
        f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/layouts/{layout_id}/fields",
        f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/customfields?layout_id={layout_id}",
    ]

    for url in possible_urls:
        try:
            print(f"[DEBUG] Tentando obter custom fields de: {url}")
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                custom_fields = data.get('customfields', []) or data.get('fields', [])
                print(f"[DEBUG] Sucesso com {len(custom_fields)} campos encontrados")
                return custom_fields
            else:
                print(f"[DEBUG] URL {url} falhou: {resp.status_code}")
        except Exception as e:
            print(f"[DEBUG] Erro com URL {url}: {e}")

    print("[WARN] Não foi possível obter custom fields do layout")
    return []

def atualizar_custom_field_projeto(access_token, project_id, field_label, value):
    """Atualiza um custom field de um projeto no Zoho."""
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = _zp_headers(access_token)
    # Tentar diferentes formatos de payload
    payloads = [
        {"custom_fields": {field_label: value}},  # Formato nested
        {field_label: value},  # Formato direto
    ]

    for payload in payloads:
        try:
            print(f"[DEBUG] Tentando payload: {payload}")
            resp = requests.patch(url, headers=headers, json=payload, timeout=30)
            if resp.status_code in (200, 201, 204):
                response_data = resp.json() if resp.text else {}
                # Verificar se o campo foi realmente atualizado (aparece na resposta)
                field_updated = False
                if isinstance(response_data, dict):
                    # Verificar se o campo aparece diretamente ou em custom_fields
                    if field_label in response_data:
                        field_updated = True
                    elif 'custom_fields' in response_data and field_label in response_data['custom_fields']:
                        field_updated = True

                if field_updated:
                    print(f"[DEBUG] Campo customizado '{field_label}' REALMENTE atualizado para '{value}' no projeto {project_id}")
                else:
                    print(f"[WARN] Campo '{field_label}' NÃO foi atualizado (não aparece na resposta da API)")
                return response_data
            else:
                print(f"[DEBUG] Payload {payload} falhou: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            print(f"[DEBUG] Erro com payload {payload}: {e}")

    raise Exception(f"Falha ao atualizar campo customizado '{field_label}'")

_DIAS_FASE_CACHE = {}
_CACHE_TTL_SECONDS = 90

# Cache para histórico de edits do Zoho (por projeto)
_EDITS_CACHE = {}
_EDITS_TTL_SECONDS = 300

def _invalidate_dias_cache(project_id: str):
    try:
        keys = list(_DIAS_FASE_CACHE.keys())
        for k in keys:
            if k == str(project_id) or k.startswith(f"{project_id}|"):
                _DIAS_FASE_CACHE.pop(k, None)
    except Exception:
        pass

def _a1_col_letter(idx0: int) -> str:
    s = ""
    n = idx0 + 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

def _find_header_indexes(headers_row_values: list[str], desired_names: list[str]) -> dict:
    out = {}
    lower_map = {str(v).strip().lower(): i for i, v in enumerate(headers_row_values or []) if str(v).strip()}
    for name in desired_names:
        key = str(name).strip().lower()
        if key in lower_map:
            out[name] = lower_map[key]
    return out

import unicodedata

def _normalize_text(s: str) -> str:
    s = (s or '').strip()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')  # remove acentos
    s = ' '.join(s.split())  # colapsa espaços
    return s.lower()

def _extract_codigo(s: str) -> str | None:
    try:
        parte = (s or '').split(' - ')[0].strip().replace('.', '')
        m = re.match(r'^\d+', parte)
        return m.group(0) if m else None
    except Exception:
        return None

def _update_status_planilha_principal(sheets_service, cliente_key: str, novo_status: str, status_header_candidates=None) -> bool:
    headers_range = f"{NOME_ABA_PLANILHA}!A{LINHA_CABECALHO}:ZZ{LINHA_CABECALHO}"
    resp = sheets_service.spreadsheets().values().get(spreadsheetId=ID_PLANILHA_PROJETOS, range=headers_range).execute()
    headers = (resp.get('values') or [[]])[0]
    if not headers:
        raise RuntimeError('Cabeçalho não encontrado na planilha principal.')

    if status_header_candidates is None:
        status_header_candidates = ["Status Principal", "Status", "STATUS PRINCIPAL", "STATUS"]
    idx_map = _find_header_indexes(headers, [COLUNA_REFERENCIA_PARA_CONTAR_LINHAS] + status_header_candidates)
    if COLUNA_REFERENCIA_PARA_CONTAR_LINHAS not in idx_map:
        raise RuntimeError(f"Coluna de referência '{COLUNA_REFERENCIA_PARA_CONTAR_LINHAS}' não encontrada no cabeçalho.")
    status_idx = None
    for nm in status_header_candidates:
        if nm in idx_map:
            status_idx = idx_map[nm]
            break
    if status_idx is None:
        raise RuntimeError("Coluna de Status não encontrada (tente ajustar os nomes candidatos).")

    cliente_idx = idx_map[COLUNA_REFERENCIA_PARA_CONTAR_LINHAS]
    cliente_col = _a1_col_letter(cliente_idx)

    valores_cli_range = f"{NOME_ABA_PLANILHA}!{cliente_col}{LINHA_CABECALHO+1}:{cliente_col}"
    vals = sheets_service.spreadsheets().values().get(spreadsheetId=ID_PLANILHA_PROJETOS, range=valores_cli_range).execute()
    linhas = (vals.get('values') or [])

    alvo = (cliente_key or '').strip()
    alvo_norm = _normalize_text(alvo)
    alvo_cod = _extract_codigo(alvo)

    linha_encontrada = None
    for i, row in enumerate(linhas, start=LINHA_CABECALHO + 1):
        val = (row[0] if row else '').strip()
        val_norm = _normalize_text(val)
        # match exato normalizado
        if val_norm == alvo_norm and val:
            linha_encontrada = i
            break
        # match por código numérico no prefixo
        if alvo_cod:
            val_cod = _extract_codigo(val)
            if val_cod and val_cod == alvo_cod:
                linha_encontrada = i
                break
    if not linha_encontrada:
        raise RuntimeError(f"Cliente '{cliente_key}' não encontrado na planilha principal.")

    status_col_letter = _a1_col_letter(status_idx)
    update_range = f"{NOME_ABA_PLANILHA}!{status_col_letter}{linha_encontrada}"
    body = {"values": [[novo_status]]}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=ID_PLANILHA_PROJETOS,
        range=update_range,
        valueInputOption="RAW",
        body=body
    ).execute()
    return True

def extrair_cliente_planilha(nome_projeto: str) -> str:
    """Normaliza o nome do cliente removendo sufixos padrão da planilha."""
    if not nome_projeto:
        return ""
    valor = (nome_projeto or "").strip()
    # remove " - AP" ou " - NR" (case-insensitive) no final
    for sufixo in (" - AP", " - NR"):
        if valor.upper().endswith(sufixo):
            valor = valor[: -len(sufixo)].strip()
    # remove " - NR/AP" (variação antiga)
    if valor.upper().endswith(" - NR/AP"):
        valor = valor[: -len(" - NR/AP")].strip()
    return valor


def update_col_value_by_cliente_tolerant(sheets_service, cliente_full: str, col_name: str, value: str) -> bool:
    headers_range = f"{NOME_ABA_PLANILHA}!A{LINHA_CABECALHO}:ZZ{LINHA_CABECALHO}"
    resp = sheets_service.spreadsheets().values().get(spreadsheetId=ID_PLANILHA_PROJETOS, range=headers_range).execute()
    headers = (resp.get('values') or [[]])[0]
    if not headers:
        raise RuntimeError('Cabeçalho não encontrado na planilha principal.')
    idx_map = _find_header_indexes(headers, [COLUNA_REFERENCIA_PARA_CONTAR_LINHAS, col_name])
    if COLUNA_REFERENCIA_PARA_CONTAR_LINHAS not in idx_map:
        raise RuntimeError(f"Coluna de referência '{COLUNA_REFERENCIA_PARA_CONTAR_LINHAS}' não encontrada.")
    if col_name not in idx_map:
        raise RuntimeError(f"Coluna '{col_name}' não encontrada no cabeçalho.")

    cliente_idx = idx_map[COLUNA_REFERENCIA_PARA_CONTAR_LINHAS]
    cliente_col = _a1_col_letter(cliente_idx)

    valores_cli_range = f"{NOME_ABA_PLANILHA}!{cliente_col}{LINHA_CABECALHO+1}:{cliente_col}"
    vals = sheets_service.spreadsheets().values().get(spreadsheetId=ID_PLANILHA_PROJETOS, range=valores_cli_range).execute()
    linhas = (vals.get('values') or [])

    alvo = (cliente_full or '').strip()
    alvo_norm = _normalize_text(alvo)
    alvo_cod = _extract_codigo(alvo)

    linha_encontrada = None
    for i, row in enumerate(linhas, start=LINHA_CABECALHO + 1):
        val = (row[0] if row else '').strip()
        val_norm = _normalize_text(val)
        if val and (val_norm == alvo_norm):
            linha_encontrada = i
            break
        if alvo_cod:
            val_cod = _extract_codigo(val)
            if val_cod and val_cod == alvo_cod:
                linha_encontrada = i
                break
        if alvo_norm and alvo_norm in val_norm:
            linha_encontrada = i
            break

    if not linha_encontrada:
        raise RuntimeError(f"Cliente '{cliente_full}' não encontrado na planilha principal (tolerante).")

    target_col_letter = _a1_col_letter(idx_map[col_name])
    update_range = f"{NOME_ABA_PLANILHA}!{target_col_letter}{linha_encontrada}"
    body = {"values": [[value]]}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=ID_PLANILHA_PROJETOS,
        range=update_range,
        valueInputOption="RAW",
        body=body
    ).execute()
    return True

def obter_ipv6_do_drive(drive_service, id_pasta_cliente):
    try:
        print(f"DEBUG: Iniciando busca de IPv6 na pasta do cliente com ID: {id_pasta_cliente}")
        query_infra = f"name = 'Infraestrutura' and mimeType = 'application/vnd.google-apps.folder' and '{id_pasta_cliente}' in parents and trashed = false"
        results_infra = drive_service.files().list(q=query_infra, fields="files(id, name)").execute()
        items_infra = results_infra.get('files', [])
        if not items_infra:
            print(f"DEBUG: Pasta 'Infraestrutura' não encontrada na pasta do cliente com ID '{id_pasta_cliente}'.")
            return None
        id_pasta_infra = items_infra[0]['id']
        print(f"DEBUG: Pasta 'Infraestrutura' encontrada (ID: {id_pasta_infra})")

        query_docx = f"mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' and '{id_pasta_infra}' in parents and trashed = false"
        results_docx = drive_service.files().list(q=query_docx, fields="files(id, name)").execute()
        files_docx = results_docx.get('files', [])
        print(f"DEBUG: Arquivos .docx encontrados na pasta 'Infraestrutura': {[f['name'] for f in files_docx]}")
        
        target_file = None
        for file in files_docx:
            if 'broker' not in file['name'].lower():
                target_file = file
                break
        
        if not target_file:
            print("DEBUG: Nenhum arquivo .docx válido (sem 'broker' no nome) encontrado.")
            return None
        
        print(f"DEBUG: Arquivo .docx alvo selecionado: {target_file['name']} (ID: {target_file['id']})")

        request_download = drive_service.files().get_media(fileId=target_file['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_download)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        fh.seek(0)
        document = docx.Document(fh)
        
        for para in document.paragraphs:
            if 'vpn animati' in para.text.lower():
                match = re.search(r'(fd[0-9a-fA-F:]+)', para.text)
                if match:
                    ipv6 = match.group(1)
                    print(f"DEBUG: IPv6 encontrado em parágrafo: {ipv6}")
                    return ipv6

        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if 'vpn animati' in para.text.lower():
                            match = re.search(r'(fd[0-9a-fA-F:]+)', para.text)
                            if match:
                                ipv6 = match.group(1)
                                print(f"DEBUG: IPv6 encontrado em tabela: {ipv6}")
                                return ipv6
        
        print("DEBUG: IPv6 não encontrado no documento.")
        return None

    except HttpError as error:
        print(f"ERRO: Ocorreu um erro na API do Google Drive: {error}")
        return None
    except Exception as e:
        print(f"ERRO: Ocorreu um erro inesperado em obter_ipv6_do_drive: {e}")
        return None


ZP_API_BASE = 'https://projectsapi.zoho.com/api/v3'
ZP_API_BASE_DYNAMIC = None

def _zp_base():
    return ZP_API_BASE_DYNAMIC or ZP_API_BASE

def _map_projects_base(api_domain: str) -> str:
    try:
        host = urllib.parse.urlparse(api_domain).netloc if api_domain else ''
    except Exception:
        host = ''
    if 'zohoapis.eu' in host:
        return 'https://projectsapi.zoho.eu/api/v3'
    if 'zohoapis.in' in host:
        return 'https://projectsapi.zoho.in/api/v3'
    if 'zohoapis.com.au' in host:
        return 'https://projectsapi.zoho.com.au/api/v3'
    if 'zohoapis.com.cn' in host:
        return 'https://projectsapi.zoho.com.cn/api/v3'
    return 'https://projectsapi.zoho.com/api/v3'


_ZOHO_TOKEN_CACHE = { 'token': None, 'exp': 0 }

def obter_access_token_zoho(ttl_seconds: int = 2700):
    import time as _t
    now = int(_t.time())
    tok = _ZOHO_TOKEN_CACHE.get('token')
    exp = int(_ZOHO_TOKEN_CACHE.get('exp') or 0)
    if tok and now < exp:
        return tok

    try:
        with open(ZOHO_TOKEN_PATH, 'r', encoding='utf-8') as f:
            refresh_token = f.read().strip()
    except FileNotFoundError:
        raise Exception('Arquivo de refresh token do Zoho não encontrado.')

    token_url = 'https://accounts.zoho.com/oauth/v2/token'
    data_form = {
        'refresh_token': refresh_token,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'grant_type': 'refresh_token'
    }

    last_err = None
    for i in range(3):
        r = requests.post(token_url, data=data_form, timeout=30)
        if r.status_code == 200:
            data = r.json()
            access_token = data.get('access_token')
            if not access_token:
                raise Exception('Resposta do Zoho sem access_token.')
            global ZP_API_BASE_DYNAMIC
            ZP_API_BASE_DYNAMIC = _map_projects_base(data.get('api_domain'))
            _ZOHO_TOKEN_CACHE['token'] = access_token
            _ZOHO_TOKEN_CACHE['exp'] = now + ttl_seconds
            return access_token
        else:
            last_err = f'HTTP {r.status_code} - {r.text}'
            _t.sleep(1 + i * 2)
    raise Exception(f'Falha ao obter access_token Zoho: {last_err}')

def _zp_headers(access_token: str):
    return {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json'
    }

def get_portal_project_tags(access_token: str):
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/tags"
    params = {"module": "projects"}
    print(f"[get_portal_project_tags] URL={url} params={params}")
    r = requests.get(url, headers=_zp_headers(access_token), params=params, timeout=30)
    print(f"[get_portal_project_tags] status={r.status_code} body={r.text[:500]}")
    r.raise_for_status()
    data = r.json() if r.text else {}
    tags = data.get('tags') if isinstance(data, dict) else None
    return tags or []

def get_project_tags(access_token: str, project_id: str):
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tags"
    print(f"[get_project_tags] URL={url}")
    r = requests.get(url, headers=_zp_headers(access_token), timeout=30)
    print(f"[get_project_tags] status={r.status_code} body={r.text[:500]}")
    r.raise_for_status()
    data = r.json() if r.text else {}
    return (data.get('tags') or []) if isinstance(data, dict) else []

def get_project_tags_strict(access_token: str, project_id: str):
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    params = {"fields": "tags"}
    print(f"[get_project_tags_strict] URL={url} params={params}")
    r = requests.get(url, headers=_zp_headers(access_token), params=params, timeout=30)
    print(f"[get_project_tags_strict] status={r.status_code} body={r.text[:500]}")
    r.raise_for_status()
    data = r.json() if r.text else {}
    tags_atuais = []
    if isinstance(data, dict):
        if isinstance(data.get('tags'), list):
            tags_atuais = data['tags']
        elif isinstance(data.get('tags'), dict):
            tags_atuais = data['tags'].get('data', []) or []
    return tags_atuais

def add_project_tag(access_token: str, project_id: str, tag_id: str):
    current_tags = get_project_tags_strict(access_token, project_id)
    current_ids = [str(t.get('id')) for t in (current_tags or []) if t.get('id') is not None]

    target_id = str(tag_id)
    if target_id not in current_ids:
        final_ids = current_ids + [target_id]
    else:
        final_ids = current_ids

    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    payload = { "tags": [ { "id": tid } for tid in final_ids ] }
    print(f"[add_project_tag] PATCH URL={url} payload={payload}")
    resp = requests.patch(url, headers=_zp_headers(access_token), json=payload, timeout=30)
    print(f"[add_project_tag] status={resp.status_code} body={resp.text[:10000]}")
    if resp.status_code not in (200, 201):
        raise Exception(f'Falha ao adicionar tag ao projeto: HTTP {resp.status_code} - {resp.text}')

    
def remove_project_tag(access_token: str, project_id: str, tag_id: str):
    current_tags = get_project_tags_strict(access_token, project_id)
    current_ids = [str(t.get('id')) for t in (current_tags or []) if t.get('id') is not None]

    target_id = str(tag_id)
    final_ids = [tid for tid in current_ids if tid != target_id]

    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    payload = { "tags": [ { "id": tid } for tid in final_ids ] }
    print(f"[remove_project_tag] PATCH URL={url} payload={payload}")
    resp = requests.patch(url, headers=_zp_headers(access_token), json=payload, timeout=30)
    print(f"[remove_project_tag] status={resp.status_code} body={resp.text[:1000]}")
    if resp.status_code not in (200, 201):
        raise Exception(f'Falha ao remover tag do projeto: HTTP {resp.status_code} - {resp.text}')

def ensure_project_tags(access_token: str, project_id: str, required_tag_ids, attempts: int = 2, delay_sec: float = 2.0):
    required = {str(tid) for tid in (required_tag_ids or [])}
    for i in range(max(1, attempts)):
        try:
            current_tags = get_project_tags_strict(access_token, project_id)
            current_ids = {str(t.get('id')) for t in (current_tags or []) if t.get('id') is not None}
            final_ids = list(current_ids.union(required))
            url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
            payload = {"tags": [{"id": tid} for tid in final_ids]}
            print(f"[ensure_project_tags] try={i+1} PATCH URL={url} payload={payload}")
            resp = requests.patch(url, headers=_zp_headers(access_token), json=payload, timeout=30)
            print(f"[ensure_project_tags] status={resp.status_code} body={resp.text[:500]}")
        except Exception as e:
            print(f"[ensure_project_tags] erro tentativa {i+1}: {e}")
        try:
            time.sleep(delay_sec)
        except Exception:
            pass

def set_project_tags_exact(access_token: str, project_id: str, final_tag_ids):
    desired = []
    for tid in (final_tag_ids or []):
        s = str(tid)
        if s and s not in BANNED_PROJECT_TAG_IDS:
            desired.append(s)
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    payload = {"tags": [{"id": tid} for tid in desired]}
    print(f"[set_project_tags_exact] PATCH URL={url} payload={payload}")
    resp = requests.patch(url, headers=_zp_headers(access_token), json=payload, timeout=30)
    print(f"[set_project_tags_exact] status={resp.status_code} body={resp.text[:500]}")
    if resp.status_code not in (200, 201):
        raise Exception(f'Falha ao definir tags do projeto: HTTP {resp.status_code} - {resp.text}')

def obter_detalhes_projeto(access_token: str, project_id):
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    params = {"fields": "id,name,status,tags,description"}
    print(f"[obter_detalhes_projeto] URL={url} params={params}")
    r = requests.get(url, headers=_zp_headers(access_token), params=params, timeout=30)
    print(f"[obter_detalhes_projeto] status={r.status_code} body={r.text[:500]}")
    r.raise_for_status()
    try:
        return r.json() if r.text else {}
    except Exception:
        return {}


def _buscar_tasklist_impeditivos_info(access_token: str, project_id: str):
    """
    Procura pela tasklist de Impeditivos no projeto e retorna { id, web_url }.
    Critério: nome contendo 'impedit' (case-insensitive) ou 'impedimento'.
    """
    try:
        base_url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasklists"
        print(f"[_buscar_tasklist_impeditivos_info] URL={base_url}")
        resp = requests.get(base_url, headers=_zp_headers(access_token), timeout=30)
        print(f"[_buscar_tasklist_impeditivos_info] status={resp.status_code} body_sample={resp.text[:500]}")
        if resp.status_code != 200:
            return None
        data = resp.json() if resp.text else {}
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            for key in ["tasklists", "data", "items", "results"]:
                if isinstance(data.get(key), list):
                    items = data[key]
                    break
            if not items and isinstance(data.get('project'), dict):
                proj = data['project']
                for key in ["tasklists", "data", "items"]:
                    if isinstance(proj.get(key), list):
                        items = proj[key]
                        break
        sel = None
        for it in items or []:
            try:
                name = str(it.get('name') or it.get('title') or it.get('tasklist_name') or '')
                if not name:
                    continue
                nm = name.strip().lower()
                if ('impedit' in nm) or ('impediment' in nm) or ('impedimento' in nm) or ('impeditivos' in nm):
                    sel = it
                    break
            except Exception:
                continue
        if not sel:
            return None
        tid = sel.get('id') or sel.get('tasklist_id') or sel.get('entity_id')
        if tid is None:
            return None
        web_url = None
        try:
            link = sel.get('link') or {}
            web_url = link.get('web') or None
        except Exception:
            web_url = None
        return { 'id': str(tid), 'web_url': web_url }
    except Exception as e:
        print(f"[_buscar_tasklist_impeditivos_info] erro: {e}")
        return None


def _contar_tarefas_abertas_na_tasklist(access_token: str, project_id: str, tasklist_id: str) -> int:
    """Conta tarefas não concluídas dentro de uma tasklist específica."""
    total_abertas = 0
    try:
        page = 1
        per_page = 200
        while True:
            url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasklists/{tasklist_id}/tasks"
            params = {"page": page, "per_page": per_page}
            print(f"[_contar_tarefas_abertas_na_tasklist] URL={url} params={params}")
            r = requests.get(url, headers=_zp_headers(access_token), params=params, timeout=30)
            print(f"[_contar_tarefas_abertas_na_tasklist] status={r.status_code} body_sample={r.text[:300]}")
            if r.status_code != 200:
                # Fallback: lista tarefas do projeto e filtra pela tasklist
                url2 = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
                params2 = {"page": page, "per_page": per_page}
                r = requests.get(url2, headers=_zp_headers(access_token), params=params2, timeout=30)
                print(f"[_contar_tarefas_abertas_na_tasklist] fallback status={r.status_code}")
                if r.status_code != 200:
                    break
            data = r.json() if r.text else {}
            items = data.get('tasks') or data.get('data') or []
            if not isinstance(items, list):
                items = []
            count_page = 0
            for t in items:
                try:
                    # Filtra por tasklist quando estamos usando o fallback de /tasks
                    tlid = t.get('tasklist_id') or (t.get('tasklist') or {}).get('id')
                    if tlid is not None and str(tlid) != str(tasklist_id):
                        continue
                    is_completed = t.get('is_completed')
                    if isinstance(is_completed, str):
                        is_completed = is_completed.lower() in {'true', '1', 'yes'}
                    if is_completed is True:
                        continue
                    status_id = None
                    try:
                        st = t.get('status') or {}
                        status_id = str(st.get('id')) if st.get('id') is not None else None
                    except Exception:
                        status_id = None
                    if status_id and status_id == str(STATUS_CONCLUIDO_ID):
                        continue
                    count_page += 1
                except Exception:
                    continue
            total_abertas += count_page
            if len(items) < per_page:
                break
            page += 1
    except Exception as e:
        print(f"[_contar_tarefas_abertas_na_tasklist] erro: {e}")
    return total_abertas

def find_task_by_name(access_token: str, project_id: str, task_name):
    def _normalize(s: str) -> str:
        return (s or '').strip().lower()

    target_norm = _normalize(task_name)

    base_url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
    page = 1
    per_page = 200
    max_pages = 10
    while page <= max_pages:
        params = { 'page': page, 'per_page': per_page }
        print(f"[find_task_by_name] LIST URL={base_url} params={params}")
        resp = requests.get(base_url, headers=_zp_headers(access_token), params=params, timeout=30)
        if resp.status_code != 200:
            print(f"[find_task_by_name] list status={resp.status_code} body={resp.text[:300]}")
            break
        data = resp.json() or {}
        items = data.get('tasks') or data.get('data') or []
        if not isinstance(items, list):
            items = []
        for it in items:
            name = it.get('name') or it.get('title') or it.get('task_name') or ''
            if _normalize(name) == target_norm:
                tid = it.get('id') or it.get('task_id') or it.get('entity_id')
                if tid is not None:
                    print(f"[find_task_by_name] FOUND VIA LIST (exact): {tid}")
                    return str(tid)
        for it in items:
            name = it.get('name') or it.get('title') or it.get('task_name') or ''
            name_norm = _normalize(name)
            if target_norm in name_norm or name_norm in target_norm:
                tid = it.get('id') or it.get('task_id') or it.get('entity_id')
                if tid is not None:
                    print(f"[find_task_by_name] FOUND VIA LIST (contains): {tid} - name='{name}'")
                    return str(tid)
        if len(items) < per_page:
            break
        page += 1

    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/search"
    params = {
        'search_term': task_name,
        'module': 'tasks',
        'per_page': 50
    }
    resp = requests.get(url, headers=_zp_headers(access_token), params=params, timeout=30)
    if resp.status_code != 200:
        raise Exception(f'Falha ao buscar tarefas: HTTP {resp.status_code} - {resp.text}')
    data = resp.json() or {}
    results = data.get('results') or []
    for r in results:
        proj = (r.get('project') or {})
        name = r.get('title') or r.get('name') or ''
        name_norm = _normalize(name)
        if str(proj.get('id')) == str(project_id) and (name_norm == target_norm or target_norm in name_norm or name_norm in target_norm):
            ent = r.get('entity_id')
            if ent is not None:
                print(f"[find_task_by_name] FOUND VIA GLOBAL (fallback): {ent} - name='{name}'")
                return str(ent)
    return None

def add_comment_to_task(access_token: str, project_id: str, task_id: str, content: str):
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}/comments"
    payload = { "comment": content }
    print(f"[add_comment_to_task] URL={url} payload_size={len(content)}")
    resp = requests.post(url, headers=_zp_headers(access_token), json=payload, timeout=30)
    print(f"[add_comment_to_task] status={resp.status_code} body={resp.text[:300]}")
    if resp.status_code not in (200, 201):
        raise Exception(f'Falha ao adicionar comentário na tarefa: HTTP {resp.status_code} - {resp.text}')

def list_task_comments(access_token: str, project_id: str, task_id: str, page: int = 1, per_page: int = 200):
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}/comments"
    params = {"page": page, "per_page": per_page}
    print(f"[list_task_comments] URL={url} params={params}")
    resp = requests.get(url, headers=_zp_headers(access_token), params=params, timeout=30)
    print(f"[list_task_comments] status={resp.status_code} body_sample={resp.text[:500]}")
    if resp.status_code != 200:
        raise Exception(f"Falha ao listar comentários: HTTP {resp.status_code} - {resp.text}")
    return resp.json() or {}

def listar_todos_projetos_ativos(access_token):
    """Lista todos os projetos ativos do Zoho Projects"""
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
    headers = {"Authorization": f"Bearer {access_token}"}
    todos_os_projetos = []
    page_number = 1
    while True:
        params = {"page": page_number, "per_page": 100}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            projetos_da_pagina = response.json()
            if isinstance(projetos_da_pagina, dict):
                projetos_da_pagina = projetos_da_pagina.get("projects", [])
            if not isinstance(projetos_da_pagina, list) or not projetos_da_pagina:
                break
            todos_os_projetos.extend(projetos_da_pagina)
            if len(projetos_da_pagina) < 100:
                break
            page_number += 1
        except requests.exceptions.RequestException as e:
            print(f"ERRO ao listar projetos: {e.response.text if e.response else e}")
            return []
    # Filtra apenas projetos não completos e não cancelados
    projetos_filtrados = []
    for projeto in todos_os_projetos:
        is_completed = projeto.get('is_completed')
        status = projeto.get('status', {}).get('name', '').lower()
        status_id = str(projeto.get('status', {}).get('id', ''))
        if (is_completed not in [True, "true", "True"] and status not in ["completed", "completo"] and status_id != STATUS_CANCELADO_ID):
            projetos_filtrados.append(projeto)
    return projetos_filtrados


def calcular_dias_total_projeto(start_date: str | None, created_time: str | None) -> int | None:
    """
    Calcula o total de dias desde o início do projeto até hoje.
    Prioriza start_date, usa created_time como fallback.
    """
    from datetime import datetime, date
    
    data_referencia = start_date or created_time
    if not data_referencia:
        return None
    
    try:
        # Tenta diferentes formatos de data
        for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y']:
            try:
                if isinstance(data_referencia, str):
                    data_inicio = datetime.strptime(data_referencia.split(' ')[0], fmt).date()
                else:
                    data_inicio = data_referencia
                break
            except ValueError:
                continue
        else:
            return None
        
        hoje = date.today()
        delta = hoje - data_inicio
        return max(0, delta.days)
    except Exception:
        return None


def calcular_dias_na_fase(info_projeto: dict, coluna_atual: str | None) -> int | None:
    """
    Calcula quantos dias o projeto está na fase atual.
    Usa data_ultima_mudanca se disponível, senão usa a data mais apropriada baseada na coluna.
    """
    from datetime import datetime, date
    
    if not coluna_atual:
        return None
    
    # Mapeamento de colunas para campos de data relevantes
    mapeamento_datas = {
        'Aguardando Onboarding': 'data_criacao',
        'Falta Liberar Servidor Infra': 'data_de_onboarding',
        'Aguardando Liberação Servidor': 'data_liberacao_servidor',
        'Aguardando Início Implantação': 'data_inicio_implantacao',
        'Em Implantação': 'data_inicio_implantacao',
        'Aguardando Homologação': 'data_homologacao',
        'Em Homologação': 'data_homologacao',
        'Aguardando Virada': 'data_virada',
        'Aguardando Início OA': 'data_inicio_oa',
        'Em OA': 'data_inicio_oa'
    }
    
    # Primeiro tenta usar data_ultima_mudanca se disponível
    data_mudanca = info_projeto.get('data_ultima_mudanca')
    if data_mudanca:
        try:
            if isinstance(data_mudanca, str):
                # Remove timezone info se presente
                data_mudanca = data_mudanca.split('+')[0].split('T')[0]
                data_ref = datetime.strptime(data_mudanca, '%Y-%m-%d').date()
            else:
                data_ref = data_mudanca
            
            hoje = date.today()
            delta = hoje - data_ref
            return max(0, delta.days)
        except Exception:
            pass
    
    # Fallback: usa a data específica da fase
    campo_data = mapeamento_datas.get(coluna_atual)
    if campo_data:
        data_fase = info_projeto.get(campo_data)
        if data_fase:
            try:
                if isinstance(data_fase, str):
                    # Remove timezone info se presente
                    data_fase = data_fase.split('+')[0].split('T')[0]
                    data_ref = datetime.strptime(data_fase, '%Y-%m-%d').date()
                else:
                    data_ref = data_fase
                
                hoje = date.today()
                delta = hoje - data_ref
                return max(0, delta.days)
            except Exception:
                pass
    
    # Último fallback: usa data de criação
    data_criacao = info_projeto.get('data_criacao') or info_projeto.get('data_inicio')
    if data_criacao:
        try:
            if isinstance(data_criacao, str):
                data_criacao = data_criacao.split('+')[0].split('T')[0]
                data_ref = datetime.strptime(data_criacao, '%Y-%m-%d').date()
            else:
                data_ref = data_criacao
            
            hoje = date.today()
            delta = hoje - data_ref
            return max(0, delta.days)
        except Exception:
            pass
    
    return None


def determinar_coluna_projeto(project_data: dict) -> str:
    """
    Determina a coluna atual do projeto baseado no status e tags usando o mapeamento_colunas.json.
    """
    if not project_data:
        return 'Status Desconhecido'
    
    # Carrega o mapeamento de colunas
    import json
    import os
    
    try:
        mapeamento_path = os.path.join(os.path.dirname(__file__), 'mapeamento_colunas.json')
        with open(mapeamento_path, 'r', encoding='utf-8') as f:
            mapeamento = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar mapeamento_colunas.json: {e}")
        return 'Status Desconhecido'
    
    # Obtém status e tags do projeto
    status_id = str(project_data.get('status', {}).get('id', ''))
    status_name = project_data.get('status', {}).get('name', '').strip()
    tags = project_data.get('tags', [])
    tag_ids = [str(tag.get('id', '')) for tag in tags if isinstance(tag, dict)]
    
    # Verifica se o projeto está concluído ou cancelado
    if project_data.get('is_completed') or status_name.lower() in ('completed', 'finalizado'):
        return 'Finalizado'
    if status_name.lower() in ('cancelled', 'cancelado'):
        return 'Cancelado'
    
    # Procura por correspondência exata no mapeamento
    # Primeiro, verifica combinações específicas de status + tags
    matches_with_tags = []
    matches_without_tags = []
    
    for coluna, config in mapeamento.items():
        # Verifica se o status ID corresponde
        if config.get('zohoStatusId') == status_id:
            tags_to_add = config.get('zohoTagsToAdd', [])
            if tags_to_add:
                # Verifica se pelo menos uma das tags necessárias está presente
                if any(tag_id in tag_ids for tag_id in tags_to_add):
                    matches_with_tags.append(coluna)
            else:
                # Configuração sem tags específicas
                matches_without_tags.append(coluna)
    
    # Prioriza matches com tags específicas
    if matches_with_tags:
        # Se há múltiplas correspondências com tags, usa a primeira
        return matches_with_tags[0]
    elif matches_without_tags:
        # Se não há matches com tags, usa o match sem tags
        return matches_without_tags[0]
    
    # Mapeamento de fallback baseado no status
    status_fallback = {
        '2376502000000020089': 'Aguardando Onboarding',  # Aberto
        '2376502000000020092': 'Aguardando Cronograma',   # Aguardando Cronograma
        '2376502000000020104': 'Projeto Parado',          # Pendência
        '2376502000000020119': 'Em Operação Assistida',   # Em Operação Assistida
        '2376502000000020116': 'Finalizado',              # Completed
        '2376502000000020110': 'Cancelado'                # Cancelled
    }
    
    coluna_fallback = status_fallback.get(status_id)
    if coluna_fallback:
        return coluna_fallback
    
    # Se nada corresponder, retorna status desconhecido
    return 'Status Desconhecido'


def calcular_dias_uteis_desde(data_inicial_str: str) -> int:
    """
    Calcula o número de dias úteis (segunda a sexta) desde uma data até hoje.
    
    Args:
        data_inicial_str: Data inicial em formato ISO (YYYY-MM-DDTHH:MM:SS.sssZ ou YYYY-MM-DD)
    
    Returns:
        int: Número de dias úteis desde a data inicial até hoje
        
    Examples:
        >>> calcular_dias_uteis_desde('2025-10-15T10:30:00.000Z')
        5  # Se hoje for 22/10/2025 (segunda a sexta)
    """
    if not data_inicial_str:
        return 0
    
    try:
        # Parse da data inicial (suporta vários formatos)
        if 'T' in data_inicial_str:
            # Formato ISO completo: 2025-10-15T10:30:00.000Z
            data_inicial = datetime.fromisoformat(data_inicial_str.replace('Z', '+00:00'))
            # Remove timezone para comparação naive
            data_inicial = data_inicial.replace(tzinfo=None)
        else:
            # Formato simples: 2025-10-15
            data_inicial = datetime.fromisoformat(data_inicial_str)
        
        # Remove hora/minuto/segundo para comparar apenas datas
        data_inicial = data_inicial.replace(hour=0, minute=0, second=0, microsecond=0)
        data_hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Se a data inicial é futura, retorna 0
        if data_inicial > data_hoje:
            return 0
        
        # Conta dias úteis (segunda=0 a sexta=4)
        dias_uteis = 0
        data_atual = data_inicial
        
        while data_atual < data_hoje:
            # weekday(): segunda=0, terça=1, ..., domingo=6
            if data_atual.weekday() < 5:  # Segunda a Sexta
                dias_uteis += 1
            data_atual += timedelta(days=1)
        
        return dias_uteis
    
    except Exception as e:
        print(f"⚠️ Erro ao calcular dias úteis desde '{data_inicial_str}': {e}")
        return 0