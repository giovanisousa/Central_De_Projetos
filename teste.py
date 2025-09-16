# -*- coding: utf-8 -*- 

# --- IMPORTAÇÕES BÁSICAS E DO FLASK ---
import os
import json
import time
import traceback
import urllib.parse
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
try:
    from flask_session import Session
except Exception:
    Session = None

# --- BIBLIOTECAS DE API (INSTALE COM 'pip install ...') ---
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import docx
import io
import re

# --- INICIALIZAÇÃO DO FLASK ---
app = Flask(__name__)
# Chave secreta estável para manter sessões mesmo após reloads
_secret = os.environ.get('FLASK_SECRET_KEY')
if not _secret:
    try:
        _base = os.path.abspath(os.path.dirname(__file__))
        _key_path = os.path.join(_base, '.flask_secret_key')
        if os.path.exists(_key_path):
            with open(_key_path, 'r', encoding='utf-8') as f:
                _secret = (f.read() or '').strip()
        if not _secret:
            import secrets
            _secret = secrets.token_hex(32)
            try:
                with open(_key_path, 'w', encoding='utf-8') as f:
                    f.write(_secret)
            except Exception:
                pass
    except Exception:
        _secret = 'dev-secret-change-me'
app.config['SECRET_KEY'] = _secret

# Sessão do lado do servidor (recomendado para produção)
app.config.update({
    'SESSION_TYPE': 'filesystem',           # simples e sem dependências externas
    'SESSION_FILE_DIR': os.path.join(os.path.abspath(os.path.dirname(__file__)), '.flask_session'),
    'SESSION_PERMANENT': True,
    'PERMANENT_SESSION_LIFETIME': timedelta(hours=8),  # expiração de sessão (ajuste conforme política)
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SECURE': False,         # defina True em produção com HTTPS
    'SESSION_COOKIE_SAMESITE': 'Lax',
})
if Session:
    try:
        os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    except Exception:
        pass
    Session(app)

# --- CONFIGURAÇÕES GLOBAIS (COPIADAS DO SEU SCRIPT ORIGINAL) ---

# --- GOOGLE ---
ID_PASTA_PAI_NETRIS = "1I2dSlvfxmphkBdYIjsovCSxizE3Iu-pc"
ID_PASTA_PAI_ANIMATIPACS = "1hBBRW5wYQ1_aw1PWiJ5oEbDURLYcfCbL"
ID_PLANILHA_PROJETOS = "11GzE9NQXKNBgOWArcvX8ErmfzALIApbmh7m8PANUVLc"
NOME_ABA_PLANILHA = "PAINEL"
LINHA_CABECALHO = 12
COLUNA_REFERENCIA_PARA_CONTAR_LINHAS = "Cliente"
COLUNA_SEQUENCIAL_SECUNDARIA = "Num"
ID_PLANILHA_PROJETOS_SECUNDARIA = "12_eu6174i93OUK3CnN_u9CVeH0ZtOaUANC34JHXgBjM"
NOME_ABA_PLANILHA_SECUNDARIA = "Em andamento"
COLUNA_REFERENCIA_SECUNDARIA = "Cliente"
SCOPES_GOOGLE = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/documents', 'openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

# --- ZOHO ---
ZOHO_CLIENT_ID = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
ZOHO_CLIENT_SECRET = "70226965d09b04444346222d9b4846c86a5d31d2fe"
ZOHO_PORTAL_ID = "868230290"
# Para listagem/kanban
STATUS_ABERTO_ID = "2376502000000020089"
STATUS_EM_ANDAMENTO_ID = "2376502000000020092"
STATUS_CANCELADO_ID = "2376502000000020110"
STATUS_FINALIZADO_ID = "2376502000000020116"
STATUS_OPERACAO_ASSISTIDA_ID = "2376502000000020119"
STATUS_AGUARDANDO_CLIENTE_ID = "2376502000000020107"
STATUS_PENDENCIA_ID = "2376502000000020104"
TAG_AGUARDANDO_ONBOARDING_ID = "2376502000001291513"
TAG_AGUARDANDO_INFRA_ID = "2376502000000958355"
TAG_EM_HOMOLOGACAO_ID = "2376502000000983053"
TAG_EM_VIRADA_ID = "2376502000001228741"
TAG_PARADO_ID = "2376502000000983125"

# Domínio web customizado do Zoho Projects (se configurado). Ex.: "https://projects.animati.com.br"
ZOHO_PROJECTS_CUSTOM_WEB_HOST = "https://projects.animati.com.br"
# ID fixo da visualização "somente tarefas em aberto" (não varia entre projetos, segundo o uso atual)
DEFAULT_TASKS_CUSTOM_VIEW_ID = "2376502000000046003"
TAG_AGUARDANDO_ENCERRAMENTO_ID = "2376502000005304184"
STATUS_CONCLUIDO_ID = "2376502000000674703"
# Tags que não devem ser aplicadas em nível de projeto geral
BANNED_PROJECT_TAG_IDS = {"2376502000004311812"}  # Impeditivo (fase)

DONOS_PROJETO = {
    "Giovani de Sousa": "2376502000000057291",
    "Willian dos Anjos": "2376502000000057285"
}
GRUPOS_ZOHO = {
    "PACS": "2376502000000057307",
    "Hibrido": "2376502000000111007",
    "RIS": "2376502000000117069"
}
MODELOS_ZOHO = {
    "Implantação RIS (COM importação e SEM integração)": "2376502000004197548",
    "Implantação RIS (SEM importação e COM integração)": "2376502000004197548",
    "Implantação RIS (SEM importação e SEM integração)": "2376502000004197548",
    "Implantação RIS (COM importação e COM integração)": "2376502000004181530",
    "Implantação RIS + PACS (SEM importação ) - UNIFICADO FINAL": "2376502000004157044",
    "Implantação PACS (COM importação e SEM integração) - UNIFICADO FINAL": "2376502000004131436",
    "Implantação PACS (SEM importação e SEM integração) - UNIFICADO FINAL": "2376502000004114904",
    "Implantação PACS (COM integração e SEM importação) - Unificado FINAL": "2376502000004114562",
    "Implantação PACS ( IMPORTAÇÃO + INTEGRAÇÃO) - UNIFICADO FINAL": "2376502000004050339",
    "Implantação RIS + PACS (COM importação) - UNIFICADO Final": "2376502000001362286"
}

# --- USUÁRIOS PARA MENÇÕES NO ZOHO (token 'zp[@zpuser#USERNUM#Nome]zp') ---
ZOHO_MENTION_USERS = {
    # Preencha aqui os usuários que serão mencionados com frequência
    "William Floriano": {"usernum": "870213453", "name": "William Floriano"},
    "Giovani Sousa": {"usernum": "868816641", "name": "Giovani Sousa"},
    "Roger Machado": {"usernum": "870218464", "name": "Roger Machado"},
    "Carlo Tristão": {"usernum": "870217691", "name": "Carlo Tristão"}
    # Exemplo para adicionar outro usuário:
    # "Outro Nome": {"usernum": "XXXXXXXXX", "name": "Outro Nome"},
}


def zoho_mention_token(usernum: str, name: str) -> str:
    """Gera o token de menção aceito pelo Zoho Projects."""
    return f"zp[@zpuser#{usernum}#{name}]zp"


def zoho_mention_by_name(name: str) -> str:
    """Retorna o token de menção para o nome informado, se mapeado; caso contrário, retorna o próprio nome."""
    info = ZOHO_MENTION_USERS.get(name)
    if not info:
        return name
    return zoho_mention_token(info.get("usernum", ""), info.get("name", name))

def zoho_mentions(names):
    """Gera uma string com múltiplas menções a partir de uma lista de nomes."""
    try:
        return " ".join(zoho_mention_by_name(n) for n in (names or []) if n)
    except Exception:
        return ""

TAREFAS_PARA_CONCLUIR = [t.strip() for t in ["Registrar Projeto Planilha de Andamento", "Criar pastas no Google Drive", "Registrar Projeto na plataforma de gestão de projetos.", "Criação da empresa e acesso ao Zoho Projects"]]
TAREFAS_PARA_ATRIBUIR = [t.strip() for t in ["Alteração da senha de acesso do usuário suporte", "Solicitar definição do cronograma de homologação", "Gerar o ticket de virada do cliente", "Realizar a passagem do cliente para a OA", "Realizar o preenchimento do DPI", "Enviar DPI via e-mail para CS", "Realizar reunião de encerramento com o cliente", "Encaminhar todos os tickets abertos para a equipe de suporte", "Finalizar os grupos de whatsapp", "Finalizar projeto Artia", "Encaminhar mensagem com informações sobre o Plantão", "Criação dos Grupos de Whatsapp"]]
TEMPO_RELATO = {"Registrar Projeto Planilha de Andamento": "00:05", "Criar pastas no Google Drive": "00:10", "Registrar Projeto na plataforma de gestão de projetos.": "00:05", "Criação da empresa e acesso ao Zoho Projects": "00:05"}

# --- CAMINHOS RELATIVOS (ADAPTADO PARA FLASK) ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DOCS_PATH = os.path.join(BASE_DIR, 'templates_doc')
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
ZOHO_TOKEN_PATH = os.path.join(BASE_DIR, 'zoho_refresh_token.txt')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Configura a pasta de uploads após definição
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ================= Helpers de Autenticação Google =================

def build_google_credentials_from_session():
    """Monta credenciais Google a partir da sessão, complementando com client_id/secret
    do credentials.json e atualiza o access token caso esteja expirado.
    Levanta erro claro se não houver refresh_token disponível para refresh.
    """
    info = session.get('credentials')
    if not info or not isinstance(info, dict):
        raise RuntimeError("Credenciais Google ausentes na sessão. Faça login novamente.")

    # Carrega client_id/client_secret do arquivo de credenciais
    client_cfg = {}
    try:
        with open(CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f) or {}
            client_cfg = (data.get('installed') or data.get('web') or {})
    except Exception:
        client_cfg = {}

    # Garante campos necessários para refresh
    info = dict(info)  # cópia
    if not info.get('token_uri'):
        info['token_uri'] = 'https://oauth2.googleapis.com/token'
    if client_cfg:
        cid = client_cfg.get('client_id')
        csecret = client_cfg.get('client_secret')
        if cid and not info.get('client_id'):
            info['client_id'] = cid
        if csecret and not info.get('client_secret'):
            info['client_secret'] = csecret

    # Garante presença do campo 'token' (pode ser None) para evitar erro no __init__
    if 'token' not in info:
        info['token'] = None

    creds = Credentials(**info)

    # Atualiza o token se necessário ou se inválido
    try:
        if not creds.valid:
            if not creds.refresh_token:
                raise RuntimeError(
                    'As credenciais não contêm refresh_token. Refaça o login (com access_type="offline" e prompt="consent").'
                )
            creds.refresh(Request())
            # Persiste de volta na sessão
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

# ================= Helpers de Autenticação Zoho =================

# ================= Helpers de Autenticação Zoho =================

def _zoho_domain() -> str:
    """Retorna o domínio do tenant Zoho (com ou com.br)."""
    return (os.environ.get("ZOHO_DOMAIN") or "com").strip()

def _zp_base() -> str:
    """Base da API do Zoho Projects v3 conforme domínio."""
    return f"https://projectsapi.zoho.{_zoho_domain()}/api/v3"

def _zp_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Accept": "application/json"
    }

def _portal_web_base(access_token: str) -> str | None:
    """Obtém a URL base web do portal (ex.: https://projects.zoho.<dc>/portal/<slug>/).
    Tenta via API; se não conseguir, retorna somente a raiz do projects.<dc>/portal/ para fallback com ID.
    """
    headers = _zp_headers(access_token)
    # Tenta endpoint de portais (lista)
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
    # Fallback: detalhe do portal específico
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
    """Monta raiz pública do Projects conforme data center ou host customizado.
    Prioriza ZOHO_PROJECTS_CUSTOM_WEB_HOST se definido; caso contrário, mapeia o data center do token.
    Retorna com sufixo '/portal/'.
    """
    host = (ZOHO_PROJECTS_CUSTOM_WEB_HOST or '').strip().rstrip('/')
    if host:
        return f"{host}/portal/"
    base_api = _zp_base()
    # Mapeia projectsapi.zoho.<dc> -> projects.zoho.<dc>/portal
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
    """Monta URL da interface web para a tasklist específica no projeto.
    - Se custom_view_id for informado, usa o formato do Zoho UI com /#zp/projects/.../tasks/custom-view/{custom_view_id}/gantt/tasklist-detail/{tasklist_id}
    - Caso contrário, usa o formato mais simples de /#myprojects/{project_id}/tasklists/{tasklist_id}
    """
    if not base_web.endswith('/'):
        base_web += '/'
    if custom_view_id:
        return (
            f"{base_web}#zp/projects/{project_id}/tasks/custom-view/{custom_view_id}/gantt/tasklist-detail/{tasklist_id}?group_by=milestone"
        )
    return f"{base_web}#myprojects/{project_id}/tasklists/{tasklist_id}"

def obter_access_token() -> str:
    """Obtém access_token usando o refresh_token salvo em ZOHO_TOKEN_PATH."""
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

# ==============================================================================
# --- SEÇÃO DE FUNÇÕES DE LÓGICA (COPIADAS E ADAPTADAS) ---
# ==============================================================================
# (As funções de lógica como criar_estrutura_no_drive, atualizar_planilha_google, etc.
# permanecem as mesmas do arquivo anterior. Elas serão chamadas pela rota da API
# depois que a autenticação for verificada.)

def criar_estrutura_no_drive(drive_service, dados):
    try:
        produto_map = {"netRIS": "1", "AnimatiPACS": "2", "netRIS e AnimatiPACS": "3"}
        produto_id = produto_map.get(dados['produto'], "2")
        id_pasta_pai = ID_PASTA_PAI_NETRIS if produto_id in ['1', '3'] else ID_PASTA_PAI_ANIMATIPACS
        nome_pasta_cliente = construir_titulo_projeto(dados)
        print(f"INFO: Criando pasta no Drive: {nome_pasta_cliente}")
        # Evita duplicar pasta: procura por uma pasta existente com mesmo nome no pai
        query = (
            "name = '" + nome_pasta_cliente.replace("'", "\'") + "' and "
            "mimeType = 'application/vnd.google-apps.folder' and "
            f"'{id_pasta_pai}' in parents and trashed = false"
        )
        existentes = drive_service.files().list(q=query, fields="files(id, webViewLink)", pageSize=1).execute().get('files', [])
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
            # Reaproveita subpasta se já existir
            q_sub = (
                "name = '" + nome_subpasta.replace("'", "\'") + "' and "
                "mimeType = 'application/vnd.google-apps.folder' and "
                f"'{id_pasta_cliente}' in parents and trashed = false"
            )
            existentes_sub = drive_service.files().list(q=q_sub, fields="files(id)", pageSize=1).execute().get('files', [])
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
        # Busca a próxima linha vazia APÓS o cabeçalho, na coluna de referência
        range_coluna_ref = f"'{NOME_ABA_PLANILHA}'!{letra_coluna_ref}{LINHA_CABECALHO+1}:{letra_coluna_ref}"
        valores_col_ref = sheets_service.spreadsheets().values().get(
            spreadsheetId=ID_PLANILHA_PROJETOS,
            range=range_coluna_ref
        ).execute().get('values', [])
        proxima_linha_vazia = (LINHA_CABECALHO + len(valores_col_ref) + 1)



        data_selecionada_formatada = dados['start_date'].replace('-', '/')
        # Preenche "Integração":
        if dados.get('integracao_status') == 's':
            integracao_texto = dados.get('integracao_nome') or 'Possui'
        else:
            integracao_texto = 'Não possui'
        dados_para_inserir = {
            "Cliente": dados['codigo_contrato_numero'] + ' - ' + dados['nome_cliente'],
            "Cidade": dados['cidade'],
            "Estado": dados['estado'],
            "Link": f'=HYPERLINK("{url_pasta_drive}"; "DOC")',
            "GP": primeiro_nome_gp,
            "Produtos": dados['produto'],
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
            COLUNA_SEQUENCIAL_SECUNDARIA: novo_num_sequencial, "Recebido": dados['start_date'].replace('-', '/'),
            "Cód CS": dados['codigo_contrato'], "Cliente": dados['nome_cliente'],
            "Cidade": f"{dados['cidade']} - {dados['estado']}", "Sistema": sistema,
            "GP": dados['gp_selecionado'].split()[0], "Concorrente": dados['concorrente']
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
    """Mantida por compatibilidade: delega para obter_access_token sem recursão."""
    return obter_access_token()

def construir_titulo_projeto(dados):
    sufixo_map = {"netRIS": "NR", "AnimatiPACS": "AP", "netRIS e AnimatiPACS": "NR/AP"}
    sufixo = sufixo_map.get(dados['produto'], "")
    return f"{dados['codigo_contrato_numero']} - {dados['nome_cliente']} - {sufixo}"

def construir_descricao(dados):
    pacs_check = "[X]" if 'PACS' in dados['produto'] else "[ ]"; ris_check = "[X]" if 'RIS' in dados['produto'] else "[ ]"
    servidor_local = "(X)" if dados['servidor'] == 'Local' else "( )"; servidor_cloud_animati = "(X)" if dados['servidor'] == 'Cloud Animati' else "( )"; servidor_cloud_terceiros = "(X)" if dados['servidor'] == 'Cloud Terceiros' else "( )"
    integracao_sim = "(X)" if dados['integracao_status'] == 's' else "( )"; integracao_nao = "( )" if dados['integracao_status'] == 's' else "(X)"
    importacao_sim = "(X)" if dados['importacao'] == 's' else "( )"; importacao_nao = "( )" if dados['importacao'] == 's' else "(X)"
    detalhes_integracao = ""
    if dados['integracao_status'] == 's':
        worklist_check = "[X]" if dados['integ_worklist'] else "[ ]"; laudos_check = "[X]" if dados['integ_laudos'] else "[ ]"; docs_check = "[X]" if dados['integ_docs'] else "[ ]"; lab_check = "[X]" if dados['integ_lab'] else "[ ]"; outros_check = "[X]" if dados['integ_outros'] else "[ ]"
        detalhes_integracao = f"<p><b>Se Sim, selecione as integrações:</b></p><ul><li>{worklist_check} Worklist</li><li>{laudos_check} Retorno de Laudos</li><li>{docs_check} Documentos</li><li>{lab_check} Laboratório</li><li>{outros_check} Outros</li></ul>"
    detalhes_importacao = ""
    if dados['importacao'] == 's':
        cadastros_check = "[X]" if dados['import_cadastros'] else "[ ]"; prontuarios_check = "[X]" if dados['import_prontuarios'] else "[ ]"; laudos_check = "[X]" if dados['import_laudos'] else "[ ]"; imagens_check = "[X]" if dados['import_imagens'] else "[ ]"
        detalhes_importacao = f"<p><b>Se Sim, selecione os itens para importação:</b></p><ul><li>{cadastros_check} Cadastros</li><li>{prontuarios_check} Prontuários</li><li>{laudos_check} Laudos</li><li>{imagens_check} Imagens</li></ul>"
    obs_texto = ""
    if dados['observacoes'] and dados['observacoes'].strip():
        obs_formatado = dados['observacoes'].strip().replace('\n', '<br>')
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
    if produto == 'netRIS e AnimatiPACS':
        if importacao: return MODELOS_ZOHO.get("Implantação RIS + PACS (COM importação) - UNIFICADO Final")
        return MODELOS_ZOHO.get("Implantação RIS + PACS (SEM importação ) - UNIFICADO FINAL")
    print("AVISO: Nenhum modelo Zoho para este cenário.")
    return None

def criar_projeto_no_zoho(access_token, dados, template_id):
    print(f"INFO: Criando projeto Zoho para '{dados['nome_cliente']}'...")
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        start_date_obj = datetime.strptime(dados['start_date'], '%d-%m-%Y')
        start_date_api_format = start_date_obj.strftime('%Y-%m-%d')
    except ValueError:
        start_date_api_format = date.today().strftime("%Y-%m-%d")
    payload = {
        "name": construir_titulo_projeto(dados), "description": construir_descricao(dados),
        "start_date": start_date_api_format, "copy_from": str(template_id),
        "project_type": "active", "project_group": {"id": GRUPOS_ZOHO.get("Hibrido" if "e" in dados['produto'] else ("RIS" if "RIS" in dados['produto'] else "PACS"))},
        "owner": {"zpuid": DONOS_PROJETO[dados['gp_selecionado']]}, "is_rollup_project": True,
        "tags": [{"id": 2376502000001291513}]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        projeto_criado = response.json()
        id_do_projeto = projeto_criado.get('id')
        if not id_do_projeto:
            raise Exception(f"Resposta do Zoho OK, mas sem ID do projeto: {projeto_criado}")
        print(f"INFO: Projeto Zoho '{projeto_criado.get('name')}' criado!")
        # Confirma tag após criação (fallback caso o parâmetro tag_ids não aplique)
        try:
            aplicar_tag_ao_projeto(access_token, id_do_projeto, 2376502000001291513)
        except Exception as e:
            print(f"AVISO: Falha ao confirmar tag no projeto: {e}")
        return id_do_projeto
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro da API Zoho: {e.response.text}")

def listar_tarefas_do_projeto(access_token, project_id):
    print(f"INFO: Listando tarefas do projeto {project_id}...")
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
    headers = {"Authorization": f"Bearer {access_token}"}
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

# ===== Helpers de domínio e cabeçalhos Zoho =====
def _zoho_domain():
    return os.environ.get('ZOHO_DOMAIN', 'com').strip()

def _zp_base():
    return f"https://projectsapi.zoho.{_zoho_domain()}/api/v3"

def _zp_rest_base():
    return f"https://projectsapi.zoho.{_zoho_domain()}/restapi"

def _zp_headers(access_token):
    # Forma canônica aceita pela API Zoho
    return {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Accept": "application/json"
    }

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
    """Aplica a tag usando o formato esperado pela API v3: PATCH com campo 'tags' e operação 'add'."""
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
    """Remove uma tag do projeto (API v3: PATCH com 'tags.remove')."""
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
    """Obtém detalhes do projeto (nome, owner, etc.) via API v3."""
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = _zp_headers(access_token)
    try:
        print(f"[obter_detalhes_projeto] URL={url}")
        r = requests.get(url, headers=headers)
        print(f"[obter_detalhes_projeto] status={r.status_code} body={r.text[:500]}")
        r.raise_for_status()
        data = r.json()
        # Alguns responses retornam o projeto direto como objeto; outros usam wrapper 'projects'
        if isinstance(data, dict) and data.get('id'):
            return data
        projects = (data or {}).get('projects', []) if isinstance(data, dict) else []
        if projects:
            return projects[0]
        return {}
    except requests.exceptions.RequestException as e:
        raise Exception(e.response.text if e.response else str(e))

def comentar_na_tarefa(access_token, project_id, task_id, conteudo):
    """Cria um comentário em uma tarefa (REST API)."""
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
    """Atualiza a célula 'Status Principal' na linha que corresponde ao valor da coluna 'Cliente'.
    Torna a busca mais robusta (ignora acentos, caixa e variações de hífen/espaços) e tenta um fallback por nome.
    """
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
        # remove acentos
        s = unicodedata.normalize('NFD', s)
        s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
        # normaliza caixa, espaços e hífens
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

    # 1) Tentativa de match exato (normalizado)
    for idx, row in enumerate(valores):
        cel = (row[0] if row else '')
        if _norm(cel) == alvo_norm:
            linha_encontrada = LINHA_CABECALHO + 1 + idx
            print(f"[atualizar_planilha] Match exato na linha {linha_encontrada}: '{cel}'")
            break

    # 2) Fallback: tenta casar pelo nome do cliente (parte após o primeiro " - ")
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


def registrar_tempo_na_tarefa(access_token, project_id, task_id, gp_zpuid, log_time):
    url = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}/logs/"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "owner_zpuid": str(gp_zpuid), "hours": log_time,
        "date": date.today().strftime("%m-%d-%Y"), "bill_status": "Billable",
        "notes": "Relatado via automação."
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"AVISO: Erro ao registrar tempo para tarefa {task_id}: {e.response.text}")

def processar_tarefas_iniciais(access_token, project_id, gp_zpuid):
    # Aguarda as tarefas ficarem disponíveis (retentativas)
    tentativas, lista_de_tarefas = 0, []
    while tentativas < 6:  # até ~30s
        lista_de_tarefas = listar_tarefas_do_projeto(access_token, project_id)
        if lista_de_tarefas:
            break
        time.sleep(5)
        tentativas += 1
    if not lista_de_tarefas:
        print("AVISO: Nenhuma tarefa encontrada após aguardar. Pulando processamento de tarefas.")
        return
    print(f"INFO: Processando {len(lista_de_tarefas)} tarefas encontradas...")
    for tarefa in lista_de_tarefas:
        try:
            nome_original, task_id = tarefa['name'], tarefa.get('id')
            if not task_id or ' - ' not in nome_original: continue
            nome_limpo = nome_original.split(' - ', 1)[1].strip()
            if nome_limpo in TAREFAS_PARA_CONCLUIR:
                print(f"INFO: Concluindo tarefa: '{nome_limpo}'")
                if atribuir_dono_tarefa(access_token, project_id, task_id, gp_zpuid):
                    if concluir_tarefa(access_token, project_id, task_id):
                        tempo = TEMPO_RELATO.get(nome_limpo)
                        if tempo: registrar_tempo_na_tarefa(access_token, project_id, task_id, gp_zpuid, tempo)
            elif nome_limpo in TAREFAS_PARA_ATRIBUIR:
                print(f"INFO: Atribuindo tarefa: '{nome_limpo}'")
                atribuir_dono_tarefa(access_token, project_id, task_id, gp_zpuid)
        except (IndexError, KeyError) as e:
            print(f"AVISO: Não foi possível processar a tarefa '{tarefa.get('name')}'. Erro: {e}")

# ==============================================================================
# --- SEÇÃO DE ROTAS FLASK (COM AUTENTICAÇÃO) ---
# ==============================================================================

# ====== Funções de listagem/kanban (adaptadas do app_geral.py) ======

def obter_access_token():
    """Obtém e mantém em cache o access token do Zoho usando o refresh token salvo em arquivo.
    Evita múltiplas chamadas simultâneas ao endpoint de token.
    """
    try:
        # Cache simples em variável global
        global _ZOHO_ACCESS_TOKEN_CACHE
        try:
            cache = _ZOHO_ACCESS_TOKEN_CACHE
        except NameError:
            _ZOHO_ACCESS_TOKEN_CACHE = {"token": None, "exp": 0}
            cache = _ZOHO_ACCESS_TOKEN_CACHE
        now = int(time.time())
        if cache.get("token") and now < int(cache.get("exp", 0)):
            return cache["token"]

        if not os.path.exists(ZOHO_TOKEN_PATH):
            print("ERRO: zoho_refresh_token.txt não encontrado.")
            return None
        with open(ZOHO_TOKEN_PATH, 'r') as f:
            refresh_token = f.read().strip()
        if not refresh_token:
            print("ERRO: refresh_token vazio em zoho_refresh_token.txt")
            return None

        url = f"https://accounts.zoho.{_zoho_domain()}/oauth/v2/token"
        payload = {
            "refresh_token": refresh_token,
            "client_id": ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "grant_type": "refresh_token"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url, data=payload, headers=headers, timeout=20)
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException:
            body = None
            try:
                body = response.json()
            except Exception:
                body = response.text
            print(f"ERRO ao obter Access Token: status={response.status_code} body={body}")
            return None

        data = response.json()
        token = data.get("access_token")
        expires_in = int(data.get("expires_in", 3600))
        if not token:
            print(f"ERRO: resposta sem access_token: {data}")
            return None
        # Atualiza cache (com margem de segurança de 60s)
        cache["token"] = token
        cache["exp"] = now + max(60, expires_in - 60)

        # Se a Zoho devolver um novo refresh_token, atualiza o arquivo
        if 'refresh_token' in data and data['refresh_token']:
            try:
                with open(ZOHO_TOKEN_PATH, 'w') as f:
                    f.write(data['refresh_token'])
            except Exception as e:
                print(f"AVISO: não foi possível atualizar zoho_refresh_token.txt: {e}")
        return token
    except Exception as e:
        print(f"ERRO inesperado ao obter Access Token: {e}")
        return None




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
    # Aguardando Encerramento: status Operação Assistida + tag específica
    if status_id == STATUS_OPERACAO_ASSISTIDA_ID and TAG_AGUARDANDO_ENCERRAMENTO_ID in tag_ids:
        return "Aguardando Encerramento"
    if status_id == STATUS_AGUARDANDO_CLIENTE_ID and TAG_PARADO_ID in tag_ids:
        return "Projeto Parado"
    if status_id == STATUS_PENDENCIA_ID and TAG_PARADO_ID in tag_ids:
        return "Projeto Parado"
    status_map = {
        STATUS_EM_ANDAMENTO_ID: "Em Andamento",
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

def obter_data_ultima_mudanca_status_ou_tag(project_id, access_token):
    """Busca nos edits do projeto a última alteração de Status ou Tag e retorna a data (date) dessa alteração.
    Retorna None se não encontrar ou em erro.
    """
    try:
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/edits"
        headers = _zp_headers(access_token)
        params = {"index": 1, "range": 50}
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        # Normaliza lista de itens de edição/atividades
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
            # Trata sufixo 'Z' (UTC)
            if s.endswith('Z'):
                # tenta com milissegundos e sem
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
            # fallback: tenta apenas a porção de data ISO
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
            # Considera alterações que mencionem status ou tag(s)
            if ("status" in item_text) or ("tag" in item_text) or ("tags" in item_text):
                # Preferir action_time no nível do item
                ts = None
                if isinstance(item, dict):
                    ts = item.get('action_time') or item.get('time')
                # Procura campos de data comuns
                if ts is None:
                    for key in [
                        "updated_time", "modified_time", "modified_at", "time", "date", "created_time", "log_time", "timestamp"
                    ]:
                        if isinstance(item, dict) and key in item:
                            ts = item[key]
                            break
                # Busca também dentro de sub-objetos comuns
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
        'em andamento': 'Em Andamento',
        'finalizado': 'Finalizado',
        'operação assistida': 'Em Operação Assistida',
        'em operação assistida': 'Em Operação Assistida',
        'cancelado': 'Cancelado',
        # Alguns ambientes usam 'ativo' como aberto; mapeamos para Em Andamento por aproximação
        'ativo': 'Em Andamento',
    }
    return mapa.get(s)

def map_etiquetas_to_coluna_por_ids(tags_str: str) -> str:
    """Recebe a string textual do new_value das etiquetas (ex: "[Implantação, Em andamento]") e
    mapeia para coluna usando APENAS os IDs de tag definidos em mapeamento_colunas.json.
    Regras:
    - Apenas etiquetas cujo nome conseguimos mapear para um ID conhecido serão consideradas.
    - Se nenhuma etiqueta do evento corresponder a um ID presente no mapeamento, retorna None.
    """
    if not tags_str:
        return None

    # Mapa de nome de etiqueta -> ID (pelas constantes configuradas no app)
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

    # Carrega mapeamento: coluna -> lista de tag IDs
    mapeamento = get_mapeamento_colunas()
    colunas_por_tag_id = {}
    for coluna, cfg in (mapeamento or {}).items():
        for tag_id in cfg.get('zohoTagsToAdd', []) or []:
            colunas_por_tag_id[str(tag_id)] = coluna

    # Extrai nomes de etiquetas do texto do new_value
    try:
        s = str(tags_str).strip()
        if s.startswith('[') and s.endswith(']'):
            s = s[1:-1]
        nomes = [p.strip().lower() for p in s.split(',') if p.strip()]
    except Exception:
        nomes = [str(tags_str).strip().lower()]

    # Converte nomes para IDs; filtra apenas IDs que apareçam no mapeamento
    for nome in nomes:
        tag_id = nome_tag_para_id.get(nome)
        if not tag_id:
            continue
        coluna = colunas_por_tag_id.get(str(tag_id))
        if coluna:
            return coluna
    return None

def obter_data_ultima_mudanca_etiqueta_para_coluna(project_id, access_token, coluna_alvo: str):
    """Encontra a última action_time onde houve mudança de Etiquetas (field_name == 'Etiquetas')
    e o new_value mapeia para a coluna alvo informada.
    """
    try:
        # Usa busca robusta com faixas menores e paginação limitada
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

        coluna_alvo_norm = (coluna_alvo or '').strip()
        best_date = None
        for item in items or []:
            if not isinstance(item, dict):
                continue
            edits = item.get('edits') or []
            if not isinstance(edits, list):
                continue
            # Verifica alterações de Etiquetas
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


# ====== Utilitários robustos para histórico de edits ======

def _normalize_edits_response(data):
    """Normaliza diferentes formatos possíveis retornados pelo Zoho para uma lista de edits."""
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
    """Busca histórico de edits do projeto com tolerância a 400, testando faixas menores.
    Retorna lista de itens normalizados somando as páginas.
    """
    headers = _zp_headers(access_token)
    base_url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/edits"
    ranges = [20, 10, 5]
    for rg in ranges:
        try:
            collected = []
            for page in range(1, max_pages + 1):
                params = {"index": page, "range": rg}
                resp = requests.get(base_url, headers=headers, params=params, timeout=20)
                if resp.status_code == 400:
                    # tenta com faixa menor
                    print(f"[edits] 400 com range={rg} page={page} -> tentando range menor")
                    collected = []
                    break
                resp.raise_for_status()
                items = _normalize_edits_response(resp.json())
                if not isinstance(items, list) or not items:
                    break
                collected.extend(items)
                if len(items) < rg:
                    break
            if collected:
                return collected
        except Exception as e:
            print(f"[edits] falha range={rg}: {e}")
            continue
    return []

def obter_data_ultima_mudanca_status_ou_tag(project_id, access_token):
    """Obtém a data da última mudança relevante (status ou etiquetas) do projeto via edits.
    Se não conseguir buscar/parsear, retorna None.
    """
    try:
        items = _fetch_project_edits(access_token, project_id, max_pages=3)
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


# ====== Mapeamento de colunas (carregado de mapeamento_colunas.json) ======
_MAPPINGS_CACHE = None


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
    """Encontra a última action_time onde houve mudança de Status (field_name == 'Status')
    e o new_value corresponde ao status da coluna alvo conforme mapeamento_colunas.json.
    """
    try:
        mapeamento = get_mapeamento_colunas()
        cfg = mapeamento.get(coluna_alvo or '') or {}
        status_id_alvo = str(cfg.get('zohoStatusId') or '')
        if not status_id_alvo:
            return None

        # Mapa de nomes de status -> IDs conforme configuração conhecida
        nome_status_para_id = {
            'aberto': STATUS_ABERTO_ID,
            'ativo': STATUS_ABERTO_ID,
            'em andamento': STATUS_EM_ANDAMENTO_ID,
            'finalizado': STATUS_FINALIZADO_ID,
            'operação assistida': STATUS_OPERACAO_ASSISTIDA_ID,
            'em operação assistida': STATUS_OPERACAO_ASSISTIDA_ID,
            'cancelado': STATUS_CANCELADO_ID,
        }

        # Usa busca robusta com faixas menores e paginação limitada
        items = _fetch_project_edits(access_token, project_id, max_pages=3)

        # Função local para data
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
    """Calcula dias na fase com base na última mudança de status/tag.
    Se não for possível obter a data pelos edits, faz fallback para data de início/criação.
    """
    try:
        # Tenta pelo histórico de edits do Zoho, se os parâmetros estiverem disponíveis
        if project_id and access_token:
            ultima_data = obter_data_ultima_mudanca_status_ou_tag(project_id, access_token)
            if ultima_data:
                dias = (date.today() - ultima_data).days
                # Log de verificação para o projeto específico solicitado
                if str(project_id) == "2376502000000213310":
                    print(f"DEBUG dias_na_fase: projeto={project_id} ultima_data={ultima_data} dias={dias}")
                if dias < 0:
                    return "Futuro"
                elif dias == 0:
                    return "Hoje"
                else:
                    return f"{dias}d"

        # Fallback: usa data de início ou criação do projeto
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


# Utilitário: total de dias do projeto (data de início -> hoje)

def calcular_dias_total_projeto(data_inicio_str: str, data_criacao_str: str) -> str:
    try:
        def parse_date(s):
            if not s:
                return None
            s = str(s).strip()
            # Tenta formatos comuns (YYYY-MM-DD e ISO)
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(s[:19], fmt).date() if 'T' in s or ' ' in s else datetime.strptime(s, fmt).date()
                except Exception:
                    continue
            # Fallback: pega só a parte da data
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

# ====== Rotas de Kanban (adaptadas do app_geral.py) ======

# Cache simples em memória para dias_na_fase para reduzir chamadas pesadas
_DIAS_FASE_CACHE = {}
# Estrutura: { project_id: { 'valor': 'Xd|Hoje|Futuro|N/D', 'ts': epoch_seconds } }
_CACHE_TTL_SECONDS = 90

@app.route('/api/carregar_projetos', methods=['POST'])
def carregar_projetos():
    try:
        data = request.json
        gp_selecionado = data.get('gp')
        if not gp_selecionado or gp_selecionado not in DONOS_PROJETO:
            return jsonify({"erro": "GP inválido"}), 400
        id_do_gp = DONOS_PROJETO[gp_selecionado]
        access_token = obter_access_token()
        if not access_token:
            return jsonify({"erro": "Erro de autenticação"}), 401
        lista_completa_projetos = listar_todos_projetos_ativos(access_token)
        projetos_do_gp = [p for p in lista_completa_projetos if p.get('owner', {}).get('zpuid') == id_do_gp]
        projetos_por_status = {}
        colunas_validas = {
            "Aguardando Onboarding",
            "Falta Liberar Servidor Infra",
            "Em Andamento",
            "Em Homologação",
            "Em Virada",
            "Em Operação Assistida",
            "Aguardando Encerramento",
            "Projeto Parado",
            "Finalizado",
            "Cancelado",
            "Status Desconhecido"
        }
        projetos_nao_mapeados = []
        for projeto in projetos_do_gp:
            status_kanban = determinar_coluna_projeto(projeto)
            if status_kanban not in projetos_por_status:
                projetos_por_status[status_kanban] = []
            cliente = (
                projeto.get('client_company', {}).get('name')
                or projeto.get('client', {}).get('name')
                or projeto.get('client_name')
                or "Cliente não informado"
            )
            info_projeto = {
                'id': projeto.get('id'),
                'nome': projeto.get('name'),
                'cliente': cliente,
                'gp': projeto.get('owner', {}).get('name', 'GP não informado'),
                'data_inicio': projeto.get('start_date', ''),
                'data_criacao': projeto.get('created_time', ''),
                'data_inicio_formatada': projeto.get('start_date', ''),
                # Inicialmente vazio; cliente busca por projeto via endpoint dedicado e cache
                'dias_na_fase': '',
                # Total de dias do projeto: sempre calculado localmente pela data de início ou criação
                'dias_total': calcular_dias_total_projeto(projeto.get('start_date', ''), projeto.get('created_time', '')),
                'status_atual': status_kanban
            }
            projetos_por_status[status_kanban].append(info_projeto)
            # Coleta para auditoria se cair em coluna desconhecida
            if status_kanban not in colunas_validas:
                status_id = str(projeto.get('status', {}).get('id', ''))
                status_nome = str(projeto.get('status', {}).get('name', ''))
                tag_ids = [str(t.get('id', '')) for t in (projeto.get('tags') or [])]
                projetos_nao_mapeados.append({
                    'id': projeto.get('id'),
                    'nome': projeto.get('name'),
                    'status_id': status_id,
                    'status_nome': status_nome,
                    'tags': tag_ids,
                    'status_kanban': status_kanban,
                })
        if projetos_nao_mapeados:
            print("==== AUDITORIA: Projetos fora do mapeamento ====")
            for p in projetos_nao_mapeados:
                print(f"ID={p['id']} | Nome={p['nome']} | Status={p['status_nome']} ({p['status_id']}) | Tags={p['tags']} | Mapeado como='{p['status_kanban']}'")
            print("================================================")
        for status, projetos in projetos_por_status.items():
            projetos_por_status[status] = sorted(projetos, key=lambda p: p['nome'])
        return jsonify({
            "sucesso": True,
            "projetos": projetos_por_status,
            "total": len(projetos_do_gp)
        })
    except Exception as e:
        print(f"Erro ao carregar projetos: {e}")
        return jsonify({"erro": str(e)}), 500

# ================= Indicador de impeditivos =================

def _buscar_tasklist_impeditivos_info(access_token, project_id):
    """Retorna dict com {id, web_url} da tasklist '00.01 - Itens impeditivos de virada' do projeto (case-insensitive)."""
    try:
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasklists"
        headers = _zp_headers(access_token)
        page = 1
        per_page = 100
        alvo = '00.01 - itens impeditivos de virada'
        while True:
            params = {"page": page, "per_page": per_page}
            r = requests.get(url, headers=headers, params=params, timeout=20)
            if r.status_code == 400:
                # Trata projeto sem permissão/sem tasklists de maneira graciosa
                print(f"[impeditivos] LIST 400 project_id={project_id} body={r.text[:300]}")
                return None
            r.raise_for_status()
            data = r.json()
            listas = data.get('tasklists') if isinstance(data, dict) else data
            if not isinstance(listas, list):
                listas = []
            for tl in listas:
                nome = str((tl.get('name') or tl.get('title') or '')).strip().lower()
                if nome == alvo:
                    # id pode vir como int/str
                    tl_id = str(tl.get('id') or tl.get('tasklist_id') or '')
                    # Muitos recursos retornam 'link': {'web': '...'}
                    web_url = ''
                    try:
                        web_url = (tl.get('link') or {}).get('web') or tl.get('url') or ''
                    except Exception:
                        web_url = ''
                    # Fallback: tenta buscar detalhes da tasklist específica para obter o link web
                    if not web_url and tl_id:
                        try:
                            det_url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasklists/{tl_id}"
                            rr = requests.get(det_url, headers=headers, timeout=20)
                            if rr.status_code == 400:
                                print(f"[impeditivos] DETAIL 400 project_id={project_id} tl_id={tl_id} body={rr.text[:300]}")
                            else:
                                rr.raise_for_status()
                                det = rr.json()
                                node = det.get('tasklist') if isinstance(det, dict) else None
                                if isinstance(node, dict):
                                    web_url = ((node.get('link') or {}).get('web')) or node.get('url') or ''
                        except Exception as _:
                            pass
                    return {"id": tl_id, "web_url": web_url}
            if len(listas) < per_page:
                break
            page += 1
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao listar tasklists do projeto {project_id}: {e.response.text if e.response else e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao buscar tasklist impeditivos do projeto {project_id}: {e}")
        return None

def _contar_tarefas_abertas_na_tasklist(access_token, project_id, tasklist_id):
    """Conta tarefas abertas pertencentes à tasklist informada, percorrendo a paginação."""
    try:
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
        headers = _zp_headers(access_token)
        page = 1
        per_page = 200
        total_abertas = 0
        while True:
            params = {"page": page, "per_page": per_page}
            r = requests.get(url, headers=headers, params=params, timeout=25)
            r.raise_for_status()
            data = r.json()
            tarefas = data.get('tasks') if isinstance(data, dict) else data
            if not isinstance(tarefas, list) or not tarefas:
                break
            for t in tarefas:
                # Identificar a tasklist da tarefa
                tl_id = None
                try:
                    tl_id = t.get('tasklist', {}).get('id') or t.get('tasklist_id')
                except Exception:
                    tl_id = t.get('tasklist_id')
                if str(tl_id) != str(tasklist_id):
                    continue
                # Determinar se está aberta
                is_completed = t.get('is_completed')
                status_name = (t.get('status', {}) or {}).get('name', '')
                if is_completed in [True, 'True', 'true']: # concluída
                    continue
                if str(status_name).strip().lower() in ['completed', 'concluída', 'finalizado', 'closed']:
                    continue
                total_abertas += 1
            if len(tarefas) < per_page:
                break
            page += 1
        return total_abertas
    except requests.exceptions.RequestException as e:
        print(f"Erro ao listar tarefas do projeto {project_id}: {e.response.text if e.response else e}")
        return 0
    except Exception as e:
        print(f"Erro inesperado ao contar tarefas abertas em tasklist {tasklist_id} do projeto {project_id}: {e}")
        return 0


@app.route('/api/impeditivos/<project_id>', methods=['GET'])
def api_impeditivos(project_id):
    try:
        # Usa token Zoho que também define a base dinâmica (_map_projects_base)
        access_token = obter_access_token_zoho()
        if not access_token:
            return jsonify({"erro": "Erro de autenticação"}), 401
        info = _buscar_tasklist_impeditivos_info(access_token, project_id)
        if not info or not info.get('id'):
            # Se a lista não existe, considera 0 abertos
            return jsonify({"project_id": project_id, "count": 0, "has_impediments": False, "web_url": None})
        count = _contar_tarefas_abertas_na_tasklist(access_token, project_id, info['id'])
        web_url = info.get('web_url') or None
        if not web_url:
            # Construção da URL web a partir do portal
            base_web = _portal_web_base(access_token) or _projects_web_root()
            if base_web:
                # Se base_web já incluir '/portal/<slug>/', usa direto; caso contrário, anexa portal id
                if not base_web.rstrip('/').endswith('/portal') and '/portal/' in base_web:
                    web_base_final = base_web
                else:
                    web_base_final = base_web.rstrip('/') + f"/{ZOHO_PORTAL_ID}/"
                # Usa a visualização fixa "somente tarefas em aberto" se disponível
                web_url = _compose_tasklist_web_url(web_base_final, project_id, info['id'], DEFAULT_TASKS_CUSTOM_VIEW_ID)
        return jsonify({"project_id": project_id, "count": count, "has_impediments": count > 0, "web_url": web_url})
    except Exception as e:
        print(f"Erro no endpoint impeditivos: {e}")
        return jsonify({"erro": str(e)}), 500


@app.route('/api/dias-na-fase/<project_id>', methods=['GET'])
def api_dias_na_fase(project_id):
    try:
        coluna = request.args.get('coluna')  # coluna alvo (opcional)
        hint = request.args.get('hint')  # quando '1', usar a coluna como dica explicitamente
        use_coluna = (hint == '1' and bool(coluna))

        # Cache: por projeto (genérico) ou por projeto+coluna quando usar dica
        key = f"{project_id}|{coluna}" if use_coluna else f"{project_id}"
        now = int(time.time())
        ent = _DIAS_FASE_CACHE.get(key)
        if ent and (now - ent.get('ts', 0) <= _CACHE_TTL_SECONDS):
            return jsonify({"project_id": project_id, "dias_na_fase": ent.get('valor', 'N/D')})

        # Sempre usar o token Zoho unificado (define a base correta e Authorization)
        access_token = obter_access_token_zoho()
        if not access_token:
            return jsonify({"erro": "Erro de autenticação"}), 401

        # Se uso de coluna foi explicitamente solicitado, tenta pela mudança de status/etiqueta para essa coluna
        valor = None
        if use_coluna:
            d = obter_data_ultima_mudanca_status_para_coluna(project_id, access_token, coluna)
            if not d:
                d = obter_data_ultima_mudanca_etiqueta_para_coluna(project_id, access_token, coluna)
            if d:
                dias = (date.today() - d).days
                valor = "Hoje" if dias == 0 else ("Futuro" if dias < 0 else f"{dias}d")

        # Se não conseguiu via coluna/status/etiqueta (ou coluna não usada), fallback genérico
        if not valor:
            try:
                proj_url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
                rproj = requests.get(proj_url, headers=_zp_headers(access_token), params={"fields": "start_date,created_time"}, timeout=20)
                if rproj.status_code == 200:
                    pdata = rproj.json() or {}
                    if isinstance(pdata, dict):
                        node = pdata.get('project') if isinstance(pdata.get('project'), dict) else pdata
                        start_date = (node.get('start_date') or node.get('start_date_string') or '') if isinstance(node, dict) else ''
                        created_time = (node.get('created_time') or node.get('created_time_string') or '') if isinstance(node, dict) else ''
                        info_min = { 'data_inicio': start_date, 'data_criacao': created_time }
                        valor = calcular_dias_na_fase(info_min, None)
            except Exception:
                pass
            if not valor:
                info_min = { 'data_inicio': '', 'data_criacao': '' }
                valor = calcular_dias_na_fase(info_min, None, project_id=project_id, access_token=access_token)

        # Atualiza cache (se valor não definido por algum motivo, mantém 'N/D')
        if not valor:
            valor = 'N/D'
        _DIAS_FASE_CACHE[key] = { 'valor': valor, 'ts': now }
        return jsonify({"project_id": project_id, "dias_na_fase": valor})
    except Exception as e:
        print(f"Erro no endpoint dias-na-fase: {e}")
        return jsonify({"erro": str(e)}), 500


# ===== Movimentação de projeto (atualiza cache e planilha) =====

def _invalidate_dias_cache(project_id: str):
    try:
        keys = list(_DIAS_FASE_CACHE.keys())
        for k in keys:
            if k == str(project_id) or k.startswith(f"{project_id}|"):
                _DIAS_FASE_CACHE.pop(k, None)
    except Exception:
        pass


def _a1_col_letter(idx0: int) -> str:
    # 0 -> A, 1 -> B, ...
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

def _update_status_planilha_principal(sheets_service, cliente_key: str, novo_status: str, status_header_candidates=None) -> bool:
    # Lê cabeçalho
    headers_range = f"{NOME_ABA_PLANILHA}!A{LINHA_CABECALHO}:ZZ{LINHA_CABECALHO}"
    resp = sheets_service.spreadsheets().values().get(spreadsheetId=ID_PLANILHA_PROJETOS, range=headers_range).execute()
    headers = (resp.get('values') or [[]])[0]
    if not headers:
        raise RuntimeError('Cabeçalho não encontrado na planilha principal.')

    # Descobre índices de colunas
    if status_header_candidates is None:
        status_header_candidates = ["Status Principal", "Status", "STATUS PRINCIPAL", "STATUS"]
    idx_map = _find_header_indexes(headers, [COLUNA_REFERENCIA_PARA_CONTAR_LINHAS] + status_header_candidates)
    if COLUNA_REFERENCIA_PARA_CONTAR_LINHAS not in idx_map:
        raise RuntimeError(f"Coluna de referência '{COLUNA_REFERENCIA_PARA_CONTAR_LINHAS}' não encontrada no cabeçalho.")
    # Escolhe a primeira disponível para status
    status_idx = None
    for nm in status_header_candidates:
        if nm in idx_map:
            status_idx = idx_map[nm]
            break
    if status_idx is None:
        raise RuntimeError("Coluna de Status não encontrada (tente ajustar os nomes candidatos).")

    cliente_idx = idx_map[COLUNA_REFERENCIA_PARA_CONTAR_LINHAS]
    cliente_col = _a1_col_letter(cliente_idx)

    # Busca linhas da coluna Cliente
    valores_cli_range = f"{NOME_ABA_PLANILHA}!{cliente_col}{LINHA_CABECALHO+1}:{cliente_col}"
    vals = sheets_service.spreadsheets().values().get(spreadsheetId=ID_PLANILHA_PROJETOS, range=valores_cli_range).execute()
    linhas = (vals.get('values') or [])

    # Procura a linha do cliente (match exato)
    linha_encontrada = None
    alvo = (cliente_key or '').strip()
    for i, row in enumerate(linhas, start=LINHA_CABECALHO + 1):
        val = (row[0] if row else '').strip()
        if val == alvo:
            linha_encontrada = i
            break
    if not linha_encontrada:
        raise RuntimeError(f"Cliente '{cliente_key}' não encontrado na planilha principal.")

    # Atualiza célula do status
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

def obter_ipv6_do_drive(drive_service, id_pasta_cliente):
    """
    Busca por um arquivo .docx na pasta 'Infraestrutura' de um cliente no Google Drive,
    extrai um endereço IPv6 e o retorna.
    """
    try:
        print(f"DEBUG: Iniciando busca de IPv6 na pasta do cliente com ID: {id_pasta_cliente}")
        # 1. Encontrar a subpasta 'Infraestrutura'
        query_infra = f"name = 'Infraestrutura' and mimeType = 'application/vnd.google-apps.folder' and '{id_pasta_cliente}' in parents and trashed = false"
        results_infra = drive_service.files().list(q=query_infra, fields="files(id, name)").execute()
        items_infra = results_infra.get('files', [])
        if not items_infra:
            print(f"DEBUG: Pasta 'Infraestrutura' não encontrada na pasta do cliente com ID '{id_pasta_cliente}'.")
            return None
        id_pasta_infra = items_infra[0]['id']
        print(f"DEBUG: Pasta 'Infraestrutura' encontrada (ID: {id_pasta_infra})")

        # 2. Listar arquivos .docx na pasta 'Infraestrutura'
        query_docx = f"mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' and '{id_pasta_infra}' in parents and trashed = false"
        results_docx = drive_service.files().list(q=query_docx, fields="files(id, name)").execute()
        files_docx = results_docx.get('files', [])
        print(f"DEBUG: Arquivos .docx encontrados na pasta 'Infraestrutura': {[f['name'] for f in files_docx]}")
        
        # 3. Filtrar o arquivo correto (que não contém 'broker')
        target_file = None
        for file in files_docx:
            if 'broker' not in file['name'].lower():
                target_file = file
                break
        
        if not target_file:
            print("DEBUG: Nenhum arquivo .docx válido (sem 'broker' no nome) encontrado.")
            return None
        
        print(f"DEBUG: Arquivo .docx alvo selecionado: {target_file['name']} (ID: {target_file['id']})")

        # 4. Baixar e ler o conteúdo do arquivo .docx
        request_download = drive_service.files().get_media(fileId=target_file['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_download)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        fh.seek(0)
        document = docx.Document(fh)
        
        # 5. Extrair o IPv6 de parágrafos
        for para in document.paragraphs:
            if 'vpn animati' in para.text.lower():
                match = re.search(r'(fd[0-9a-fA-F:]+)', para.text)
                if match:
                    ipv6 = match.group(1)
                    print(f"DEBUG: IPv6 encontrado em parágrafo: {ipv6}")
                    return ipv6

        # 6. Extrair o IPv6 de tabelas
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


@app.route('/')
def index():
    if 'credentials' not in session:
        return render_template('index.html', logged_in=False, gps=list(DONOS_PROJETO.keys()), cores_colunas={
        "Aguardando Onboarding": "#6c757d",
        "Falta Liberar Servidor Infra": "#E67E22",
        "Em Andamento": "#2ECC71",
        "Em Homologação": "#1ABC9C",
        "Em Virada": "#1ABC9C",
        "Em Operação Assistida": "#3498DB",
        "Aguardando Encerramento": "#8B5CF6",
        "Finalizado": "#27AE60",
        "Projeto Parado": "#DC143C",
        "Cancelado": "#b5b5b5",
        "Status Desconhecido": "#95A5A6"
    })
    
    # Usuário logado: segue normalmente
    return render_template('index.html', logged_in=True, user_email=session.get('user_email'), gps=list(DONOS_PROJETO.keys()), cores_colunas={
        "Aguardando Onboarding": "#6c757d",
        "Falta Liberar Servidor Infra": "#E67E22",
        "Em Andamento": "#2ECC71",
        "Em Homologação": "#1ABC9C",
        "Em Virada": "#1ABC9C",
        "Em Operação Assistida": "#3498DB",
        "Aguardando Encerramento": "#8B5CF6",
        "Finalizado": "#27AE60",
        "Projeto Parado": "#DC143C",
        "Cancelado": "#b5b5b5",
        "Status Desconhecido": "#95A5A6"
    })

@app.route('/login')
def login():
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES_GOOGLE,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
    session['state'] = state
    # Define a sessão como permanente para aplicar PERMANENT_SESSION_LIFETIME
    session.permanent = True
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    # Recupera state salvo, se existir; se não, tenta usar o state devolvido pelo Google
    saved_state = session.get('state')
    incoming_state = request.args.get('state')
    state = saved_state or incoming_state

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES_GOOGLE,
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    # Preserva refresh_token já existente se o Google não retornar um novo
    prev_refresh = (session.get('credentials') or {}).get('refresh_token') if isinstance(session.get('credentials'), dict) else None
    refresh_token = credentials.refresh_token or prev_refresh
    session['credentials'] = {
        # Evita guardar token de acesso em sessão (curta duração); manteremos refresh_token e metadados
        'refresh_token': refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
    }
    # Reconstrói Credentials temporárias só para buscar userinfo
    temp_creds = Credentials(
        token=credentials.token,
        refresh_token=refresh_token,
        token_uri=credentials.token_uri,
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        scopes=credentials.scopes,
    )
    user_info_service = build('oauth2', 'v2', credentials=temp_creds)
    user_info = user_info_service.userinfo().get().execute()
    session['user_email'] = user_info.get('email')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/criar-projeto', methods=['POST'])
def api_criar_projeto():
    if 'credentials' not in session:
        return jsonify({"status": "error", "message": "Usuário não autenticado."}),
    
    try:
        creds = build_google_credentials_from_session()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Falha nas credenciais Google: {e}"}), 401
    
    temp_deip_path = None
    try:
        if 'deip_pdf' not in request.files:
            return jsonify({"status": "error", "message": "Arquivo DEIP é obrigatório."}),
        
        deip_file = request.files['deip_pdf']
        dados = request.form.to_dict()

        # Normaliza campos do formulário esperados pela lógica
        dados['integracao_status'] = dados.get('integracao', 'n')
        checkbox_fields = [
            'integ_worklist','integ_laudos','integ_docs','integ_lab','integ_outros',
            'import_cadastros','import_prontuarios','import_laudos','import_imagens'
        ]
        for f in checkbox_fields:
            dados[f] = (f in request.form)
        
        filename = secure_filename(deip_file.filename)
        temp_deip_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        deip_file.save(temp_deip_path)
        # Guarda caminhos para uso no Drive
        dados['caminho_deip'] = temp_deip_path
        dados['caminho_deip_original'] = deip_file.filename or filename
        dados['codigo_contrato_numero'] = dados['codigo_contrato'].split('/')[0].strip()
        
        # --- Execução da Lógica Principal ---
        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        # Garante que o arquivo existe antes do upload
        if not os.path.exists(dados['caminho_deip']):
            raise Exception(f"Arquivo DEIP não encontrado no servidor: {dados['caminho_deip']}")
        
        # Evita duplicação: usa uma chave idempotente por contrato+cliente+produto
        chave_idem = f"{dados['codigo_contrato_numero']}|{dados['nome_cliente']}|{dados['produto']}".lower()
        if 'execucoes' not in session:
            session['execucoes'] = {}
        if session['execucoes'].get(chave_idem) == 'running':
            return jsonify({"status":"error","message":"Uma execução já está em andamento para este cliente/contrato."}),
        session['execucoes'][chave_idem] = 'running'
        try:
            url_nova_pasta = criar_estrutura_no_drive(drive_service, dados)
            atualizar_planilha_principal(sheets_service, dados, url_nova_pasta)
            atualizar_planilha_secundaria(sheets_service, dados)
            
            id_do_novo_projeto = None
            template_id = escolher_template_zoho(dados)
            if template_id:
                zoho_access_token = obter_access_token_zoho()
                id_do_novo_projeto = criar_projeto_no_zoho(zoho_access_token, dados, template_id)
                print("INFO: Aguardando sincronização das tarefas (15s)...")
                time.sleep(15)
                gp_zpuid = DONOS_PROJETO[dados['gp_selecionado']]
                processar_tarefas_iniciais(zoho_access_token, id_do_novo_projeto, gp_zpuid)
        finally:
            # Libera a chave idempotente
            try:
                if 'execucoes' in session:
                    session['execucoes'].pop(chave_idem, None)
            except Exception:
                pass
        
        # Monta resposta com dados do projeto para atualizar o Kanban sem recarregar tudo
        novo_projeto = None
        if id_do_novo_projeto:
            try:
                novo_projeto = {
                    "id": str(id_do_novo_projeto),
                    "nome": construir_titulo_projeto(dados),
                    "cliente": f"{dados['codigo_contrato_numero']} - {dados['nome_cliente']}",
                    "gp": dados['gp_selecionado'],
                    "data_inicio_formatada": dados.get('start_date', '').replace('-', '/'),
                    "dias_na_fase": "0 dias",
                    "status_atual": "Aguardando Onboarding"
                }
            except Exception:
                pass
        return jsonify({"status": "success", "message": "Processo finalizado com sucesso!", "novo_projeto": novo_projeto})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        # Em Windows, o arquivo pode estar lockado por bibliotecas do Google no momento do finally.
        # Tenta remover com tolerância; se falhar por lock, ignora silenciosamente.
        try:
            if temp_deip_path and os.path.exists(temp_deip_path):
                os.remove(temp_deip_path)
        except PermissionError:
            pass

# ==============================================================================
# --- INTEGRAÇÃO ZOHO: TOKEN, TAGS E COMENTÁRIOS ---
# ==============================================================================

ZP_API_BASE = 'https://projectsapi.zoho.com/api/v3'  # API v3 base (US por padrão)
ZP_API_BASE_DYNAMIC = None  # será definido após obter o token

def _zp_base():
    """Retorna a base da API (dinâmica, se definida a partir do token)."""
    return ZP_API_BASE_DYNAMIC or ZP_API_BASE

def _map_projects_base(api_domain: str) -> str:
    """Mapeia api_domain do token (www.zohoapis.*) para projectsapi.zoho.* correspondente."""
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
    # padrão US
    return 'https://projectsapi.zoho.com/api/v3'


_ZOHO_TOKEN_CACHE = { 'token': None, 'exp': 0 }


def obter_access_token_zoho(ttl_seconds: int = 2700):
    """Obtém access_token com cache simples (TTL ~45min). Evita rate limit no OAuth.
    Retorna token válido e atualiza base da API por data center.
    """
    import time as _t
    now = int(_t.time())
    tok = _ZOHO_TOKEN_CACHE.get('token')
    exp = int(_ZOHO_TOKEN_CACHE.get('exp') or 0)
    if tok and now < exp:
        return tok

    # Quando precisar renovar, faz com backoff rápido em caso de 429/400 rate-limit
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
    for i in range(3):  # até 3 tentativas com backoff
        r = requests.post(token_url, data=data_form, timeout=30)
        if r.status_code == 200:
            data = r.json()
            access_token = data.get('access_token')
            if not access_token:
                raise Exception('Resposta do Zoho sem access_token.')
            # Atualiza base da API conforme o data center do token
            global ZP_API_BASE_DYNAMIC
            ZP_API_BASE_DYNAMIC = _map_projects_base(data.get('api_domain'))
            # Armazena no cache com TTL (45min)
            _ZOHO_TOKEN_CACHE['token'] = access_token
            _ZOHO_TOKEN_CACHE['exp'] = now + ttl_seconds
            return access_token
        else:
            last_err = f'HTTP {r.status_code} - {r.text}'
            # Erro por rate limit: espera incremental
            _t.sleep(1 + i * 2)
    raise Exception(f'Falha ao obter access_token Zoho: {last_err}')


def _zp_headers(access_token: str):
    return {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json'
    }

def get_portal_project_tags(access_token: str):
    """Lista as tags disponíveis para o módulo 'projects' no portal (id e nome)."""
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
    """Retorna tags 'usadas no projeto' (pode incluir tags de tarefas). Mantida para usos gerais."""
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tags"
    print(f"[get_project_tags] URL={url}")
    r = requests.get(url, headers=_zp_headers(access_token), timeout=30)
    print(f"[get_project_tags] status={r.status_code} body={r.text[:500]}")
    r.raise_for_status()
    data = r.json() if r.text else {}
    return (data.get('tags') or []) if isinstance(data, dict) else []

def get_project_tags_strict(access_token: str, project_id: str):
    """Retorna apenas as tags atribuídas diretamente ao projeto (não agregadas das tarefas).
    Usa GET /projects/{id}?fields=tags e normaliza a resposta.
    """
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    params = {"fields": "tags"}
    print(f"[get_project_tags_strict] URL={url} params={params}")
    r = requests.get(url, headers=_zp_headers(access_token), params=params, timeout=30)
    print(f"[get_project_tags_strict] status={r.status_code} body={r.text[:500]}")
    r.raise_for_status()
    data = r.json() if r.text else {}
    # Normaliza leitura de tags no objeto do projeto
    tags_atuais = []
    if isinstance(data, dict):
        if isinstance(data.get('tags'), list):
            tags_atuais = data['tags']
        elif isinstance(data.get('tags'), dict):
            tags_atuais = data['tags'].get('data', []) or []
    return tags_atuais

def add_project_tag(access_token: str, project_id: str, tag_id: str):
    """Adiciona uma tag preservando as tags atuais (PATCH com lista final de IDs).
    Estratégia: lê as tags atuais, inclui a nova e faz um único PATCH com todas.
    """
    # Lê somente as tags atribuídas diretamente ao projeto
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
    """Remove com segurança uma tag do projeto definindo o conjunto final de tags.
    Estratégia: lê as tags atuais e faz PATCH com a lista sem a tag alvo.
    """
    # Lê somente as tags atribuídas diretamente ao projeto
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
    """Garante que as tags 'required_tag_ids' permaneçam no projeto, mesmo após workflows.
    Faz até 'attempts' tentativas adicionais com pequena espera, sempre enviando o conjunto final de tags.
    """
    required = {str(tid) for tid in (required_tag_ids or [])}
    for i in range(max(1, attempts)):
        try:
            # sempre parte apenas das tags diretas do projeto
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
        # pequena espera para permitir workflows do Zoho executarem
        try:
            time.sleep(delay_sec)
        except Exception:
            pass

def set_project_tags_exact(access_token: str, project_id: str, final_tag_ids):
    """Define exatamente o conjunto de tags do projeto conforme 'final_tag_ids'.
    Qualquer tag não listada será removida. Tags banidas são ignoradas.
    """
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

def obter_detalhes_projeto(access_token: str, project_id: str):
    """Retorna detalhes do projeto do Zoho (inclui name, status e tags se possível)."""
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


def find_task_by_name(access_token: str, project_id: str, task_name: str):
    """Busca a tarefa pelo nome; tenta primeiro a listagem paginada do projeto (igualdade),
    depois um fallback por "contém" e, por fim, a busca global.
    """
    def _normalize(s: str) -> str:
        return (s or '').strip().lower()

    target_norm = _normalize(task_name)

    # 1) Listagem paginada do projeto (igualdade exata)
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
        # Passo 1.1: igualdade
        for it in items:
            name = it.get('name') or it.get('title') or it.get('task_name') or ''
            if _normalize(name) == target_norm:
                tid = it.get('id') or it.get('task_id') or it.get('entity_id')
                if tid is not None:
                    print(f"[find_task_by_name] FOUND VIA LIST (exact): {tid}")
                    return str(tid)
        # Passo 1.2: contém (mais permissivo)
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

    # 2) Fallback: busca global no portal
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
    """Lista comentários de uma tarefa para inspecionar como menções aparecem no JSON."""
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}/comments"
    params = {"page": page, "per_page": per_page}
    print(f"[list_task_comments] URL={url} params={params}")
    resp = requests.get(url, headers=_zp_headers(access_token), params=params, timeout=30)
    print(f"[list_task_comments] status={resp.status_code} body_sample={resp.text[:500]}")
    if resp.status_code != 200:
        raise Exception(f"Falha ao listar comentários: HTTP {resp.status_code} - {resp.text}")
    return resp.json() or {}



# ==============================================================================
# --- ROTA: MOVER PROJETO (ATUALIZA ZOHO QUANDO APLICÁVEL) ---
# ==============================================================================
@app.route('/api/mover_projeto', methods=['POST'])
def api_mover_projeto():
    try:
        if 'credentials' not in session:
            return jsonify({"sucesso": False, "erro": "Usuário não autenticado."}),

        payload = request.get_json(force=True) or {}
        projeto_id = str(payload.get('projeto_id') or '').strip()
        coluna_origem = (payload.get('coluna_origem') or '').strip()
        coluna_destino = (payload.get('coluna_destino') or '').strip()
        cliente_sheet = (payload.get('cliente_sheet') or '').strip()

        print(f"[/api/mover_projeto] payload recebido: {payload}")
        print(f"[/api/mover_projeto] projeto_id={projeto_id}, origem='{coluna_origem}', destino='{coluna_destino}'")

        if not projeto_id or not coluna_destino:
            print("[/api/mover_projeto] Parâmetros inválidos")
            return jsonify({"sucesso": False, "erro": "Parâmetros inválidos."}),

        msg_operacoes = []

        # Valida refresh_token antes de usar Google Sheets
        try:
            creds_in_session = session.get('credentials') if isinstance(session.get('credentials'), dict) else None
            if not creds_in_session or not creds_in_session.get('refresh_token'):
                print("[/api/mover_projeto] Sessão sem refresh_token. Instruindo re-login.")
                return jsonify({
                    "sucesso": False,
                    "erro": "Sessão sem refresh_token. Faça login novamente para conceder acesso offline.",
                    "acao": "/login"
                }), 401
        except Exception:
            pass

        # Aplica regras gerais via mapeamento JSON conforme a coluna de destino
        try:
            mapping_path = os.path.join(BASE_DIR, 'mapeamento_colunas.json')
            with open(mapping_path, 'r', encoding='utf-8') as f:
                colmap = json.load(f)
        except Exception as e:
            print(f"[/api/mover_projeto] Falha ao ler mapeamento_colunas.json: {e}")
            colmap = {}

        info_dest = colmap.get(coluna_destino) or {}
        if not info_dest:
            msg_operacoes.append('Coluna destino sem mapeamento; nenhuma atualização aplicada.')
        else:
            # 1) Tokens/serviços
            access_token = None
            try:
                access_token = obter_access_token_zoho()
                print(f"[/api/mover_projeto] Access token Zoho obtido? {'SIM' if access_token else 'NAO'}")
            except Exception as e:
                print(f"[/api/mover_projeto] ERRO ao obter token Zoho: {e}")

            # Google Sheets service
            sheets_service = None
            try:
                creds = build_google_credentials_from_session()
                sheets_service = build('sheets', 'v4', credentials=creds)
            except Exception as e:
                print(f"[/api/mover_projeto] ERRO ao iniciar Google Sheets service: {e}")
                if isinstance(e, Exception):
                    pass

            # 2) Descobrir valor do cliente ("codigo - nome") a partir do nome do projeto no Zoho
            valor_cliente = None
            google_drive_folder_id = None
            if access_token:
                try:
                    detalhes_zoho = obter_detalhes_projeto(access_token, projeto_id)
                    nome_projeto_zoho = (detalhes_zoho or {}).get('name', '')
                    print(f"[/api/mover_projeto] nome_projeto_zoho='{nome_projeto_zoho}'")
                    valor_cliente = nome_projeto_zoho.split(' - NR')[0].split(' - AP')[0].split(' - NR/AP')[0].strip()
                    print(f"[/api/mover_projeto] valor_cliente extraído='{valor_cliente}'")
                    
                    description = (detalhes_zoho or {}).get('description', '')
                    match = re.search(r'/folders/([a-zA-Z0-9_-]+)', description)
                    if match:
                        google_drive_folder_id = match.group(1)
                        print(f"DEBUG: Google Drive folder ID extraído da descrição do Zoho: {google_drive_folder_id}")

                except Exception as e:
                    print(f"[/api/mover_projeto] ERRO ao obter detalhes do projeto no Zoho: {e}")

            # 3) Atualizar planilha: Status Principal por valor exato da coluna "Cliente"
            try:
                novo_status_sheet = info_dest.get('sheetStatus')
                # Preferência: usar cliente_sheet do frontend, ignorando placeholders; fallback = extraído do Zoho
                _cli_raw = (cliente_sheet or '').strip()
                if _cli_raw.lower().startswith('cliente não informado') or _cli_raw.lower() in {'', 'n/a', 'na', 'null', 'none'}:
                    cliente_lookup = (valor_cliente or '').strip()
                else:
                    cliente_lookup = _cli_raw
                # Tenta extrair o código numérico antes do " - "
                codigo_lookup = None
                try:
                    import re
                    parte = (cliente_lookup or valor_cliente or '').split(' - ')[0].strip()
                    m = re.match(r'^\d+', parte.replace('.', ''))
                    if m:
                        codigo_lookup = m.group(0)
                except Exception:
                    codigo_lookup = None
                if sheets_service and (cliente_lookup or codigo_lookup) and novo_status_sheet:
                    # Lê cabeçalho (case-insensitive) e encontra colunas de Cliente e Status
                    range_cab = f"'{NOME_ABA_PLANILHA}'!A{LINHA_CABECALHO}:ZZ{LINHA_CABECALHO}"
                    cabecalhos = sheets_service.spreadsheets().values().get(
                        spreadsheetId=ID_PLANILHA_PROJETOS,
                        range=range_cab
                    ).execute().get('values', [[]])[0]
                    lower_map = {str(c).strip().lower(): i for i, c in enumerate(cabecalhos)}
                    # Cliente: usa a constante configurada, com fallback para 'cliente'
                    cliente_key_lower = str(COLUNA_REFERENCIA_PARA_CONTAR_LINHAS).strip().lower() or 'cliente'
                    col_cliente_idx = lower_map.get(cliente_key_lower)
                    if col_cliente_idx is None:
                        col_cliente_idx = lower_map.get('cliente')
                    # Status: tenta várias possibilidades
                    status_candidates = ['status principal', 'status', 'status_principal', 'statusprincipal']
                    col_status_idx = None
                    for nm in status_candidates:
                        if nm in lower_map:
                            col_status_idx = lower_map[nm]
                            break
                    if col_cliente_idx is not None and col_status_idx is not None:
                        letra_col_cliente = _a1_col_letter(col_cliente_idx)
                        start_row = LINHA_CABECALHO + 1
                        range_clientes = f"'{NOME_ABA_PLANILHA}'!{letra_col_cliente}{start_row}:{letra_col_cliente}"
                        valores_clientes = sheets_service.spreadsheets().values().get(
                            spreadsheetId=ID_PLANILHA_PROJETOS,
                            range=range_clientes
                        ).execute().get('values', [])
                        # Encontra linha do cliente por match exato OU pelo código
                        linha_encontrada = None
                        for idx, row in enumerate(valores_clientes):
                            cell = (row[0] if row else '').strip()
                            if cliente_lookup and cell == cliente_lookup:
                                linha_encontrada = start_row + idx
                                break
                            if not linha_encontrada and codigo_lookup and cell.startswith(f"{codigo_lookup} - "):
                                linha_encontrada = start_row + idx
                                break
                        if linha_encontrada:
                            range_status_cell = f"'{NOME_ABA_PLANILHA}'!{_a1_col_letter(col_status_idx)}{linha_encontrada}"
                            sheets_service.spreadsheets().values().update(
                                spreadsheetId=ID_PLANILHA_PROJETOS,
                                range=range_status_cell,
                                valueInputOption='USER_ENTERED',
                                body={'values': [[novo_status_sheet]]}
                            ).execute()
                            msg_operacoes.append('Planilha principal: Status Principal atualizado')
                        else:
                            msg_operacoes.append('Cliente não encontrado na planilha principal')
                    else:
                        msg_operacoes.append('Cabeçalho: colunas de Cliente/Status não encontradas')
                else:
                    msg_operacoes.append('Planilha não atualizada (serviço/cliente/status indisponível)')
            except Exception as e:
                print(f"[/api/mover_projeto] ERRO atualização planilha: {e}")
                msg_operacoes.append(f'Falha ao atualizar planilha: {e}')

            # 4) Atualizar status do projeto no Zoho (se mapeado)
            try:
                zoho_status_id = (info_dest.get('zohoStatusId') or '').strip() if isinstance(info_dest.get('zohoStatusId'), str) else info_dest.get('zohoStatusId')
                if access_token and zoho_status_id:
                    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}"
                    payload = {"status": {"id": zoho_status_id}}
                    print(f"[/api/mover_projeto] Atualizando status do projeto: {payload}")
                    r = requests.patch(url, headers=_zp_headers(access_token), json=payload, timeout=30)
                    print(f"[/api/mover_projeto] status PATCH projeto={r.status_code} body={r.text[:500]}")
                    if r.status_code in (200, 201):
                        msg_operacoes.append('Status do projeto atualizado no Zoho')
                    else:
                        msg_operacoes.append(f'Falha ao atualizar status no Zoho: HTTP {r.status_code}')
            except Exception as e:
                print(f"[/api/mover_projeto] ERRO ao atualizar status do projeto: {e}")
                msg_operacoes.append(f'Erro ao atualizar status no Zoho: {e}')

            # Regra específica: Falta Liberar Servidor Infra -> Em Andamento
            if (coluna_origem == "Falta Liberar Servidor Infra" and coluna_destino == "Em Andamento"):
                print("DEBUG: Entrou na regra específica 'Falta Liberar Servidor Infra -> Em Andamento'")
                if sheets_service:
                    try:
                        if google_drive_folder_id:
                            range_cab = f"'{NOME_ABA_PLANILHA}'!A{LINHA_CABECALHO}:ZZ{LINHA_CABECALHO}"
                            cabecalhos = sheets_service.spreadsheets().values().get(
                                spreadsheetId=ID_PLANILHA_PROJETOS,
                                range=range_cab
                            ).execute().get('values', [[]])[0]
                            lower_map = {str(c).strip().lower(): i for i, c in enumerate(cabecalhos)}

                            col_cliente_idx = lower_map.get(str(COLUNA_REFERENCIA_PARA_CONTAR_LINHAS).strip().lower()) or lower_map.get('cliente')
                            col_vpn_idx = lower_map.get('vpn')

                            if col_cliente_idx is not None:
                                letra_col_cliente = _a1_col_letter(col_cliente_idx)
                                start_row = LINHA_CABECALHO + 1
                                range_clientes = f"'{NOME_ABA_PLANILHA}'!{letra_col_cliente}{start_row}:{letra_col_cliente}"
                                valores_clientes = sheets_service.spreadsheets().values().get(
                                    spreadsheetId=ID_PLANILHA_PROJETOS,
                                    range=range_clientes
                                ).execute().get('values', [])

                                print(f"DEBUG: Procurando pelo cliente '{valor_cliente}' na planilha.")
                                linha_encontrada = None
                                for idx, row in enumerate(valores_clientes):
                                    cell = (row[0] if row else '').strip()
                                    if valor_cliente and cell == valor_cliente:
                                        linha_encontrada = start_row + idx
                                        print(f"DEBUG: Cliente '{valor_cliente}' encontrado na linha {linha_encontrada}.")
                                        break
                                
                                if not linha_encontrada:
                                    print(f"DEBUG: Cliente '{valor_cliente}' não encontrado na planilha.")

                                if linha_encontrada and col_vpn_idx is not None:
                                    try:
                                        drive_service = build('drive', 'v3', credentials=creds)
                                        ipv6 = obter_ipv6_do_drive(drive_service, google_drive_folder_id)
                                        if ipv6:
                                            print(f"DEBUG: Tentando inserir IPv6 '{ipv6}' na planilha.")
                                            letra_col_vpn = _a1_col_letter(col_vpn_idx)
                                            range_vpn = f"'{NOME_ABA_PLANILHA}'!{letra_col_vpn}{linha_encontrada}"
                                            print(f"DEBUG: Atualizando célula da VPN no range: {range_vpn}")
                                            sheets_service.spreadsheets().values().update(
                                                spreadsheetId=ID_PLANILHA_PROJETOS,
                                                range=range_vpn,
                                                valueInputOption='USER_ENTERED',
                                                body={'values': [[ipv6]]}
                                            ).execute()
                                            msg_operacoes.append('Planilha principal: Coluna VPN atualizada com IPv6.')
                                        else:
                                            msg_operacoes.append('IPv6 não encontrado no Google Drive.')
                                    except Exception as e:
                                        msg_operacoes.append(f'Falha ao buscar IPv6 no Drive: {e}')
                                elif linha_encontrada:
                                    print("DEBUG: Coluna 'VPN' não encontrada no cabeçalho da planilha.")
                                    msg_operacoes.append('Planilha principal: Coluna VPN não encontrada.')
                        else:
                            print("DEBUG: ID da pasta do Google Drive não encontrado na descrição do projeto Zoho.")
                            msg_operacoes.append('ID da pasta do Google Drive não encontrado na descrição do projeto Zoho.')

                    except Exception as e:
                        msg_operacoes.append(f'Falha ao atualizar planilha (regra específica): {e}')

                    # 2) Zoho: status e campo customizado "data_liberacao_servidor"
                    if access_token:
                        try:
                            # Define explicitamente o status Em Andamento
                            status_id = "2376502000000020092"
                            url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}"
                            r = requests.patch(url, headers=_zp_headers(access_token), json={"status": {"id": status_id}}, timeout=30)
                            if r.status_code in (200, 201):
                                msg_operacoes.append('Zoho: Status do projeto definido para Em Andamento')
                            else:
                                msg_operacoes.append(f"Zoho: falha ao definir status (HTTP {r.status_code})")
                        except Exception as e:
                            msg_operacoes.append(f'Zoho: erro ao definir status (regra específica): {e}')

                        try:
                            hoje_iso = datetime.now().strftime('%Y-%m-%d')
                            url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}"
                            payload = {"custom_fields": {"data_liberacao_servidor": hoje_iso}}
                            headers = _zp_headers(access_token)

                            # Logs detalhados para diagnosticar a atualização do campo customizado
                            headers_log = dict(headers)
                            if 'Authorization' in headers_log:
                                headers_log['Authorization'] = 'Zoho-oauthtoken ***'
                            print(f"[/api/mover_projeto] PATCH custom_fields (data_liberacao_servidor) -> proj={projeto_id}")
                            print(f"[/api/mover_projeto] URL: {url}")
                            print(f"[/api/mover_projeto] Payload: {payload}")
                            print(f"[/api/mover_projeto] Headers: {headers_log}")

                            r2 = requests.patch(url, headers=headers, json=payload, timeout=30)
                            print(f"[/api/mover_projeto] Resposta PATCH custom_fields -> status={r2.status_code}")
                            try:
                                print(f"[/api/mover_projeto] Body (primeiros 800 chars): {r2.text[:800]}")
                            except Exception:
                                pass

                            updated_ok = False
                            try:
                                resp_json = r2.json() if hasattr(r2, 'json') else None
                                cf = (resp_json or {}).get('custom_fields') if isinstance(resp_json, dict) else None
                                if isinstance(cf, dict) and cf.get('data_liberacao_servidor') == hoje_iso:
                                    updated_ok = True
                                # Alguns tenants retornam no topo ou com prefixo cf_
                                if isinstance(resp_json, dict):
                                    if resp_json.get('data_liberacao_servidor') == hoje_iso:
                                        updated_ok = True
                                    if resp_json.get('cf_data_liberacao_servidor') == hoje_iso:
                                        updated_ok = True
                            except Exception:
                                pass

                            # Fallback 1: tentar enviar o campo no topo (sem custom_fields)
                            if not updated_ok:
                                payload_inline = {"data_liberacao_servidor": hoje_iso}
                                print(f"[/api/mover_projeto] Fallback PATCH inline -> payload: {payload_inline}")
                                r3 = requests.patch(url, headers=headers, json=payload_inline, timeout=30)
                                print(f"[/api/mover_projeto] Resposta PATCH inline -> status={r3.status_code}")
                                try:
                                    print(f"[/api/mover_projeto] Body inline (primeiros 800 chars): {r3.text[:800]}")
                                except Exception:
                                    pass
                                try:
                                    j3 = r3.json() if hasattr(r3, 'json') else None
                                    if isinstance(j3, dict):
                                        if (j3.get('data_liberacao_servidor') == hoje_iso) or (j3.get('cf_data_liberacao_servidor') == hoje_iso):
                                            updated_ok = True
                                except Exception:
                                    pass

                            # GET de verificação (se ainda não temos confirmação)
                            try:
                                g = requests.get(url, headers=headers, timeout=20)
                                print(f"[/api/mover_projeto] GET verificação -> status={g.status_code}")
                                try:
                                    gj = g.json()
                                except Exception:
                                    gj = None
                                try:
                                    print(f"[/api/mover_projeto] GET body (primeiros 800 chars): {g.text[:800]}")
                                except Exception:
                                    pass
                                if isinstance(gj, dict):
                                    cf2 = gj.get('custom_fields') if isinstance(gj.get('custom_fields'), dict) else None
                                    if (cf2 and cf2.get('data_liberacao_servidor') == hoje_iso) or \
                                       (gj.get('data_liberacao_servidor') == hoje_iso) or \
                                       (gj.get('cf_data_liberacao_servidor') == hoje_iso):
                                        updated_ok = True
                            except Exception:
                                pass

                            if updated_ok or r2.status_code in (200, 201):
                                msg_operacoes.append('Zoho: Campo "Data Liberação Servidor" atualizado (verificado)')
                            else:
                                msg_operacoes.append(f"Zoho: falha ao atualizar campo customizado (HTTP {r2.status_code})")
                        except Exception as e:
                            print(f"[/api/mover_projeto] EXCEPTION ao atualizar custom_fields data_liberacao_servidor: {e}")
                            msg_operacoes.append(f'Zoho: erro ao atualizar campo customizado (regra específica): {e}')


            # 5) Tags (definir exatamente conforme mapeamento)
            if access_token:
                try:
                    final_tags = [str(t) for t in (info_dest.get('zohoTagsToAdd') or [])]
                    # Se o mapeamento desejar explicitamente remover tags, elas simplesmente não entram no conjunto final
                    set_project_tags_exact(access_token, projeto_id, final_tags)
                    msg_operacoes.append('Tags definidas exatamente conforme mapeamento')
                except Exception as e:
                    print(f"[/api/mover_projeto] ERRO ao definir tags exatas: {e}")
                    msg_operacoes.append(f'Falha ao definir tags: {e}')

            # 6) Ações adicionais por gatilho
            trigger = info_dest.get('triggersAction')
            if trigger and access_token:
                try:
                    if trigger == 'adicionar_comentario_servidor':
                        mentions_text = zoho_mentions(["Giovani Sousa"])  # ajuste os nomes se necessário
                        comentario = (
                            f"Bom dia {mentions_text}, tudo bem? Realizada reunião de onboarding com o cliente. "
                            "Sendo assim, podemos dar inicio as atividades de infra. Vamos iniciar os grupos. "
                            "Os detalhes do projeto se encontram na descrição do mesmo. Att"
                        )
                        print("[/api/mover_projeto] Buscando tarefa '02.01.01 - Validação do DEIP'...")
                        task_id = find_task_by_name(access_token, projeto_id, "02.01.01 - Validação do DEIP")
                        print(f"[/api/mover_projeto] task_id encontrado: {task_id}")
                        if task_id:
                            add_comment_to_task(access_token, projeto_id, task_id, comentario)
                            msg_operacoes.append('Comentário adicionado na tarefa alvo')
                        else:
                            msg_operacoes.append('Tarefa alvo não encontrada para comentar')
                    # Outros gatilhos podem ser adicionados aqui (ex.: preencher_dpi_homologacao, etc.)
                except Exception as e:
                    print(f"[/api/mover_projeto] ERRO em ação de gatilho ({trigger}): {e}")
                    msg_operacoes.append(f'Falha ao executar ação: {e}')

            # Ações específicas para a coluna "Em Andamento"
            if coluna_destino == "Em Andamento" and access_token:
                try:
                    # TODO: Tornar o nome do usuário a ser mencionado configurável
                    # Comentário na tarefa de importação
                    mentions_text_import = zoho_mentions(["Giovani Sousa"])
                    task_import_id = find_task_by_name(access_token, projeto_id, "Contato inicial com o cliente")
                    if task_import_id:
                        comentario_import = (
                            f"Bom dia {mentions_text_import}, tudo bem? Apenas para informar que o servidor se encontra liberado.\n\n"
                            "Sendo assim, podemos dar inicio as atividades de Importação. Vamos iniciar os grupos. \n\n"
                            "Os detalhes do projeto se encontram na descrição do mesmo. Att"
                        )
                        add_comment_to_task(access_token, projeto_id, task_import_id, comentario_import)
                        msg_operacoes.append('Comentário adicionado na tarefa de importação.')
                    else:
                        msg_operacoes.append('Tarefa de importação não encontrada.')

                    # Comentário na tarefa de integração
                    mentions_text_integ = zoho_mentions(["Giovani Sousa"])
                    task_integ_id = find_task_by_name(access_token, projeto_id, "Solicitar dados ao RIS/HIS para integração de worklist")
                    if task_integ_id:
                        comentario_integ = (
                            f"Bom dia {mentions_text_integ}, tudo bem? Apenas para informar que o servidor se encontra liberado.\n\n"
                            "Sendo assim, podemos dar inicio as atividades de Integração. Vamos iniciar os grupos. \n\n"
                            "Os detalhes do projeto se encontram na descrição do mesmo. Att"
                        )
                        add_comment_to_task(access_token, projeto_id, task_integ_id, comentario_integ)
                        msg_operacoes.append('Comentário adicionado na tarefa de integração.')
                    else:
                        msg_operacoes.append('Tarefa de integração não encontrada.')

                except Exception as e:
                    print(f"[/api/mover_projeto] ERRO ao adicionar comentários em tarefas de 'Em Andamento': {e}")
                    msg_operacoes.append(f'Falha ao adicionar comentários: {e}')

        # Atualiza cache de dias-na-fase apenas para o projeto movido
        try:
            _invalidate_dias_cache(projeto_id)
            now_ts = int(time.time())
            chave_hint = f"{projeto_id}|{coluna_destino}"
            _DIAS_FASE_CACHE[chave_hint] = { 'valor': 'Hoje', 'ts': now_ts }
            _DIAS_FASE_CACHE[str(projeto_id)] = { 'valor': 'Hoje', 'ts': now_ts }
        except Exception:
            pass

        return jsonify({"sucesso": True, "mensagem": "; ".join(msg_operacoes) or 'Movimentação registrada.'})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"sucesso": False, "erro": str(e)}), 500


# ============================== 
# --- API: Comentários Projeto ---
# ==============================

@app.route('/api/projetos/comentar', methods=['POST'])
def comentar_projeto():
    try:
        if 'credentials' not in session:
            return jsonify({"sucesso": False, "erro": "Não autenticado."}),

        data = request.get_json(silent=True) or {}
        projeto_id = str(data.get('projeto_id') or '').strip()
        content = (data.get('content') or '').strip()
        if not projeto_id or not content:
            return jsonify({"sucesso": False, "erro": "Parâmetros inválidos"}), 400

        access_token = obter_access_token()
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}/comments"

        # Tenta formatos aceitos pela API do Zoho
        last_resp = None
        for payload in ({"comment": content}, {"content": content}):
            try:
                r = requests.post(
                    url,
                    headers={**_zp_headers(access_token), "Content-Type": "application/json"},
                    json=payload,
                    timeout=30
                )
                last_resp = r
                if r.status_code in (200, 201):
                    return jsonify({"sucesso": True})
            except Exception as req_err:
                last_resp = req_err
                break

        if hasattr(last_resp, 'status_code'):
            try:
                body = last_resp.json()
            except Exception:
                body = getattr(last_resp, 'text', str(last_resp))
            return jsonify({"sucesso": False, "erro": f"HTTP {last_resp.status_code}", "detalhe": body}), 502
        else:
            return jsonify({"sucesso": False, "erro": str(last_resp)}), 502

    except Exception as e:
        traceback.print_exc()
        return jsonify({"sucesso": False, "erro": str(e)}), 500

# ====================== 
# --- ROTAS GOOGLE ---
# ======================




# ====================== 
# --- ROTA PRINCIPAL ---
# ======================



# ==============================================================================
# --- EXECUÇÃO DO SERVIDOR ---
# ==============================================================================

if __name__ == '__main__':
    # Garante que o servidor rode em HTTP para o callback do OAuth funcionar localmente
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True, port=5000)