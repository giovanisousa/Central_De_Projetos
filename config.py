# -*- coding: utf-8 -*-
import os
from datetime import timedelta

# --- CAMINHOS E DIRETÓRIOS ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DOCS_PATH = os.path.join(BASE_DIR, 'templates_doc')
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
ZOHO_TOKEN_PATH = os.path.join(BASE_DIR, 'zoho_refresh_token.txt')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# --- GOOGLE API ---
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
SCOPES_GOOGLE = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# --- ZOHO API ---
ZOHO_CLIENT_ID = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
ZOHO_CLIENT_SECRET = "70226965d09b04444346222d9b4846c86a5d31d2fe"
ZOHO_PORTAL_ID = "868230290"
ZOHO_PROJECTS_CUSTOM_WEB_HOST = "https://projects.animati.com.br"

# IDs de Status do Zoho
STATUS_ABERTO_ID = "2376502000000020089"
STATUS_EM_ANDAMENTO_ID = "2376502000000020092"
STATUS_CANCELADO_ID = "2376502000000020110"
STATUS_FINALIZADO_ID = "2376502000000020116"
STATUS_OPERACAO_ASSISTIDA_ID = "2376502000000020119"
STATUS_AGUARDANDO_CLIENTE_ID = "2376502000000020107"
STATUS_PENDENCIA_ID = "2376502000000020104"
STATUS_CONCLUIDO_ID = "2376502000000674703"

# IDs de Tags do Zoho
TAG_AGUARDANDO_ONBOARDING_ID = "2376502000001291513"
TAG_AGUARDANDO_INFRA_ID = "2376502000000958355"
TAG_EM_HOMOLOGACAO_ID = "2376502000000983053"
TAG_EM_VIRADA_ID = "2376502000001228741"
TAG_PARADO_ID = "2376502000000983125"
TAG_AGUARDANDO_ENCERRAMENTO_ID = "2376502000005304184"
TAG_IMPLANTACAO = "2376502000000188201"
BANNED_PROJECT_TAG_IDS = {"2376502000004311812"}  # Impeditivo (fase)

# Outras configs Zoho
DEFAULT_TASKS_CUSTOM_VIEW_ID = "2376502000000046003"

# --- MAPEAMENTOS E DADOS DO PROJETO ---
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
ZOHO_MENTION_USERS = {
    "William Floriano": {"usernum": "870213453", "name": "William Floriano"},
    "Giovani Sousa": {"usernum": "868816641", "name": "Giovani Sousa"},
    "Roger Machado": {"usernum": "870218464", "name": "Roger Machado"},
    "Carlo Tristão": {"usernum": "870217691", "name": "Carlo Tristão"}
}
TAREFAS_PARA_CONCLUIR = [t.strip() for t in [
    "Registrar Projeto Planilha de Andamento",
    "Criar pastas no Google Drive",
    "Registrar Projeto na plataforma de gestão de projetos.",
    "Criação da empresa e acesso ao Zoho Projects"
]]
TAREFAS_PARA_ATRIBUIR = [t.strip() for t in [
    "Alteração da senha de acesso do usuário suporte",
    "Solicitar definição do cronograma de homologação",
    "Gerar o ticket de virada do cliente",
    "Realizar a passagem do cliente para a OA",
    "Realizar o preenchimento do DPI",
    "Enviar DPI via e-mail para CS",
    "Realizar reunião de encerramento com o cliente",
    "Encaminhar todos os tickets abertos para a equipe de suporte",
    "Finalizar os grupos de whatsapp",
    "Finalizar projeto Artia",
    "Encaminhar mensagem com informações sobre o Plantão",
    "Criação dos Grupos de Whatsapp"
]]
TEMPO_RELATO = {
    "Registrar Projeto Planilha de Andamento": "00:05",
    "Criar pastas no Google Drive": "00:10",
    "Registrar Projeto na plataforma de gestão de projetos.": "00:05",
    "Criação da empresa e acesso ao Zoho Projects": "00:05"
}

class Config:
    # --- CONFIGURAÇÃO FLASK ---
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    if not SECRET_KEY:
        try:
            _key_path = os.path.join(BASE_DIR, '.flask_secret_key')
            if os.path.exists(_key_path):
                with open(_key_path, 'r', encoding='utf-8') as f:
                    SECRET_KEY = (f.read() or '').strip()
            if not SECRET_KEY:
                import secrets
                SECRET_KEY = secrets.token_hex(32)
                with open(_key_path, 'w', encoding='utf-8') as f:
                    f.write(SECRET_KEY)
        except Exception:
            SECRET_KEY = 'dev-secret-change-me'

    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(BASE_DIR, '.flask_session')
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Mudar para True em produção com HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    UPLOAD_FOLDER = UPLOAD_FOLDER