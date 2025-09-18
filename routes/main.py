from flask import Blueprint, render_template, session, redirect, url_for, request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from config import CREDENTIALS_PATH, SCOPES_GOOGLE, DONOS_PROJETO
import json
import os

main_bp = Blueprint('main', __name__)

def carregar_implantadores():
    try:
        path = os.path.join(os.path.dirname(__file__), '..', 'equipe_implantacao_classificada.json')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("Implantação RIS", []), data.get("Implantação PACS", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return [], []

@main_bp.route('/')
def index():
    implantadores_ris, implantadores_pacs = carregar_implantadores()
    
    template_vars = {
        "logged_in": 'credentials' in session,
        "user_email": session.get('user_email'),
        "gps": list(DONOS_PROJETO.keys()),
        "implantadores_ris": implantadores_ris,
        "implantadores_pacs": implantadores_pacs,
        "cores_colunas": {
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
        }
    }
    return render_template('index.html', **template_vars)

@main_bp.route('/login')
def login():
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES_GOOGLE,
        redirect_uri=url_for('main.oauth2callback', _external=True)
    )
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
    session['state'] = state
    # Define a sessão como permanente para aplicar PERMANENT_SESSION_LIFETIME
    session.permanent = True
    return redirect(authorization_url)

@main_bp.route('/oauth2callback')
def oauth2callback():
    # Recupera state salvo, se existir; se não, tenta usar o state devolvido pelo Google
    saved_state = session.get('state')
    incoming_state = request.args.get('state')
    state = saved_state or incoming_state

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES_GOOGLE,
        state=state,
        redirect_uri=url_for('main.oauth2callback', _external=True)
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
    return redirect(url_for('main.index'))

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))
