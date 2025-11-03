# -*- coding: utf-8 -*-

import os
import json
import time
import traceback
import urllib.parse
from datetime import date, datetime, timedelta
import logging # Import logging
import warnings

# Suprime warning do googleapiclient sobre file_cache (é apenas informativo, não afeta funcionalidade)
warnings.filterwarnings('ignore', message='file_cache is only supported with oauth2client<4.0.0')

# Carrega variáveis do .env automaticamente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Se não estiver instalado, ignora (Railway já injeta variáveis)
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

# --- INICIALIZAÇÃO E CONFIGURAÇÃO DO FLASK ---

from config import Config, DONOS_PROJETO, BASE_DIR
import utils


app = Flask(__name__)

app.config.from_object(Config)

# Garante que Flask reconheça HTTPS atrás de proxy (Railway, Heroku, etc)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configurar logging para toda a aplicação
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__) # Logger para app.py

# Inicializa caches/TTL usados pelos endpoints
app.config.setdefault('_DIAS_FASE_CACHE', {})
app.config.setdefault('_CACHE_TTL_SECONDS', 90)

from routes.main import main_bp
app.register_blueprint(main_bp)

from routes.api import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

# Sessão do lado do servidor
if Session:
    if app.config['SESSION_TYPE'] == 'filesystem':
        try:
            os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
        except Exception as e:
            logger.error(f"Erro ao criar diretório de sessão: {e}")

    # Sessão do lado do servidor
    if Session:
        if app.config['SESSION_TYPE'] == 'filesystem':
            try:
                os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
            except Exception as e:
                logger.error(f"Erro ao criar diretório de sessão: {e}")
        Session(app)

    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except Exception as e:
        logger.error(f"Erro ao criar diretório de upload: {e}")

# Configurar cache para arquivos estáticos (imagens, CSS, JS)
@app.after_request
def add_header(response):
    """
    Adiciona headers de cache para arquivos estáticos para melhorar performance.
    Imagens de fundo e assets carregam instantaneamente após primeira visita.
    """
    if 'static' in request.path:
        # Cache por 1 ano para assets estáticos (imagens, fonts, etc)
        if any(ext in request.path for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf']):
            response.cache_control.max_age = 31536000  # 1 ano
            response.cache_control.public = True
        # Cache por 1 semana para CSS e JS
        elif any(ext in request.path for ext in ['.css', '.js']):
            response.cache_control.max_age = 604800  # 1 semana
            response.cache_control.public = True
    return response

    # Sincronização automática se o banco estiver vazio (executa sempre que o app é importado)
    try:
        from database import Session, Project
        session = Session()
        projetos_count = session.query(Project).count()
        session.close()
        logger.info(f"[SYNC] Projetos no banco: {projetos_count}")
        if projetos_count == 0:
            logger.info("[SYNC] Nenhum projeto encontrado no banco. Iniciando sincronização automática com Zoho...")
            from sync_zoho import synchronize_projects
            try:
                synchronize_projects()
                logger.info("[SYNC] Sincronização automática concluída.")
            except Exception as sync_err:
                logger.error(f"[SYNC] Erro durante sincronização automática: {sync_err}")
        else:
            logger.info("[SYNC] Sincronização automática não necessária. Projetos já presentes no banco.")
    except Exception as e:
        logger.error(f"[SYNC] Falha ao tentar sincronizar projetos automaticamente: {e}")

    if __name__ == '__main__':
        if app.config.get('FLASK_ENV', 'production') == 'development':
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
            debug_mode = True
        else:
            debug_mode = False
        app.run(debug=debug_mode, port=5000, use_reloader=False)
        session.close()
