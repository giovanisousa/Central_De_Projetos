from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from config import CREDENTIALS_PATH, SCOPES_GOOGLE, DONOS_PROJETO
from database import get_user_by_email
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
    if 'credentials' not in session:
        return redirect(url_for('main.login_page'))

    implantadores_ris, implantadores_pacs = carregar_implantadores()
    
    user_info = session.get('user_info')

    template_vars = {
        "logged_in": 'credentials' in session,
        "user_email": user_info.get('email') if user_info else None,
        "user_name": user_info.get('name') if user_info else None,
        "gps": list(DONOS_PROJETO.keys()),
        "implantadores_ris": implantadores_ris,
        "implantadores_pacs": implantadores_pacs,
        "cores_colunas": {
            "Aguardando Onboarding": "#6c757d",
            "Falta Liberar Servidor Infra": "#E67E22",
            "Aguardando Cronograma": "#b8b814",
            "Em Homologação": "#1ABC9C",
            "Em Virada": "#1ABC9C",
            "Em Operação Assistida": "#3498DB",
            "Aguardando Encerramento": "#8B5CF6",
            "Finalizado": "#229954",
            "Projeto Parado": "#DC143C",
            "Cancelado": "#b5b5b5",
            "Status Desconhecido": "#95A5A6"
        }
    }
    return render_template('index.html', **template_vars)

@main_bp.route('/login')
def login_page():
    return render_template('login.html')

@main_bp.route('/google_login')
def google_login():
    # Detectar scheme automaticamente (http local, https produção)
    redirect_uri = url_for('main.oauth2callback', _external=True)
    print(f"Redirect URI enviado para o Google: {redirect_uri}")
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES_GOOGLE,
        redirect_uri=redirect_uri
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

    # Verifica se houve erro no callback
    error = request.args.get('error')
    if error:
        flash(f'Erro na autenticação: {error}', 'danger')
        return redirect(url_for('main.login_page'))

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES_GOOGLE,
        state=state,
        redirect_uri=url_for('main.oauth2callback', _external=True)
    )
    authorization_response = request.url
    
    # Tenta obter o token com tratamento de erros
    try:
        # Ignora warnings de mudança de escopo (scope) do OAuth
        # Isso pode acontecer quando novos escopos são adicionados (ex: Calendar API)
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Scope has changed')
            flow.fetch_token(authorization_response=authorization_response)
    except Exception as e:
        error_msg = str(e)
        if 'invalid_grant' in error_msg.lower():
            flash('Erro na autenticação: o código de autorização expirou ou já foi usado. Por favor, tente fazer login novamente.', 'danger')
        else:
            flash(f'Erro ao obter token de autenticação: {error_msg}', 'danger')
        return redirect(url_for('main.login_page'))
    
    credentials = flow.credentials

    temp_creds = Credentials(
        token=credentials.token,
        refresh_token=credentials.refresh_token,
        token_uri=credentials.token_uri,
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        scopes=credentials.scopes,
    )
    user_info_service = build('oauth2', 'v2', credentials=temp_creds)
    user_info = user_info_service.userinfo().get().execute()
    
    user_email = user_info.get('email')
    user_from_db = get_user_by_email(user_email)

    if user_from_db:
        session['credentials'] = {
            'refresh_token': credentials.refresh_token or (session.get('credentials') or {}).get('refresh_token'),
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
        }
        session['user_info'] = {
            'email': user_from_db.email,
            'name': user_from_db.nome
        }
        return redirect(url_for('main.index'))
    else:
        flash('Você não possui acesso ao sistema.', 'danger')
        return redirect(url_for('main.login_page'))

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login_page'))
