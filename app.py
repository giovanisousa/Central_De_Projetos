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

# --- INICIALIZAÇÃO E CONFIGURAÇÃO DO FLASK ---
from config import Config, DONOS_PROJETO
import utils


app = Flask(__name__)
app.config.from_object(Config)
# Inicializa caches/TTL usados pelos endpoints
app.config.setdefault('_DIAS_FASE_CACHE', {})
app.config.setdefault('_CACHE_TTL_SECONDS', 90)

from routes.main import main_bp
app.register_blueprint(main_bp)

from routes.api import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

# Sessão do lado do servidor
if Session:
    try:
        os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    except Exception:
        pass
    Session(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)














if __name__ == '__main__':
    import logging
    # OTIMIZAÇÃO: Configurar logging ao invés de prints excessivos (~50ms por operação)
    # INFO = mensagens essenciais (movimentações, erros)
    # DEBUG = apenas quando debug=True e LOG_LEVEL=DEBUG na config
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # use_reloader=False para evitar reinicializações durante requisições
    app.run(debug=True, port=5000, use_reloader=False)
