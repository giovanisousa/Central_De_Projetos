# -*- coding: utf-8 -*-

import os
import json
import time
import traceback
import urllib.parse
from datetime import date, datetime, timedelta
import logging 
import warnings
from sqlalchemy import text # Import necessário para a rota keep-alive

# Suprime warning do googleapiclient
warnings.filterwarnings('ignore', message='file_cache is only supported with oauth2client<4.0.0')

# Carrega variáveis do .env automaticamente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename

try:
    from flask_session import Session
except Exception:
    Session = None

# --- BIBLIOTECAS DE API ---
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

# Garante que Flask reconheça HTTPS atrás de proxy (Render, Railway, etc)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configurações de Cache
app.config.setdefault('_DIAS_FASE_CACHE', {})
app.config.setdefault('_CACHE_TTL_SECONDS', 90)

# --- NOVA ROTA: KEEP-ALIVE (EVITA SUSPEND DO NEON E STANDBY DO RENDER) ---
@app.route('/keep-alive')
def keep_alive():
    """
    Mantém o Render acordado 24/7, mas só acorda o Neon no horário comercial.
    """
    from datetime import datetime, timedelta, timezone
    
    # Define o fuso horário de Brasília (UTC-3)
    tz_brasilia = timezone(timedelta(hours=-3))
    agora = datetime.now(tz_brasilia)
    
    dia_semana = agora.isoweekday() # 1 = Segunda, 7 = Domingo
    hora = agora.hour

    # Define horário comercial: Segunda a Sexta, das 08h às 18h
    is_horario_comercial = (1 <= dia_semana <= 5) and (8 <= hora < 18)

    if is_horario_comercial:
        try:
            from database import Session
            db_session = Session()
            db_session.execute(text('SELECT 1'))
            db_session.close()
            return "Modo Comercial: Render + Neon Ativos", 200
        except Exception as e:
            logger.error(f"[KEEP-ALIVE] Erro ao acordar banco: {e}")
            return f"Erro no banco: {e}", 500
    else:
        # Fora do horário comercial, apenas responde 200 para o Render não dormir
        # Mas NÃO faz consulta SQL, permitindo que o Neon fique SUSPENDED
        return "Modo Descanso: Render Ativo (Neon Suspenso)", 200

# --- REGISTRO DE BLUEPRINTS ---
from routes.main import main_bp
app.register_blueprint(main_bp)

from routes.api import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

# Sessão do lado do servidor
if Session:
    if app.config.get('SESSION_TYPE') == 'filesystem':
        try:
            os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
        except Exception as e:
            logger.error(f"Erro ao criar diretório de sessão: {e}")
    Session(app)

try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except Exception as e:
    logger.error(f"Erro ao criar diretório de upload: {e}")

# Configurar cache para arquivos estáticos
@app.after_request
def add_header(response):
    if 'static' in request.path:
        if any(ext in request.path for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf']):
            response.cache_control.max_age = 31536000  
            response.cache_control.public = True
        elif any(ext in request.path for ext in ['.css', '.js']):
            response.cache_control.max_age = 604800  
            response.cache_control.public = True
    return response

# Verificação do banco de dados no startup
try:
    from database import Session, Project
    db_session = Session()
    projetos_count = db_session.query(Project).count()
    db_session.close()
    logger.info(f"[SYNC] Projetos no banco: {projetos_count}")
    
    if projetos_count == 0:
        logger.warning("[SYNC] ⚠️ Banco de dados vazio! Execute sincronização após deploy.")
    else:
        logger.info(f"[SYNC] ✅ Banco de dados OK com {projetos_count} projetos.")
        
except Exception as e:
    logger.error(f"[SYNC] Erro ao verificar banco de dados: {e}")

# Configuração de OAuth para produção/desenvolvimento
if os.environ.get('FLASK_ENV') != 'production':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    # Configuração de porta e host para o Render (quando rodado localmente)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
