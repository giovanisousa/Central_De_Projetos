from flask import Blueprint, request, jsonify, session, current_app
import utils
from config import (
    DONOS_PROJETO,
    ZOHO_PORTAL_ID,

    BASE_DIR,
    TAREFAS_PARA_ATRIBUIR,
    TAREFAS_PARA_CONCLUIR,
    TEMPO_RELATO,
    STATUS_CONCLUIDO_ID,
    STATUS_EM_ANDAMENTO_ID,
    STATUS_OPERACAO_ASSISTIDA_ID,
    STATUS_AGUARDANDO_CLIENTE_ID,
    STATUS_FINALIZADO_ID,
    STATUS_CANCELADO_ID,
    TAG_AGUARDANDO_ONBOARDING_ID,
    TAG_AGUARDANDO_INFRA_ID,
    TAG_EM_HOMOLOGACAO_ID,
    TAG_EM_VIRADA_ID,
    TAG_PARADO_ID,
    TAG_AGUARDANDO_ENCERRAMENTO_ID,
)

# Variável para custom view de tarefas (pode ser None se não configurada)
DEFAULT_TASKS_CUSTOM_VIEW_ID = None
import traceback
import os
from werkzeug.utils import secure_filename
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, date
from typing import Any
import json
import re
import requests
import sqlite3

# Imports para o cache de banco de dados e sincronização
import database
from sync_zoho import synchronize_projects, synchronize_single_project
# Coletor robusto de tarefas (paginação e status)
from buscar_tarefas import listar_tarefas_do_projeto
from datetime import date

# Coletor rápido para uso no fluxo do app (baixa latência)
# Busca até ~400 tarefas com status=all em poucas chamadas, com 1 retry breve
# Evita a varredura extensa do script de diagnóstico

def _listar_tarefas_quick(project_id: str, headers: dict) -> list[dict]:
    import time as _t
    base = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks"
    tasks_by_id: dict[str, dict] = {}

    def _get(url: str) -> list[dict]:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code in (200, 201):
                data = r.json() or {}
                return data.get('tasks', []) if isinstance(data, dict) else []
        except Exception:
            pass
        return []

    def _collect_once():
        status = 'all'
        # Páginas prováveis (duas faixas)
        ranges = ["1-200", "201-400"]
        for rg in ranges:
            url = f"{base}?range={rg}&status={status}"
            chunk = _get(url)
            for t in chunk:
                tid = t.get('id')
                if tid and tid not in tasks_by_id:
                    tasks_by_id[tid] = t
        # index fixo como reforço para portais que exigem index para avançar páginas
        for index in (1, 2, 3):
            url = f"{base}?index={index}&range=1-200&status=all"
            chunk = _get(url)
            for t in chunk:
                tid = t.get('id')
                if tid and tid not in tasks_by_id:
                    tasks_by_id[tid] = t
        # index como offset absoluto (1,201,401) + range correspondente
        for start in (1, 201, 401):
            end = start + 199
            url = f"{base}?index={start}&range={start}-{end}&status=all"
            chunk = _get(url)
            for t in chunk:
                tid = t.get('id')
                if tid and tid not in tasks_by_id:
                    tasks_by_id[tid] = t
        # page/per_page (páginas 1..3)
        for page in (1, 2, 3):
            url = f"{base}?page={page}&per_page=200&status=all"
            chunk = _get(url)
            for t in chunk:
                tid = t.get('id')
                if tid and tid not in tasks_by_id:
                    tasks_by_id[tid] = t

    _collect_once()
    if len(tasks_by_id) < 120:
        _t.sleep(5)  # breve espera para materialização de tarefas do template
        _collect_once()

    # Fallback por Custom View se configurada e ainda baixo
    if len(tasks_by_id) < 120 and DEFAULT_TASKS_CUSTOM_VIEW_ID:
        url_cv = f"{base}/custom-view/{DEFAULT_TASKS_CUSTOM_VIEW_ID}?range=1-200"
        chunk = _get(url_cv)
        for t in chunk:
            tid = t.get('id')
            if tid and tid not in tasks_by_id:
                tasks_by_id[tid] = t

    try:
        print(f"INFO: Coletadas (quick) {len(tasks_by_id)} tarefas")
    except Exception:
        pass
    return list(tasks_by_id.values())


api_bp = Blueprint('api', __name__)

@api_bp.route('/projetos/comentar', methods=['POST'], strict_slashes=False)
@api_bp.route('/projetos/comentar/', methods=['POST'], strict_slashes=False)
def comentar_projeto():
    """Publica comentário no projeto (v3 Comments com fallback REST status/)."""
    if 'credentials' not in session:
        return jsonify({"status": "error", "message": "Usuário não autenticado."}), 401
    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        project_id = data.get('project_id') or data.get('id_projeto') or data.get('projeto_id')
        message = data.get('message') or data.get('mensagem') or data.get('comentario') or data.get('content')
        if not project_id or not message:
            return jsonify({"status": "error", "message": "Campos obrigatórios: project_id e message."}), 400

        access_token = utils.obter_access_token()

        # 1) v3 Comments API
        url_v3 = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/comments"
        headers_v3 = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload_v3 = {"content": str(message)}
        try:
            resp_v3 = requests.post(url_v3, headers=headers_v3, json=payload_v3, timeout=30)
        except Exception:
            resp_v3 = None

        if resp_v3 is not None and resp_v3.status_code in (200, 201):
            print(f"INFO: Comentário de projeto publicado (v3) no projeto {project_id}")
            return jsonify({"status": "success", "sucesso": True, "message": "Comentário adicionado", "mensagem": "Comentário adicionado"})
        else:
            # 2) Fallback: REST status/
            url_rest = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/status/"
            headers_rest = {"Authorization": f"Bearer {access_token}"}
            payload_rest = {"content": str(message)}
            resp_rest = requests.post(url_rest, headers=headers_rest, data=payload_rest, timeout=30)
            if resp_rest.status_code in (200, 201):
                print(f"INFO: Comentário de projeto publicado (REST) no projeto {project_id}")
                return jsonify({"status": "success", "sucesso": True, "message": "Comentário adicionado", "mensagem": "Comentário adicionado"})
            else:
                status_v3 = getattr(resp_v3, "status_code", "n/a")
                text_v3 = (resp_v3.text[:400] if getattr(resp_v3, "text", None) else "")
                print(f"WARN: Falha ao comentar (v3={status_v3}, REST={resp_rest.status_code}) - v3:{text_v3} REST:{resp_rest.text[:400]}")
                return jsonify({
                    "status": "error",
                    "message": "Falha ao comentar no projeto.",
                    "details": {
                        "v3_status": status_v3,
                        "v3_text": text_v3,
                        "rest_status": resp_rest.status_code,
                        "rest_text": resp_rest.text[:400],
                    }
                }), 502
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route('/sync', methods=['POST'])
def sync_projects_endpoint():
    """Endpoint para acionar a sincronização de projetos do Zoho para o DB local."""
    try:
        synchronize_projects()
        return jsonify({"status": "success", "message": "Sincronização com Zoho concluída."})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Falha na sincronização: {e}"}), 500

@api_bp.route('/criar-projeto', methods=['POST'])
def api_criar_projeto():
    if 'credentials' not in session:
        return jsonify({"status": "error", "message": "Usuário não autenticado."}), 401
    
    try:
        creds = utils.build_google_credentials_from_session()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Falha nas credenciais Google: {e}"}), 401
    
    temp_deip_path = None
    try:
        if 'deip_pdf' not in request.files:
            return jsonify({"status": "error", "message": "Arquivo DEIP é obrigatório."}), 400
        
        deip_file = request.files['deip_pdf']
        dados = request.form.to_dict()

        # Normaliza campos do formulário esperados pela lógica
        dados['integracao_status'] = dados.get('integracao', 'n')
        checkbox_fields = [
            'integ_worklist','integ_laudos','integ_lab','integ_teleradiologia','integ_outros',
            'import_cadastros','import_prontuarios','import_laudos','import_imagens'
        ]
        for f in checkbox_fields:
            dados[f] = (f in request.form)
        
        filename = secure_filename(deip_file.filename)
        temp_deip_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
            url_nova_pasta = utils.criar_estrutura_no_drive(drive_service, dados)
            utils.atualizar_planilha_principal(sheets_service, dados, url_nova_pasta)
            utils.atualizar_planilha_secundaria(sheets_service, dados)
            
            id_do_novo_projeto = None
            # Monta payload validado para Zoho (com custom_fields e UDF)
            from dryrun_zoho_payload import montar_payload
            payload = montar_payload(dados)

            # Criar projeto no Zoho usando o template escolhido
            template_id = payload.get('copy_from')
            if template_id is not None:
                access_token = utils.obter_access_token()
                url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
                headers = {
                    "Authorization": f"Zoho-oauthtoken {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=45)
                resp.raise_for_status()
                projeto_criado = resp.json() if resp.text else {}
                id_do_novo_projeto = projeto_criado.get('id')

                # Reforço: PATCH dos custom_fields e UDF
                if id_do_novo_projeto:
                    patch_url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{id_do_novo_projeto}"
                    patch_payload = {
                        "custom_fields": payload.get('custom_fields', {}),
                        "custom_fields_udf": payload.get('custom_fields_udf', {}),
                    }
                    # Opcionalmente também no nível raiz conforme observado no script
                    patch_payload.update(payload.get('custom_fields', {}))
                    patch_resp = requests.patch(patch_url, headers=headers, json=patch_payload, timeout=45)
                    if patch_resp.status_code not in (200, 201):
                        print(f"PATCH custom_fields falhou: {patch_resp.status_code} - {patch_resp.text[:500]}")

                # Aguardar tempo suficiente para tarefas do template materializarem
                print("INFO: Aguardando sincronização das tarefas (45s)...")
                time.sleep(45)

                # Pós-criação: atribuir tarefas ao GP, concluir tarefas iniciais e lançar tempo
                try:
                    if id_do_novo_projeto and dados.get('gp_selecionado') in DONOS_PROJETO:
                        gp_zpuid = DONOS_PROJETO[dados['gp_selecionado']]

                        # 1) Listar tarefas do projeto (coletor rápido para reduzir latência)
                        tarefas_por_nome = {}
                        try:
                            tasks = _listar_tarefas_quick(str(id_do_novo_projeto), headers)
                        except Exception as e:
                            print(f"WARN: Coletor quick falhou: {e}")
                            tasks = []



                        if not tasks:
                            print("WARN: Não foi possível obter as tarefas do projeto.")
                        else:
                            try:
                                print(f"INFO: Tarefas obtidas: {len(tasks)}")
                            except Exception:
                                pass
                            for t in tasks:
                                nome = (t.get('name') or '').strip()
                                if nome:
                                    tarefas_por_nome[nome] = t
                            try:
                                nomes = list(tarefas_por_nome.keys())[:30]
                                print(f"INFO: Amostra de tarefas: {nomes}")
                            except Exception:
                                pass
                            print(f"INFO: Tarefas indexadas por nome: {len(tarefas_por_nome)}")

                        # Normalização de nomes para correspondência parcial/código prefixado
                        import unicodedata
                        def _normalize(n: str) -> str:
                            if not n:
                                return ''
                            t = n.strip()
                            # Remove prefixos de código do tipo "01.01 - "
                            try:
                                t = re.sub(r'^\s*\d+(?:\.\d+)*\s*-\s*', '', t)
                            except Exception:
                                pass
                            # Remove acentos para reduzir chances de mismatch
                            try:
                                t = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
                            except Exception:
                                pass
                            t = t.casefold()
                            t = ' '.join(t.split())
                            return t
                        tarefas_por_nome_norm = {}
                        for k, v in tarefas_por_nome.items():
                            tarefas_por_nome_norm[_normalize(k)] = v
                        def _get_task_by_name(nome_raw: str):
                            t = tarefas_por_nome.get(nome_raw)
                            if t:
                                return t
                            key = _normalize(nome_raw)
                            t2 = tarefas_por_nome_norm.get(key)
                            if t2:
                                try:
                                    print(f"INFO: Correspondência parcial por nome para '{nome_raw}' -> '{t2.get('name')}'")
                                except Exception:
                                    pass
                                return t2
                            # Busca por substring normalizada
                            for name, task in tarefas_por_nome.items():
                                try:
                                    norm_name = _normalize(name)
                                except Exception:
                                    norm_name = name
                                if norm_name == key or key in norm_name:
                                    try:
                                        print(f"INFO: Match por substring para '{nome_raw}' -> '{name}'")
                                    except Exception:
                                        pass
                                    return task
                            return None

                        # 3) Atribuir tarefas ao GP
                        for nome_tarefa in TAREFAS_PARA_ATRIBUIR:
                            t = _get_task_by_name(nome_tarefa)
                            if not t:
                                print(f"INFO: Tarefa para atribuir não encontrada no projeto: '{nome_tarefa}'")
                                continue
                            owner = (t.get('owner') or {}).get('zpuid')
                            if str(owner) == str(gp_zpuid):
                                continue
                            try:
                                task_id = t.get('id')
                                try:
                                    url_rest = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{id_do_novo_projeto}/tasks/{task_id}/"
                                    headers_rest = {"Authorization": f"Bearer {access_token}"}
                                    payload_rest = {"person_responsible": str(gp_zpuid)}
                                    resp_rest = requests.post(url_rest, headers=headers_rest, data=payload_rest, timeout=45)
                                    if resp_rest.status_code in (200, 201):
                                        print(f"INFO: Atribuição via REST bem-sucedida '{nome_tarefa}'.")
                                    else:
                                        print(f"WARN: Atribuição (REST) falhou '{nome_tarefa}': {resp_rest.status_code} - {resp_rest.text[:400]}")
                                except Exception as e2:
                                    print(f"WARN: Erro no REST de atribuição '{nome_tarefa}': {e2}")
                            except Exception as e:
                                print(f"WARN: Erro ao atribuir '{nome_tarefa}': {e}")

                        # 4) Concluir tarefas iniciais (atribui ao GP se necessário)
                        for nome_tarefa in TAREFAS_PARA_CONCLUIR:
                            t = _get_task_by_name(nome_tarefa)
                            if not t:
                                print(f"INFO: Tarefa para concluir não encontrada no projeto: '{nome_tarefa}'")
                                continue
                            try:
                                task_id = t.get('id')
                                url_patch_task = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{id_do_novo_projeto}/tasks/{task_id}"
                                # Garante ownership pelo GP: tentar REST primeiro
                                owner = (t.get('owner') or {}).get('zpuid')
                                if str(owner) != str(gp_zpuid):
                                    try:
                                        url_rest_assign = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{id_do_novo_projeto}/tasks/{task_id}/"
                                        headers_rest = {"Authorization": f"Bearer {access_token}"}
                                        payload_rest_assign = {"person_responsible": str(gp_zpuid)}
                                        resp_rest_assign = requests.post(url_rest_assign, headers=headers_rest, data=payload_rest_assign, timeout=45)
                                        if resp_rest_assign.status_code in (200, 201):
                                            print(f"INFO: Reatribuição (REST) bem-sucedida para '{nome_tarefa}'.")
                                    except Exception as _:
                                        print(f"WARN: Reatribuição (REST) falhou para '{nome_tarefa}'. Prosseguindo.")
                                # Marca como concluída via REST
                                try:
                                    url_rest_done = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{id_do_novo_projeto}/tasks/{task_id}/"
                                    headers_rest_done = {"Authorization": f"Bearer {access_token}"}
                                    payload_rest_done = {"custom_status": STATUS_CONCLUIDO_ID}
                                    resp_rest_done = requests.post(url_rest_done, headers=headers_rest_done, data=payload_rest_done, timeout=45)
                                    if resp_rest_done.status_code in (200, 201):
                                        print(f"INFO: Conclusão via REST bem-sucedida '{nome_tarefa}'.")
                                    else:
                                        print(f"WARN: Conclusão (REST) falhou '{nome_tarefa}': {resp_rest_done.status_code} - {resp_rest_done.text[:400]}")
                                except Exception as e2:
                                    print(f"WARN: Erro no REST de conclusão '{nome_tarefa}': {e2}")
                            except Exception as e:
                                print(f"WARN: Erro ao concluir '{nome_tarefa}': {e}")

                        # 5) Lançar timesheet nas tarefas concluídas conforme TEMPO_RELATO
                        from datetime import date as _date
                        hoje = _date.today().strftime('%Y-%m-%d')
                        for nome_tarefa, tempo_hhmm in TEMPO_RELATO.items():
                            t = _get_task_by_name(nome_tarefa)
                            if not t:
                                continue
                            try:
                                task_id = t.get('id')
                                # Timesheet diretamente via REST (MM-DD-YYYY)
                                try:
                                    from datetime import datetime as _dt
                                    mmddyyyy = _dt.strptime(hoje, "%Y-%m-%d").strftime("%m-%d-%Y")
                                    url_rest = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{id_do_novo_projeto}/tasks/{task_id}/logs/"
                                    headers_rest = {"Authorization": f"Bearer {access_token}"}
                                    payload_rest = {
                                        "owner_zpuid": str(gp_zpuid),
                                        "hours": tempo_hhmm,
                                        "date": mmddyyyy,
                                        "bill_status": "Billable",
                                        "notes": "Relatado via automação."
                                    }
                                    resp_rest = requests.post(url_rest, headers=headers_rest, data=payload_rest, timeout=45)
                                    if resp_rest.status_code in (200, 201):
                                        print(f"INFO: Timesheet via REST bem-sucedido '{nome_tarefa}'.")
                                    else:
                                        print(f"WARN: Timesheet (REST) falhou '{nome_tarefa}': {resp_rest.status_code} - {resp_rest.text[:400]}")
                                except Exception as e2:
                                    print(f"WARN: Erro no REST de timesheet '{nome_tarefa}': {e2}")
                            except Exception as e:
                                print(f"WARN: Erro ao lançar timesheet '{nome_tarefa}': {e}")
                    else:
                        print("INFO: Projeto não criado ou GP inválido; etapa de pós-criação ignorada.")
                except Exception as e:
                    print(f"WARN: Falha geral no pós-criação (atribuição/conclusão/timesheets): {e}")
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
                from sync_zoho import synchronize_single_project

                token_para_sync = access_token if 'access_token' in locals() and access_token else utils.obter_access_token()
                projeto_json = synchronize_single_project(str(id_do_novo_projeto), token_para_sync)
                if projeto_json:
                    # Recarrega do banco para garantir consistência com o cache
                    registro_db = database.get_project_by_id(str(id_do_novo_projeto))
                    if registro_db and registro_db['full_data_json']:
                        dados_zoho = json.loads(registro_db['full_data_json'])
                        nome_projeto = dados_zoho.get('name', utils.construir_titulo_projeto(dados))
                        cliente = (
                            (dados_zoho.get('client_company') or {}).get('name')
                            or (dados_zoho.get('client') or {}).get('name')
                            or dados_zoho.get('client_name')
                            or "Cliente não informado"
                        )
                        gp_nome = (dados_zoho.get('owner') or {}).get('name', 'GP não informado')
                        produto_info = ''
                        if ' - NR/AP' in nome_projeto:
                            produto_info = 'netRIS e AnimatiPACS'
                        elif ' - NR' in nome_projeto:
                            produto_info = 'netRIS'
                        elif ' - AP' in nome_projeto:
                            produto_info = 'AnimatiPACS'
                        novo_projeto = {
                            "id": str(registro_db['id']),
                            "nome": nome_projeto,
                            "cliente": cliente,
                            "gp": gp_nome,
                            "data_inicio": dados_zoho.get('start_date', ''),
                            "data_criacao": dados_zoho.get('created_time', ''),
                            "data_inicio_formatada": (dados_zoho.get('start_date') or '').replace('-', '/'),
                            "dias_na_fase": registro_db.get('dias_na_fase') or utils.calcular_dias_na_fase(dados_zoho, utils.determinar_coluna_projeto(dados_zoho)),
                            "dias_total": registro_db.get('dias_total') or utils.calcular_dias_total_projeto(dados_zoho.get('start_date'), dados_zoho.get('created_time')),
                            "status_atual": utils.determinar_coluna_projeto(dados_zoho),
                            "produto": produto_info
                        }
            except Exception as sync_error:
                print(f"WARN: Falha ao sincronizar projeto recém-criado {id_do_novo_projeto}: {sync_error}")
                novo_projeto = None
            if not novo_projeto:
                try:
                    novo_projeto = {
                        "id": str(id_do_novo_projeto),
                        "nome": utils.construir_titulo_projeto(dados),
                        "cliente": f"{dados['codigo_contrato_numero']} - {dados['nome_cliente']}",
                        "gp": dados.get('gp_selecionado', 'GP não informado'),
                        "data_inicio_formatada": dados.get('start_date', '').replace('-', '/'),
                        "dias_na_fase": "0 dias",
                        "status_atual": "Aguardando Onboarding"
                    }
                except Exception:
                    novo_projeto = None
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

@api_bp.route('/carregar_projetos', methods=['POST'])
def carregar_projetos():
    """Carrega projetos para o Kanban a partir do banco de dados local (cache)."""
    try:
        data = request.json
        gp_selecionado = data.get('gp')
        if not gp_selecionado or gp_selecionado not in DONOS_PROJETO:
            return jsonify({"erro": "GP inválido"}), 400
        
        id_do_gp = DONOS_PROJETO[gp_selecionado]

        # Conecta ao banco de dados para buscar os projetos cacheados
        conn = database.get_db_connection()
        # Carrega todos os projetos relevantes do banco de dados
        # O campo full_data_json contém o JSON original do Zoho
        rows = conn.execute('SELECT full_data_json FROM projects').fetchall()
        conn.close()

        lista_completa_projetos = [json.loads(row['full_data_json']) for row in rows]
        
        # O resto da lógica permanece o mesmo, pois opera sobre a estrutura de dados do Zoho
        projetos_do_gp = [p for p in lista_completa_projetos if p.get('owner', {}).get('zpuid') == id_do_gp]
        
        projetos_por_status = {}
        colunas_validas = {
            "Aguardando Onboarding", "Falta Liberar Servidor Infra", "Em Andamento",
            "Em Andamento - Implantação", "Em Homologação", "Em Virada", 
            "Em Operação Assistida", "Aguardando Encerramento", "Projeto Parado", 
            "Finalizado", "Cancelado", "Status Desconhecido"
        }
        projetos_nao_mapeados = []

        for projeto in projetos_do_gp:
            # Ignora projetos finalizados ou cancelados que ainda possam estar no cache
            status_nome = (projeto.get('status', {}).get('name', '') or '').lower()
            if projeto.get('is_completed') or status_nome in ('finalizado', 'cancelado'):
                continue

            status_kanban = utils.determinar_coluna_projeto(projeto)
            if status_kanban not in projetos_por_status:
                projetos_por_status[status_kanban] = []

            cliente = (
                projeto.get('client_company', {}).get('name')
                or projeto.get('client', {}).get('name')
                or projeto.get('client_name')
                or "Cliente não informado"
            )
            nome_projeto = projeto.get('name', '')
            produto_info = ''
            if ' - NR/AP' in nome_projeto:
                produto_info = 'netRIS e AnimatiPACS'
            elif ' - NR' in nome_projeto:
                produto_info = 'netRIS'
            elif ' - AP' in nome_projeto:
                produto_info = 'AnimatiPACS'

            info_projeto = {
                'id': projeto.get('id'),
                'nome': nome_projeto,
                'cliente': cliente,
                'gp': projeto.get('owner', {}).get('name', 'GP não informado'),
                'data_inicio': projeto.get('start_date', ''),
                'data_criacao': projeto.get('created_time', ''),
                'data_inicio_formatada': projeto.get('start_date', ''),
                'dias_na_fase': '',  # Será preenchido por chamadas individuais
                'dias_total': utils.calcular_dias_total_projeto(projeto.get('start_date', ''), projeto.get('created_time', '')),
                'status_atual': status_kanban,
                'produto': produto_info
            }
            projetos_por_status[status_kanban].append(info_projeto)

            if status_kanban not in colunas_validas:
                projetos_nao_mapeados.append({
                    'id': projeto.get('id'), 'nome': projeto.get('name'),
                    'status_id': str(projeto.get('status', {}).get('id', '')),
                    'status_nome': str(projeto.get('status', {}).get('name', '')),
                    'tags': [str(t.get('id', '')) for t in (projeto.get('tags') or [])],
                    'status_kanban': status_kanban,
                })

        if projetos_nao_mapeados:
            print("==== AUDITORIA: Projetos fora do mapeamento ====")
            for p in projetos_nao_mapeados:
                print(f"ID={p['id']} | Nome={p['nome']} | Status={p['status_nome']} ({p['status_id']}) | Tags={p['tags']} | Mapeado como='{p['status_kanban']}'")
            print("=================================================")

        for status, projetos in projetos_por_status.items():
            projetos_por_status[status] = sorted(projetos, key=lambda p: p['nome'])
            
        return jsonify({
            "sucesso": True,
            "projetos": projetos_por_status,
            "total": len(projetos_do_gp)
        })
    except Exception as e:
        print(f"Erro ao carregar projetos do cache: {e}")
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500

@api_bp.route('/impeditivos/<project_id>', methods=['GET'])
def api_impeditivos(project_id):
    try:
        # Agora sem chamadas à API do Zoho: contamos direto no banco
        count = database.count_open_impediments(project_id)
        # Monta uma URL web, se possível, a partir de qualquer tasklist sincronizada
        tasklist_id = database.get_any_impediments_tasklist_id(project_id)
        web_url = None
        if tasklist_id:
            # Como não vamos consultar o portal dinâmico via API aqui, usamos o host configurado
            base_web = utils._projects_web_root()
            web_url = utils._compose_tasklist_web_url(
                base_web, project_id, tasklist_id, DEFAULT_TASKS_CUSTOM_VIEW_ID
            )
        return jsonify({"project_id": project_id, "count": count, "has_impediments": count > 0, "web_url": web_url})
    except Exception as e:
        print(f"Erro no endpoint impeditivos: {e}")
        return jsonify({"erro": str(e)}), 500

@api_bp.route('/dias-na-fase/<project_id>', methods=['GET'])
def api_dias_na_fase(project_id):
    try:
        coluna = request.args.get('coluna')  # coluna alvo (opcional, vindo do frontend)
        # Trate a presença de 'coluna' como dica implícita para precisão dos cálculos
        use_coluna = bool(coluna)

        # Cache: por projeto (genérico) ou por projeto+coluna quando usar dica
        key = f"{project_id}|{coluna}" if use_coluna else f"{project_id}"
        now = int(time.time())
        ent = current_app.config['_DIAS_FASE_CACHE'].get(key)
        if ent and (now - ent.get('ts', 0) <= current_app.config['_CACHE_TTL_SECONDS']):
            return jsonify({"project_id": project_id, "dias_na_fase": ent.get('valor', 'N/D')})

        # Tenta buscar do DB local primeiro
        project_row = database.get_project_by_id(project_id)
        if project_row:
            try:
                dias_fase = project_row['dias_na_fase']
            except Exception:
                dias_fase = None
            if dias_fase:
                return jsonify({"project_id": project_id, "dias_na_fase": dias_fase})

        # Agora evitamos chamadas à API do Zoho; calculamos a partir do banco
        valor = None

        # Se houver dica de coluna, ainda assim ficamos restritos ao DB: usamos data_inicio/data_criacao
        # gravadas no projeto para um cálculo aproximado e consistente.
        try:
            node = None
            if project_row and project_row['full_data_json']:
                node = json.loads(project_row['full_data_json'])
            if isinstance(node, dict):
                start_date = node.get('start_date') or node.get('start_date_string') or (project_row['data_inicio'] if project_row else '')
                created_time = node.get('created_time') or node.get('created_time_string') or (project_row['data_criacao'] if project_row else '')
            else:
                start_date = (project_row['data_inicio'] if project_row else '')
                created_time = (project_row['data_criacao'] if project_row else '')
            info_min = { 'data_inicio': start_date, 'data_criacao': created_time }
            valor = utils.calcular_dias_na_fase(info_min, None)
        except Exception as e:
            print(f"[AUDIT][dias-na-fase][db-only-fallback-error] project_id={project_id} coluna='{coluna or ''}' erro='{e}'")
            valor = None

        if not valor:
            valor = 'N/D'
        current_app.config['_DIAS_FASE_CACHE'][key] = { 'valor': valor, 'ts': now }
        return jsonify({"project_id": project_id, "dias_na_fase": valor})
    except Exception as e:
        print(f"Erro no endpoint dias-na-fase: {e}")
        return jsonify({"erro": str(e)}), 500

@api_bp.route('/mover_projeto', methods=['POST'])
def api_mover_projeto():
    """Orquestra a movimentação do projeto entre colunas (Zoho + Sheets + DB)."""
    try:
        if 'credentials' not in session:
            return jsonify({"sucesso": False, "erro": "Usuário não autenticado."}), 401

        payload = request.get_json(force=True) or {}
        projeto_id = str(payload.get('projeto_id') or '').strip()
        coluna_origem = (payload.get('coluna_origem') or '').strip()
        coluna_destino = (payload.get('coluna_destino') or '').strip()
        cliente_sheet = (payload.get('cliente_sheet') or '').strip()

        if not projeto_id or not coluna_destino:
            return jsonify({"sucesso": False, "erro": "Parâmetros inválidos."}), 400

        project_row = database.get_project_by_id(projeto_id)
        if not project_row:
            return jsonify({"sucesso": False, "erro": f"Projeto {projeto_id} não encontrado no cache."}), 404

        try:
            creds_in_session = session.get('credentials') if isinstance(session.get('credentials'), dict) else None
            if not creds_in_session or not creds_in_session.get('refresh_token'):
                return jsonify({
                    "sucesso": False,
                    "erro": "Sessão sem refresh_token. Faça login novamente para conceder acesso offline.",
                    "acao": "/login"
                }), 401
        except Exception:
            pass

        full_data_json = project_row['full_data_json'] if 'full_data_json' in project_row.keys() else None
        detalhes_zoho = json.loads(full_data_json) if full_data_json else {}
        colmap = utils.carregar_mapeamento_colunas()
        info_dest = colmap.get(coluna_destino) or {}
        if not info_dest:
            return jsonify({
                "sucesso": False,
                "erro": f"Coluna destino '{coluna_destino}' não possui mapeamento configurado."
            }), 400

        try:
            access_token = utils.obter_access_token()
        except Exception as exc:
            _log_move_error("[MOVE][AUTH]", projeto_id, coluna_destino, f"Falha ao obter access token: {exc}")
            return jsonify({"sucesso": False, "erro": "Falha na autenticação Zoho."}), 502

        msg_operacoes: list[str] = []

        if coluna_origem == "Falta Liberar Servidor Infra" and coluna_destino == "Em Andamento":
            data_atual = date.today().strftime('%Y-%m-%d')
            conn = database.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE projects SET data_liberacao_servidor = ? WHERE id = ?",
                    (data_atual, projeto_id)
                )
                cursor.execute(
                    "UPDATE projects SET data_ultima_mudanca = ? WHERE id = ?",
                    (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), projeto_id)
                )
                conn.commit()
                msg_operacoes.append("Banco de dados: campos data_liberacao_servidor e data_ultima_mudanca atualizados")
            except Exception as e:
                msg_operacoes.append(f"Erro ao atualizar banco de dados: {str(e)}")
            finally:
                conn.close()

            # Atualizar campo customizado data_liberacao_servidor no Zoho
            try:
                access_token = utils.obter_access_token()
                utils.atualizar_custom_field_projeto(access_token, projeto_id, "data_liberacao_servidor", data_atual)
                msg_operacoes.append("Zoho: campo customizado data_liberacao_servidor atualizado com data de liberação do servidor")
            except Exception as e:
                msg_operacoes.append(f"Erro ao atualizar campo customizado no Zoho: {str(e)}")

        try:
            _atualizar_zoho(
                projeto_id=projeto_id,
                coluna_destino=coluna_destino,
                info_dest=info_dest,
                access_token=access_token,
                detalhes_zoho=detalhes_zoho,
                coletor_mensagens=msg_operacoes,
                coluna_origem=coluna_origem
            )
        except Exception:
            _log_move_error("[MOVE][ZOHO]", projeto_id, coluna_destino, "Falha durante atualização Zoho.", coluna_origem)
            raise

        try:
            _atualizar_planilha(
                projeto_id=projeto_id,
                coluna_destino=coluna_destino,
                info_dest=info_dest,
                cliente_sheet=cliente_sheet,
                detalhes_zoho=detalhes_zoho,
                coletor_mensagens=msg_operacoes,
                project_row=project_row,
                coluna_origem=coluna_origem
            )
        except Exception:
            _log_move_error("[MOVE][SHEET]", projeto_id, coluna_destino, "Falha durante atualização da planilha.", coluna_origem)
            raise

        try:
            _sincronizar_db_local(
                projeto_id=projeto_id,
                access_token=access_token,
                coletor_mensagens=msg_operacoes
            )
        except Exception:
            _log_move_error("[MOVE][DB]", projeto_id, coluna_destino, "Falha durante sincronização do banco local.", coluna_origem)
            raise

        return jsonify({
            "sucesso": True,
            "mensagem": "; ".join(msg_operacoes) or 'Movimentação registrada.'
        })

    except Exception as exc:
        traceback.print_exc()
        context_project = locals().get('projeto_id', '<indefinido>')
        context_dest = locals().get('coluna_destino', '<indefinida>')
        context_origin = locals().get('coluna_origem', '<indefinida>')
        _log_move_error("[MOVE][UNHANDLED]", context_project, context_dest, str(exc), context_origin)
        return jsonify({"sucesso": False, "erro": str(exc)}), 500


def _log_move_error(prefix: str, projeto_id: str | None, coluna_destino: str | None, mensagem: str, coluna_origem: str | None = None, extra: dict | None = None) -> None:
    """Centraliza logs de erro do fluxo de movimentação com contexto estruturado."""
    try:
        payload = {
            "projeto_id": projeto_id,
            "coluna_destino": coluna_destino,
            "coluna_origem": coluna_origem,
            "mensagem": mensagem,
            "extra": extra or {}
        }
        print(f"{prefix} {json.dumps(payload, ensure_ascii=False)}")
    except Exception as log_exc:
        print(f"[MOVE][LOG][FALLBACK] prefix={prefix} projeto={projeto_id} destino={coluna_destino} erro={mensagem} fallback={log_exc}")


def _log_move_info(prefix: str, projeto_id: str, coluna_destino: str, detalhe: str, coluna_origem: str | None = None, extra: dict | None = None) -> None:
    """Log informativo padronizado para o fluxo de movimentação."""
    try:
        payload = {
            "projeto_id": projeto_id,
            "coluna_destino": coluna_destino,
            "coluna_origem": coluna_origem,
            "detalhe": detalhe,
            "extra": extra or {}
        }
        print(f"{prefix} {json.dumps(payload, ensure_ascii=False)}")
    except Exception as log_exc:
        print(f"[MOVE][LOG][INFO-FALLBACK] prefix={prefix} projeto={projeto_id} destino={coluna_destino} detalhe={detalhe} fallback={log_exc}")


def _validar_planilha_move(info_dest: dict, cliente_sheet: str) -> None:
    sheet_target = (info_dest or {}).get('sheetStatus')
    exige_cliente = bool(sheet_target)
    if exige_cliente and not cliente_sheet:
        raise ValueError("Cliente da planilha não informado para atualização do status")


def _atualizar_zoho(
    projeto_id: str,
    coluna_destino: str,
    info_dest: dict,
    access_token: str,
    detalhes_zoho: dict,
    coletor_mensagens: list,
    coluna_origem: str | None = None
) -> None:
    """Atualiza o projeto no Zoho conforme o mapeamento da coluna destino."""
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    base_url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}"

    # 1) Atualiza status e campos customizados
    payload_patch: dict = {}
    status_id = info_dest.get("zohoStatusId")
    if status_id:
        payload_patch["status"] = {"id": status_id}

    # Processa campos customizados do destino
    custom_fields = info_dest.get("zohoCustomFields", {}) or {}
    
    # Processa campos customizados do evento onExit da coluna de origem
    if coluna_origem:
        from utils import carregar_mapeamento_colunas
        mapeamento = carregar_mapeamento_colunas()
        config_origem = mapeamento.get(coluna_origem, {})
        on_exit = config_origem.get("onExit", {})
        exit_custom_fields = on_exit.get("zohoCustomFields", {})
        if exit_custom_fields:
            custom_fields.update(exit_custom_fields)

    if custom_fields:
        payload_patch["custom_fields"] = _resolver_custom_fields(custom_fields)

    if payload_patch:
        print(f"[DEBUG] Enviando PATCH para {base_url}")
        print(f"[DEBUG] Headers: {headers}")
        print(f"[DEBUG] Payload: {payload_patch}")
        response_patch = requests.patch(base_url, headers=headers, json=payload_patch, timeout=45)
        print(f"[DEBUG] Status code: {response_patch.status_code}")
        print(f"[DEBUG] Resposta: {response_patch.text[:1000]}")
        
        if response_patch.status_code not in (200, 201):
            raise RuntimeError(
                f"Falha ao atualizar projeto no Zoho (status/custom): {response_patch.status_code} - {response_patch.text[:400]}"
            )

        # Fallback para tenants que exigem campos customizados no topo do payload
        if custom_fields:
            try:
                response_data = response_patch.json()
            except Exception:
                response_data = None

            resolved_values = _resolver_custom_fields(custom_fields)
            updated_ok = _verificar_campos_customizados(response_data, resolved_values)

            if not updated_ok:
                inline_payload = _resolver_custom_fields(custom_fields)
                response_inline = requests.patch(base_url, headers=headers, json=inline_payload, timeout=45)
                if response_inline.status_code not in (200, 201):
                    raise RuntimeError(
                        f"Falha ao atualizar projeto no Zoho (fallback custom): {response_inline.status_code} - {response_inline.text[:400]}"
                    )

                try:
                    inline_response_data = response_inline.json()
                except Exception:
                    inline_response_data = None

                if not _verificar_campos_customizados(inline_response_data, inline_payload):
                    try:
                        project_id_hint = base_url.rstrip('/').split('/')[-1]
                        print(
                            f"[MOVE][ZOHO][WARN] Campos customizados não confirmados após fallback; prosseguindo. projeto={project_id_hint} payload={inline_payload} response={inline_response_data}"
                        )
                    except Exception:
                        pass

    # 2) Ajuste de tags
    _ajustar_tags_projeto(base_url, headers, info_dest, detalhes_zoho, coluna_destino)

    # 3) Disparo de triggers configurados
    triggers = info_dest.get("triggers", []) or []
    if triggers:
        _executar_triggers(
            triggers=triggers,
            projeto_id=projeto_id,
            coluna_destino=coluna_destino,
            detalhes_zoho=detalhes_zoho,
            headers=headers,
            access_token=access_token
        )

    mensagem = f"Projeto atualizado no Zoho para '{coluna_destino}'."
    coletor_mensagens.append(mensagem)
    _log_move_info("[MOVE][ZOHO]", projeto_id, coluna_destino, mensagem, coluna_origem)


def _resolver_custom_fields(custom_fields: dict) -> dict:
    """Resolve placeholders e converte campos especiais antes de enviar ao Zoho."""
    print("[DEBUG] Resolvendo campos customizados...")
    print(f"[DEBUG] Campos recebidos: {custom_fields}")
    resolved = {}
    for chave, valor in (custom_fields or {}).items():
        print(f"[DEBUG] Processando campo: {chave} = {valor}")
        if isinstance(valor, str) and valor.upper() == "CURRENT_DATE":
            resolved[chave] = date.today().strftime("%Y-%m-%d")
            print(f"[DEBUG] Campo {chave} resolvido para: {resolved[chave]}")
        else:
            resolved[chave] = valor
            print(f"[DEBUG] Campo {chave} mantido como: {resolved[chave]}")
    print(f"[DEBUG] Campos resolvidos: {resolved}")
    return resolved


def _verificar_campos_customizados(response_data: dict | None, valores_esperados: dict) -> bool:
    """Confere se os valores esperados aparecem em possíveis estruturas retornadas pelo Zoho."""
    print(f"[DEBUG] Verificando campos customizados na resposta...")
    print(f"[DEBUG] Resposta da API: {response_data}")
    print(f"[DEBUG] Valores esperados: {valores_esperados}")
    
    if not isinstance(response_data, dict):
        print("[DEBUG] Resposta não é um dicionário")
        return False

    def _collect_candidates(obj: dict) -> list[dict]:
        candidatos: list[dict] = []
        stack: list[dict] = [obj]
        while stack:
            atual = stack.pop()
            if not isinstance(atual, dict):
                continue
            candidatos.append(atual)
            nested_project = atual.get("project")
            if isinstance(nested_project, dict):
                stack.append(nested_project)
            nested_projects = atual.get("projects")
            if isinstance(nested_projects, list):
                for item in nested_projects:
                    if isinstance(item, dict):
                        stack.append(item)
        return candidatos

    def _match_valor(esperado: Any, atual: Any) -> bool:
        if esperado == atual:
            return True
        if isinstance(esperado, str) and isinstance(atual, str):
            return esperado.strip().lower() == atual.strip().lower()
        return False

    candidatos = _collect_candidates(response_data)
    if not candidatos:
        return False

    for chave, esperado in (valores_esperados or {}).items():
        chave_norm = (chave or "").strip().lower()
        encontrado = False

        for candidato in candidatos:
            custom_fields = candidato.get("custom_fields")
            if isinstance(custom_fields, dict):
                for nome, valor in custom_fields.items():
                    if (nome or "").strip().lower() == chave_norm and _match_valor(esperado, valor):
                        encontrado = True
                        break
                if encontrado:
                    break
            elif isinstance(custom_fields, list):
                for item in custom_fields:
                    if not isinstance(item, dict):
                        continue
                    nomes_possiveis = [
                        (item.get("column_name") or "").strip().lower(),
                        (item.get("api_name") or "").strip().lower(),
                        (item.get("link_name") or "").strip().lower(),
                        (item.get("name") or "").strip().lower(),
                    ]
                    if chave_norm in nomes_possiveis and _match_valor(esperado, item.get("value")):
                        encontrado = True
                        break
                if encontrado:
                    break

            valor_direto = candidato.get(chave)
            if valor_direto is not None and _match_valor(esperado, valor_direto):
                encontrado = True
                break

            valor_cf_prefixed = candidato.get(f"cf_{chave}")
            if valor_cf_prefixed is not None and _match_valor(esperado, valor_cf_prefixed):
                encontrado = True
                break

        if not encontrado:
            return False

    return True


def _carregar_tags_atuais(base_url: str, headers: dict, detalhes_zoho: dict | None) -> list[dict]:
    """Retorna a lista atual de tags do projeto, priorizando dados frescos da API."""
    def _extrair_tags(origem: dict | None) -> list[dict] | None:
        if isinstance(origem, dict):
            bruto = origem.get("tags")
            if isinstance(bruto, list):
                return [tag for tag in bruto if isinstance(tag, dict)]
        return None

    tags_existentes = _extrair_tags(detalhes_zoho) or []

    try:
        response = requests.get(base_url, headers=headers, timeout=30)
        if response.status_code in (200, 201):
            try:
                data = response.json()
            except Exception:
                data = None

            projeto = None
            if isinstance(data, dict):
                if isinstance(data.get("project"), dict):
                    projeto = data["project"]
                elif data.get("id"):
                    projeto = data
                elif isinstance(data.get("projects"), list) and data["projects"]:
                    projeto = data["projects"][0]

            tags_api = _extrair_tags(projeto)
            if tags_api is not None:
                tags_existentes = tags_api
        else:
            try:
                print(
                    f"[MOVE][ZOHO][WARN] Falha ao buscar tags atuais (HTTP {response.status_code}): {response.text[:200]}"
                )
            except Exception:
                pass
    except Exception as exc:
        try:
            project_id_hint = base_url.rstrip('/').split('/')[-1]
            print(f"[MOVE][ZOHO][WARN] Erro ao consultar tags do projeto {project_id_hint}: {exc}")
        except Exception:
            pass

    return tags_existentes


def _ajustar_tags_projeto(base_url: str, headers: dict, info_dest: dict, detalhes_zoho: dict, coluna_destino: str) -> None:
    """Reconstrói a lista de tags do projeto no Zoho com base nas informações atuais."""
    add_tags = info_dest.get("zohoTagsToAdd", []) or []
    remove_tags = info_dest.get("zohoTagsToRemove", []) or []

    if coluna_destino == "Em Andamento":
        # Remove all tags
        payload_tags = {"tags": []}
        response_tags = requests.patch(base_url, headers=headers, json=payload_tags, timeout=45)
        if response_tags.status_code not in (200, 201):
            raise RuntimeError(
                f"Falha ao remover tags: {response_tags.status_code} - {response_tags.text[:400]}"
            )
        return

    if not add_tags and not remove_tags:
        return

    def _normalize_tag(tag_val):
        if isinstance(tag_val, dict):
            cleaned = {}
            for k in ("id", "name"):
                if k in tag_val and tag_val[k] not in (None, ""):
                    cleaned[k] = str(tag_val[k]).strip()
            return cleaned or None
        tag_str = str(tag_val).strip()
        if not tag_str:
            return None
        if tag_str.isdigit():
            return {"id": tag_str}
        return {"name": tag_str}

    atuais = _carregar_tags_atuais(base_url, headers, detalhes_zoho)

    def _tag_key(entry: dict) -> tuple[str, str]:
        value = entry.get("id")
        if value:
            return ("id", str(value))
        return ("name", str(entry.get("name", "")).strip().lower())

    tags_por_chave: dict[tuple[str, str], dict] = {}
    for tag in atuais:
        normalizada = _normalize_tag(tag)
        if not normalizada:
            continue
        tags_por_chave[_tag_key(normalizada)] = normalizada

    for tag in remove_tags:
        normalizada = _normalize_tag(tag)
        if not normalizada:
            continue
        tags_por_chave.pop(_tag_key(normalizada), None)

    for tag in add_tags:
        normalizada = _normalize_tag(tag)
        if not normalizada:
            continue
        tags_por_chave[_tag_key(normalizada)] = normalizada

    novas_tags = list(tags_por_chave.values())
    payload_tags = {"tags": novas_tags}
    response_tags = requests.patch(base_url, headers=headers, json=payload_tags, timeout=45)
    if response_tags.status_code not in (200, 201):
        raise RuntimeError(
            f"Falha ao ajustar tags: {response_tags.status_code} - {response_tags.text[:400]}"
        )


def _executar_triggers(
    triggers: list,
    projeto_id: str,
    coluna_destino: str,
    detalhes_zoho: dict,
    headers: dict,
    access_token: str
) -> None:
    """Executa os gatilhos associados à coluna destino."""
    for trigger in triggers:
        if not isinstance(trigger, dict):
            continue
        tipo = trigger.get("type")
        if tipo == "projectComment":
            _postar_comentario_projeto(projeto_id, headers, trigger.get("template", ""))
        elif tipo == "taskComment":
            _postar_comentario_tarefa(
                projeto_id=projeto_id,
                headers=headers,
                detalhes_zoho=detalhes_zoho,
                trigger=trigger
            )
        elif tipo == "workflow":
            nome_workflow = trigger.get("name")
            if nome_workflow:
                try:
                    synchronize_single_project.trigger_workflow  # type: ignore[attr-defined]
                except AttributeError:
                    from sync_zoho import trigger_workflow
                    trigger_workflow(projeto_id, nome_workflow, access_token)
                else:
                    from sync_zoho import trigger_workflow
                    trigger_workflow(projeto_id, nome_workflow, access_token)


def _postar_comentario_projeto(projeto_id: str, headers: dict, template: str) -> None:
    if not template:
        return
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}/comments"
    response = requests.post(url, headers=headers, json={"content": template}, timeout=30)
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Falha ao postar comentário de projeto: {response.status_code} - {response.text[:400]}"
        )


def _postar_comentario_tarefa(projeto_id: str, headers: dict, detalhes_zoho: dict, trigger: dict) -> None:
    task_name = (trigger or {}).get("taskName")
    template = (trigger or {}).get("template")
    is_optional = (trigger or {}).get("optional", False)
    
    if not task_name or not template:
        return

    tarefas = _listar_tarefas_quick(projeto_id, headers)
    alvo = None
    task_name_norm = (task_name or "").strip().casefold()

    for tarefa in tarefas:
        nome_tarefa = (tarefa.get("name") or "").strip()
        if not nome_tarefa:
            continue
        nome_norm = nome_tarefa.casefold()
        if nome_norm == task_name_norm or nome_norm.startswith(task_name_norm) or task_name_norm in nome_norm:
            alvo = tarefa
            break

    if not alvo:
        exemplos = ", ".join((t.get("name") or "<sem nome>") for t in tarefas[:10])
        if is_optional:
            print(f"[DEBUG] Tarefa opcional '{task_name}' não encontrada para comentário - pulando")
            return  # Retorna sem erro para tarefas opcionais
        else:
            print(f"[DEBUG] Tarefa obrigatória '{task_name}' não encontrada para comentário. Tarefas disponíveis: {exemplos}")
            raise RuntimeError(
                f"Tarefa obrigatória '{task_name}' não encontrada para comentário. Encontradas: {exemplos}"
            )

    mentions_text = utils.zoho_mentions(["Giovani Sousa"])
    
    # Processar o template substituindo as menções
    comentario_template = template.replace("@{Giovani Sousa}", mentions_text)
    
    task_id = alvo.get("id")
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}/tasks/{task_id}/comments"
    payload = {"comment": comentario_template, "content": comentario_template}
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Falha ao postar comentário na tarefa '{task_name}': {response.status_code} - {response.text[:400]}"
        )


def _render_template_mencoes(template: str, mentions: list) -> str:
    if not mentions:
        return template
    partes = []
    for mention in mentions:
        info = ZOHO_MENTION_USERS.get(mention)
        if not info:
            continue
        partes.append(f"<@{info['usernum']}:{info['name']}>")
    bloco_mentions = ", ".join(partes)
    return template.replace("{mentions}", bloco_mentions or "")


def _atualizar_planilha(
    projeto_id: str,
    coluna_destino: str,
    info_dest: dict,
    cliente_sheet: str,
    detalhes_zoho: dict,
    coletor_mensagens: list,
    project_row: sqlite3.Row | dict | None = None,
    coluna_origem: str | None = None
) -> None:
    """Atualiza a planilha principal conforme o novo status."""
    _validar_planilha_move(info_dest, cliente_sheet)

    sheet_status = (info_dest or {}).get("sheetStatus")
    print(f"[DEBUG][SHEET] sheet_status obtido: '{sheet_status}'")
    print(f"[DEBUG][SHEET] info_dest: {info_dest}")
    if not sheet_status:
        print("[DEBUG][SHEET] sheet_status vazio, retornando sem atualizar")
        return

    creds = utils.build_google_credentials_from_session()
    from googleapiclient.discovery import build
    sheets_service = build('sheets', 'v4', credentials=creds)

    def _sanitizar_cliente(valor: str) -> str:
        texto = (valor or "").strip()
        if not texto:
            return ""
        if texto.casefold() in {"cliente não informado", "cliente nao informado"}:
            return ""
        return texto

    cliente_sheet = _sanitizar_cliente(cliente_sheet)
    chave_busca = cliente_sheet
    fonte_chave = "payload"

    if not chave_busca and project_row is not None:
        try:
            candidato = project_row["cliente"] if isinstance(project_row, sqlite3.Row) else project_row.get("cliente")
        except Exception:
            candidato = None
        chave_busca = _sanitizar_cliente(candidato)
        if chave_busca:
            fonte_chave = "db"

    if not chave_busca:
        chave_busca = _sanitizar_cliente(utils.extrair_cliente_planilha((detalhes_zoho or {}).get("name", "")))
        if chave_busca:
            fonte_chave = "zoho:name"

    if not chave_busca:
        chave_busca = _sanitizar_cliente(utils.extrair_cliente_planilha((detalhes_zoho or {}).get("project_name", "")))
        if chave_busca:
            fonte_chave = "zoho:project_name"

    if not chave_busca:
        chave_busca = _sanitizar_cliente(utils.extrair_cliente_planilha((detalhes_zoho or {}).get("project", {}).get("name", "")))
        if chave_busca:
            fonte_chave = "zoho:project.name"

    if not chave_busca:
        raise ValueError("Cliente não localizado para atualização da planilha")

    try:
        print(f"[DEBUG][SHEET] Cliente para planilha: '{chave_busca}' (fonte: {fonte_chave})")
    except Exception:
        pass

    status_col_candidatos = [
        "Status",
        "Status Principal",
        "STATUS",
        "STATUS PRINCIPAL"
    ]
    coluna_utilizada = None
    ultimo_erro_coluna = None
    for nome_coluna in status_col_candidatos:
        try:
            utils.update_col_value_by_cliente_tolerant(
                sheets_service,
                chave_busca,
                nome_coluna,
                sheet_status
            )
            coluna_utilizada = nome_coluna
            break
        except RuntimeError as exc:
            if "não encontrada no cabeçalho" in str(exc):
                ultimo_erro_coluna = exc
                continue
            raise

    if not coluna_utilizada:
        raise RuntimeError(
            "Nenhuma coluna de status conhecida encontrada na planilha principal. "
            f"Tentativas: {', '.join(status_col_candidatos)}. Erro original: {ultimo_erro_coluna}"
        )

    mensagem = (
        f"Planilha atualizada na coluna '{coluna_utilizada}' para '{sheet_status}'."
    )
    coletor_mensagens.append(mensagem)
    _log_move_info("[MOVE][SHEET]", projeto_id, coluna_destino, mensagem)

    # Atualizações específicas por transição após descobrir o cliente correto
    if coluna_origem == "Falta Liberar Servidor Infra" and coluna_destino == "Em Andamento":
        hoje_ddmmyyyy = datetime.now().strftime('%d/%m/%Y')
        print(f"[DEBUG][SHEET] Atualizando Lib.Servidor para cliente '{chave_busca}' com data '{hoje_ddmmyyyy}'")
        try:
            utils.update_col_value_by_cliente_tolerant(sheets_service, chave_busca, "Lib.Servidor", hoje_ddmmyyyy)
            coletor_mensagens.append('Planilha principal: Coluna "Lib.Servidor" atualizada.')
            print(f"[DEBUG][SHEET] Lib.Servidor atualizada com sucesso")
        except Exception as e:
            print(f"[DEBUG][SHEET] Erro ao atualizar Lib.Servidor: {e}")
            coletor_mensagens.append(f'Falha ao atualizar a coluna "Lib.Servidor": {e}')
        
        # Buscar e atualizar campo VPN
        try:
            print(f"[DEBUG][SHEET] Buscando informações VPN para cliente '{chave_busca}'")
            
            # Buscar ID da pasta do cliente no banco de dados (coluna link_google)
            pasta_cliente_id = None
            
            # Primeiro, tentar obter o link do Google Drive do banco de dados
            link_google = None
            if project_row:
                try:
                    if isinstance(project_row, sqlite3.Row):
                        link_google = project_row.get('link_google')
                    elif isinstance(project_row, dict):
                        link_google = project_row.get('link_google')
                except Exception:
                    link_google = None
            
            # Se não encontrou no project_row, buscar diretamente no banco
            if not link_google:
                try:
                    conn = database.get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT link_google FROM projects WHERE id = ?", (projeto_id,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        link_google = row[0]
                    conn.close()
                except Exception as e:
                    print(f"[DEBUG][SHEET] Erro ao buscar link_google no banco: {e}")
                    
            if link_google:
                # Extrair ID da pasta do link do Google Drive
                import re
                match = re.search(r'https://drive\.google\.com/drive/folders/([a-zA-Z0-9_-]+)', link_google)
                if match:
                    pasta_cliente_id = match.group(1)
                    print(f"[DEBUG][SHEET] ID da pasta do cliente encontrado no banco: {pasta_cliente_id}")
                else:
                    print(f"[DEBUG][SHEET] Link Google Drive inválido no banco: {link_google}")
            else:
                print(f"[DEBUG][SHEET] Link Google Drive não encontrado no banco para projeto {projeto_id}")
            
            if pasta_cliente_id:
                from googleapiclient.discovery import build
                drive_service = build('drive', 'v3', credentials=utils.build_google_credentials_from_session())
                
                # Buscar IPv6 na pasta Infraestrutura
                ipv6_vpn = utils.buscar_ipv6_por_pasta(drive_service, pasta_cliente_id)
                
                if ipv6_vpn:
                    print(f"[DEBUG][SHEET] IPv6 VPN encontrado: {ipv6_vpn}")
                    # Atualizar coluna VPN na planilha
                    utils.update_col_value_by_cliente_tolerant(sheets_service, chave_busca, "VPN", ipv6_vpn)
                    coletor_mensagens.append(f'Planilha principal: Coluna "VPN" atualizada com {ipv6_vpn}.')
                    print(f"[DEBUG][SHEET] Coluna VPN atualizada com sucesso")
                else:
                    print(f"[DEBUG][SHEET] IPv6 VPN não encontrado na pasta Infraestrutura")
                    coletor_mensagens.append('Aviso: IPv6 VPN não encontrado na pasta Infraestrutura.')
            else:
                print(f"[DEBUG][SHEET] ID da pasta do cliente não encontrado nos detalhes do projeto")
                coletor_mensagens.append('Aviso: Pasta do cliente no Drive não encontrada para buscar VPN.')
                
        except Exception as e:
            print(f"[DEBUG][SHEET] Erro ao buscar/atualizar VPN: {e}")
            coletor_mensagens.append(f'Falha ao atualizar a coluna "VPN": {e}')


def _sincronizar_db_local(
    projeto_id: str,
    access_token: str,
    coletor_mensagens: list
) -> None:
    """Sincroniza o projeto movido com o banco de dados local."""
    resultado = synchronize_single_project(projeto_id, access_token)
    if not resultado:
        raise RuntimeError("Sincronização do projeto não retornou dados.")

    mensagem = "Cache local sincronizado com sucesso."
    coletor_mensagens.append(mensagem)
    _log_move_info("[MOVE][DB]", projeto_id, "<sync>", mensagem)


@api_bp.route('/iniciar_implantacao', methods=['POST'])
def iniciar_implantacao():
    try:
        if 'credentials' not in session:
            return jsonify({"sucesso": False, "erro": "Não autenticado."}), 401

        data = request.get_json(silent=True) or {}
        project_id = str(data.get('project_id') or '').strip()
        data_inicio_implantacao = (data.get('data_inicio_implantacao') or '').strip()  # esperado yyyy-mm-dd
        implantador_ris = (data.get('implantador_ris') or '').strip()
        implantador_pacs = (data.get('implantador_pacs') or '').strip()

        if not project_id or not data_inicio_implantacao:
            return jsonify({"sucesso": False, "erro": "Parâmetros inválidos."}), 400

        project_row = database.get_project_by_id(project_id)
        if not project_row:
            return jsonify({"sucesso": False, "erro": f"Projeto {project_id} não encontrado no cache."}), 404
        detalhes_zoho = json.loads(project_row['full_data_json'])

        # ==== 1. PRIMEIRO: Mover para coluna "Em Andamento - Implantação" usando o sistema de mapeamento ====
        print(f"[DEBUG][INICIAR_IMPLANTACAO] Movendo projeto {project_id} para 'Em Andamento - Implantação'")
        
        try:
            access_token = utils.obter_access_token()
            print(f"[DEBUG][INICIAR_IMPLANTACAO] Access token obtido com sucesso")
            
            # Carregar configuração da coluna "Em Andamento - Implantação"
            from utils import carregar_mapeamento_colunas
            mapeamento = carregar_mapeamento_colunas()
            info_dest = mapeamento.get("Em Andamento - Implantação", {})
            
            if not info_dest:
                erro_msg = "Configuração para 'Em Andamento - Implantação' não encontrada no mapeamento"
                print(f"[ERROR][INICIAR_IMPLANTACAO] {erro_msg}")
                return jsonify({"sucesso": False, "erro": erro_msg}), 500
            
            print(f"[DEBUG][INICIAR_IMPLANTACAO] Configuração encontrada: {info_dest}")
            
            # Atualizar o campo data_de_inicio_da_implantacao na configuração
            custom_fields_config = info_dest.get("zohoCustomFields", {}).copy()
            custom_fields_config["data_de_inicio_da_implantacao"] = data_inicio_implantacao
            info_dest_modificada = info_dest.copy()
            info_dest_modificada["zohoCustomFields"] = custom_fields_config
            
            print(f"[DEBUG][INICIAR_IMPLANTACAO] Configuração modificada com data: {info_dest_modificada}")
            
            # Usar o sistema de mapeamento existente para aplicar as mudanças
            mensagens_zoho = []
            try:
                _atualizar_zoho(
                    projeto_id=project_id,
                    coluna_destino="Em Andamento - Implantação", 
                    info_dest=info_dest_modificada,
                    access_token=access_token,
                    detalhes_zoho=detalhes_zoho,
                    coletor_mensagens=mensagens_zoho,
                    coluna_origem="Em Andamento"  # Assumindo que vem de "Em Andamento"
                )
                print(f"[DEBUG][INICIAR_IMPLANTACAO] Zoho atualizado com sucesso. Mensagens: {mensagens_zoho}")
            except Exception as zoho_error:
                # Se falhar completamente, tenta uma abordagem mais simples
                print(f"[WARN][INICIAR_IMPLANTACAO] Erro na atualização completa: {zoho_error}")
                print(f"[DEBUG][INICIAR_IMPLANTACAO] Tentando atualização simplificada...")
                
                # Tenta apenas atualizar o campo customizado sem mexer nas tags
                try:
                    headers = {
                        "Authorization": f"Zoho-oauthtoken {access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
                    base_url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
                    
                    # Apenas atualizar o campo customizado
                    payload_custom = {"custom_fields": {"data_de_inicio_da_implantacao": data_inicio_implantacao}}
                    response_custom = requests.patch(base_url, headers=headers, json=payload_custom, timeout=45)
                    
                    if response_custom.status_code in (200, 201):
                        print(f"[DEBUG][INICIAR_IMPLANTACAO] Campo customizado atualizado com sucesso (fallback)")
                        mensagens_zoho.append("Campo customizado atualizado (modo compatibilidade)")
                        
                        # Tentar adicionar tag separadamente
                        try:
                            # Obter tags atuais
                            response_get = requests.get(base_url, headers=headers, timeout=30)
                            if response_get.status_code == 200:
                                project_data = response_get.json().get('project', {})
                                tags_atuais = project_data.get('tags', [])
                                
                                # Verificar se já tem a tag
                                tag_implantacao_id = "2376502000000188201"
                                ja_tem_tag = any(str(tag.get('id', '')) == tag_implantacao_id for tag in tags_atuais)
                                
                                if not ja_tem_tag:
                                    tags_atuais.append({"id": tag_implantacao_id})
                                    payload_tags = {"tags": tags_atuais}
                                    response_tags = requests.patch(base_url, headers=headers, json=payload_tags, timeout=45)
                                    
                                    if response_tags.status_code in (200, 201):
                                        print(f"[DEBUG][INICIAR_IMPLANTACAO] Tag de implantação adicionada (fallback)")
                                        mensagens_zoho.append("Tag de implantação adicionada")
                                    else:
                                        print(f"[WARN][INICIAR_IMPLANTACAO] Falha ao adicionar tag: {response_tags.status_code}")
                                        mensagens_zoho.append("Aviso: Tag não pôde ser adicionada automaticamente")
                                else:
                                    print(f"[DEBUG][INICIAR_IMPLANTACAO] Tag de implantação já existe")
                                    mensagens_zoho.append("Tag de implantação já presente")
                        except Exception as tag_error:
                            print(f"[WARN][INICIAR_IMPLANTACAO] Erro ao processar tags: {tag_error}")
                            mensagens_zoho.append("Aviso: Erro ao processar tags")
                    else:
                        print(f"[ERROR][INICIAR_IMPLANTACAO] Falha no fallback: {response_custom.status_code} - {response_custom.text}")
                        raise zoho_error  # Re-raise o erro original
                        
                except Exception as fallback_error:
                    print(f"[ERROR][INICIAR_IMPLANTACAO] Falha no fallback: {fallback_error}")
                    raise zoho_error  # Re-raise o erro original

        except Exception as e:
            erro_msg = f"Falha ao atualizar Zoho Projects: {str(e)}"
            print(f"[ERROR][INICIAR_IMPLANTACAO] {erro_msg}")
            traceback.print_exc()
            return jsonify({"sucesso": False, "erro": erro_msg}), 500

        # ==== 2. SEGUNDO: Atualizar PLANILHA PRINCIPAL ====
        print(f"[DEBUG][INICIAR_IMPLANTACAO] Iniciando atualização da planilha...")
        
        creds = utils.build_google_credentials_from_session()
        sheets_service = build('sheets', 'v4', credentials=creds)

        proj_name = str((detalhes_zoho or {}).get('name', '') or '')
        base_cliente = proj_name.split(' - NR')[0].split(' - AP')[0].split(' - NR/AP')[0].strip()
        chave_busca = base_cliente

        if not chave_busca:
            return jsonify({"sucesso": False, "erro": "Não foi possível identificar o cliente do projeto."}), 400

        def _fmt_ddmmyyyy(s: str) -> str:
            try:
                y, m, d = s.split('-')
                return f"{d.zfill(2)}/{m.zfill(2)}/{y}"
            except Exception:
                return s

        def _primeiro_nome(nome: str) -> str:
            nome = (nome or '').strip()
            if not nome:
                return ''
            partes = nome.split()
            return partes[0]

        implant_responsavel = ''
        pacs_first = _primeiro_nome(implantador_pacs)
        ris_first = _primeiro_nome(implantador_ris)
        if pacs_first:
            implant_responsavel = f"Pacs - {pacs_first}"
            if ris_first:
                implant_responsavel += f" + Ris - {ris_first}"

        print(f"[DEBUG][INICIAR_IMPLANTACAO] Cliente identificado: '{chave_busca}'")
        print(f"[DEBUG][INICIAR_IMPLANTACAO] Implantador responsável: '{implant_responsavel}'")
        print(f"[DEBUG][INICIAR_IMPLANTACAO] Data para planilha: '{_fmt_ddmmyyyy(data_inicio_implantacao)}'")

        try:
            print(f"[DEBUG][INICIAR_IMPLANTACAO] Atualizando coluna 'Dt Inicio Implantação'...")
            utils.update_col_value_by_cliente_tolerant(
                sheets_service,
                chave_busca,
                'Dt Inicio Implantação',
                _fmt_ddmmyyyy(data_inicio_implantacao)
            )
            print(f"[DEBUG][INICIAR_IMPLANTACAO] Coluna 'Dt Inicio Implantação' atualizada com sucesso")
        except Exception as e:
            erro_msg = f"Falha ao atualizar data na planilha: {e}"
            print(f"[ERROR][INICIAR_IMPLANTACAO] {erro_msg}")
            return jsonify({"sucesso": False, "erro": erro_msg}), 500

        detalhes_msg = []
        if implant_responsavel:
            try:
                print(f"[DEBUG][INICIAR_IMPLANTACAO] Atualizando coluna 'Implant Responsável'...")
                utils.update_col_value_by_cliente_tolerant(
                    sheets_service,
                    chave_busca,
                    'Implant Responsável',
                    implant_responsavel
                )
                detalhes_msg.append("Implant Responsável atualizado.")
                print(f"[DEBUG][INICIAR_IMPLANTACAO] Coluna 'Implant Responsável' atualizada com sucesso")
            except Exception as e:
                erro_msg = f"Falha ao atualizar implantador na planilha: {e}"
                print(f"[ERROR][INICIAR_IMPLANTACAO] {erro_msg}")
                return jsonify({"sucesso": False, "erro": erro_msg}), 500
        else:
            detalhes_msg.append("Implant Responsável não atualizado (selecione PACS).")
            print(f"[DEBUG][INICIAR_IMPLANTACAO] Implant Responsável não atualizado - nenhum PACS selecionado")

        # ==== 3. TERCEIRO: Sincronizar banco local FORÇADAMENTE ====
        print(f"[DEBUG][INICIAR_IMPLANTACAO] Iniciando sincronização forçada do banco local...")
        try:
            # Forçar sincronização múltipla para garantir que as mudanças sejam capturadas
            _sincronizar_db_local_forcado(project_id, access_token, detalhes_msg)
        except Exception as e:
            # Log do erro mas não falha a operação
            print(f"[WARN] Falha na sincronização do banco local: {e}")
            detalhes_msg.append("Aviso: Falha na sincronização do cache local")

        return jsonify({
            "sucesso": True, 
            "mensagem": "Implantação iniciada com sucesso! Zoho Projects e planilha atualizados.", 
            "detalhes": detalhes_msg
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"sucesso": False, "erro": str(e)}), 500


def _sincronizar_db_local_forcado(projeto_id: str, access_token: str, coletor_mensagens: list) -> None:
    """
    Sincroniza o projeto com múltiplas tentativas para garantir que as mudanças sejam capturadas.
    Especialmente útil após alterações de tags que podem demorar para se propagar na API do Zoho.
    """
    import time
    from sync_zoho import synchronize_single_project
    
    max_tentativas = 3
    intervalo_tentativas = 2  # segundos
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            print(f"[DEBUG][SYNC] Tentativa {tentativa}/{max_tentativas} de sincronização do projeto {projeto_id}")
            
            # Pequena pausa para permitir que a API do Zoho propague as mudanças
            if tentativa > 1:
                time.sleep(intervalo_tentativas)
            
            # Sincroniza o projeto específico
            project_updated = synchronize_single_project(projeto_id, access_token)
            
            if project_updated:
                # Verificar se as mudanças foram capturadas
                import database
                project_row = database.get_project_by_id(projeto_id)
                
                if project_row:
                    import json
                    detalhes_zoho = json.loads(project_row['full_data_json'])
                    
                    # Verificar se tem a tag de implantação
                    tags = detalhes_zoho.get('tags', [])
                    tag_implantacao_presente = any(str(tag.get('id', '')) == "2376502000000188201" for tag in tags)
                    
                    # Verificar se tem o campo customizado
                    campo_data_presente = detalhes_zoho.get('data_de_inicio_da_implantacao') is not None
                    
                    print(f"[DEBUG][SYNC] Tag implantação presente: {tag_implantacao_presente}")
                    print(f"[DEBUG][SYNC] Campo data presente: {campo_data_presente}")
                    
                    if tag_implantacao_presente or tentativa == max_tentativas:
                        coletor_mensagens.append(f"Banco local sincronizado (tentativa {tentativa})")
                        _log_move_info("[MOVE][DB]", projeto_id, "Em Andamento - Implantação", f"Sincronização concluída na tentativa {tentativa}")
                        return
                    else:
                        print(f"[DEBUG][SYNC] Mudanças ainda não propagadas, tentando novamente...")
                else:
                    print(f"[WARN][SYNC] Projeto não encontrado no banco local após sincronização")
            else:
                print(f"[WARN][SYNC] Falha na sincronização, tentativa {tentativa}")
                
        except Exception as exc:
            error_msg = f"Erro na sincronização (tentativa {tentativa}): {exc}"
            print(f"[ERROR][SYNC] {error_msg}")
            
            if tentativa == max_tentativas:
                coletor_mensagens.append(f"Aviso: Falha na sincronização após {max_tentativas} tentativas")
                _log_move_error("[MOVE][DB]", projeto_id, "Em Andamento - Implantação", error_msg)
                raise


def _sincronizar_db_local(projeto_id: str, access_token: str, coletor_mensagens: list) -> None:
    """
    Sincroniza o projeto específico com o banco local após movimentação.
    Atualiza campos como dias_na_fase e data_ultima_mudanca.
    """
    try:
        from sync_zoho import synchronize_single_project
        
        # Sincroniza o projeto específico
        project_updated = synchronize_single_project(projeto_id, access_token)
        
        if project_updated:
            coletor_mensagens.append("Banco local sincronizado com sucesso")
            _log_move_info("[MOVE][DB]", projeto_id, "", "Sincronização do banco local concluída")
        else:
            coletor_mensagens.append("Aviso: Projeto não encontrado durante sincronização")
            _log_move_info("[MOVE][DB]", projeto_id, "", "Projeto não encontrado durante sincronização")
            
    except Exception as exc:
        error_msg = f"Erro na sincronização do banco local: {exc}"
        coletor_mensagens.append(error_msg)
        _log_move_error("[MOVE][DB]", projeto_id, "", error_msg)
        raise





@api_bp.route('/mover_projeto', methods=['POST'])
def mover_projeto():
    """Move projeto entre colunas do Kanban, atualizando status/tag no Zoho e sincronizando DB local."""
    if 'credentials' not in session:
        return jsonify({"sucesso": False, "mensagem": "Usuário não autenticado."}), 401

    try:
        data = request.get_json(silent=True) or {}
        projeto_id = data.get('projeto_id')
        coluna_origem = data.get('coluna_origem')
        coluna_destino = data.get('coluna_destino')
        cliente_sheet = data.get('cliente_sheet')

        # Obter access token
        access_token = utils.obter_access_token()
        if not access_token:
            print("[ERROR] Não foi possível obter o access token")
            return jsonify({"sucesso": False, "mensagem": "Erro de autenticação"}), 401

        # Mapeamento de colunas para tags/status IDs
        mapeamento_colunas = {
            "Aguardando Onboarding": {"tag_id": TAG_AGUARDANDO_ONBOARDING_ID},
            "Falta Liberar Servidor Infra": {"tag_id": TAG_AGUARDANDO_INFRA_ID},
            "Em Andamento": {"status_id": STATUS_EM_ANDAMENTO_ID},
            "Em Homologação": {"tag_id": TAG_EM_HOMOLOGACAO_ID},
            "Em Virada": {"tag_id": TAG_EM_VIRADA_ID},
            "Em Operação Assistida": {"status_id": STATUS_OPERACAO_ASSISTIDA_ID},
            "Aguardando Encerramento": {"status_id": STATUS_AGUARDANDO_CLIENTE_ID},
            "Finalizado": {"status_id": STATUS_FINALIZADO_ID},
            "Projeto Parado": {"tag_id": TAG_PARADO_ID},
            "Cancelado": {"status_id": STATUS_CANCELADO_ID}
        }
        
        print(f"[DEBUG] Movendo projeto {projeto_id} de '{coluna_origem}' para '{coluna_destino}'")

        config_destino = mapeamento_colunas.get(coluna_destino)
        if not config_destino:
            return jsonify({"sucesso": False, "mensagem": f"Coluna destino '{coluna_destino}' não reconhecida."}), 400

        config_origem = mapeamento_colunas.get(coluna_origem) if coluna_origem else None

        mensagens = []

        # Remover tags antigas e atualizar status
        try:
            headers = {
                "Authorization": f"Zoho-oauthtoken {access_token}",
                "Content-Type": "application/json"
            }
            
            # 1. Se movendo para Em Andamento, remover TODAS as tags primeiro
            if coluna_destino == "Em Andamento":
                print(f"[DEBUG] Obtendo tags atuais do projeto {projeto_id}")
                tags_resp = requests.get(tags_url, headers=headers, timeout=30)
                if tags_resp.status_code == 200:
                    tags = tags_resp.json().get('tags', [])
                    print(f"[DEBUG] Tags encontradas: {tags}")
                    for tag in tags:
                        tag_id = tag.get('id')
                        if tag_id:
                            print(f"[DEBUG] Removendo tag {tag_id}")
                            del_resp = requests.delete(del_url, headers=headers, timeout=30)
                            print(f"[DEBUG] Resposta remoção tag {tag_id}: {del_resp.status_code}")
                            if del_resp.status_code in (200, 204):
                                mensagens.append(f"Tag {tag.get('name', tag_id)} removida do Zoho")
                            else:
                                mensagens.append(f"Aviso: Falha ao remover tag {tag.get('name', tag_id)} ({del_resp.status_code})")
                else:
                    print(f"[WARNING] Falha ao obter tags: {tags_resp.status_code}")

            # 2. Atualizar status do projeto
            print(f"[DEBUG] Atualizando status do projeto para {coluna_destino}")
            status_payload = {
                "status": {"id": STATUS_EM_ANDAMENTO_ID}
            }
            status_resp = requests.patch(status_url, headers=headers, json=status_payload, timeout=30)
            print(f"[DEBUG] Resposta atualização status: {status_resp.status_code}")
            if status_resp.status_code in (200, 201):
                mensagens.append("Status atualizado para Em Andamento no Zoho")
            else:
                print(f"[ERROR] Falha ao atualizar status: {status_resp.text}")
                mensagens.append(f"Aviso: Falha ao atualizar status ({status_resp.status_code})")

        except Exception as e:
            print(f"[ERROR] Erro ao manipular projeto no Zoho: {str(e)}")
            traceback.print_exc()
            mensagens.append(f"Erro ao manipular projeto no Zoho: {str(e)}")

        # Atualizar status/tag no Zoho
        if 'status_id' in config_destino:
            status_id = config_destino['status_id']
            # PATCH project status
            headers = {
                "Authorization": f"Zoho-oauthtoken {access_token}",
                "Content-Type": "application/json"
            }
            payload = {"status": {"id": status_id}}
            resp = requests.put(url, headers=headers, json=payload, timeout=30)
            if resp.status_code not in (200, 201):
                mensagens.append(f"Aviso: Falha ao atualizar status ({resp.status_code})")
            else:
                mensagens.append("Status atualizado no Zoho")

        if 'tag_id' in config_destino:
            tag_id = config_destino['tag_id']
            # Adicionar tag ao projeto
            headers = {
                "Authorization": f"Zoho-oauthtoken {access_token}",
                "Content-Type": "application/json"
            }
            resp = requests.post(url, headers=headers, timeout=30)
            if resp.status_code not in (200, 201):
                mensagens.append(f"Aviso: Falha ao adicionar tag ({resp.status_code})")
            else:
                mensagens.append("Tag adicionada no Zoho")

        # Sincronizar projeto específico
        _sincronizar_db_local(projeto_id, access_token, mensagens)

        # Obter data da última mudança do feed de atividades
        data_ultima_mudanca = _obter_data_ultima_mudanca(projeto_id, access_token)

        if data_ultima_mudanca:
            # Atualizar no banco de dados
            conn = database.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE projects SET data_ultima_mudanca = ? WHERE id = ?",
                    (data_ultima_mudanca, projeto_id)
                )
                conn.commit()
                mensagens.append(f"Data última mudança atualizada: {data_ultima_mudanca}")
            except Exception as e:
                mensagens.append(f"Aviso: Falha ao atualizar data_ultima_mudanca: {e}")
            finally:
                conn.close()
        else:
            mensagens.append("Aviso: Não foi possível obter data da última mudança")

        # Ações especiais para transição de Falta Liberar Servidor Infra para Em Andamento
        print(f"[DEBUG] Verificando transição especial: origem={coluna_origem}, destino={coluna_destino}")
        if coluna_origem == "Falta Liberar Servidor Infra" and coluna_destino == "Em Andamento":
            print("[DEBUG] Executando ações especiais para liberação de servidor")
            from datetime import date, datetime
            data_atual = date.today().strftime('%Y-%m-%d')
            data_atual_ddmmyyyy = datetime.now().strftime('%d/%m/%Y')

            # 1. Atualizar campo customizado no Zoho
            try:
                print("[DEBUG] Iniciando atualização do campo Data Liberação Servidor")
                
                # Usar o label identificado: UDF_DATE4
                target_label = "UDF_DATE4"

                utils.atualizar_custom_field_projeto(access_token, projeto_id, target_label, data_atual)
                mensagens.append(f"Campo customizado '{target_label}' atualizado no Zoho")
                    
            except Exception as e:
                print(f"[ERROR] Erro ao atualizar campo customizado: {str(e)}")
                traceback.print_exc()
                mensagens.append(f"Aviso: Falha ao atualizar campo customizado: {e}")

            # 2. Atualizar planilha principal (Status Principal e Lib.Servidor)
            if cliente_sheet:
                try:
                    print(f"[DEBUG] Atualizando planilha principal para cliente: {cliente_sheet}")
                    sheets_service = build('sheets', 'v4', credentials=utils.build_google_credentials_from_session())
                    
                    # Buscar cabeçalhos
                    range_cab = f"'{NOME_ABA_PLANILHA}'!A{LINHA_CABECALHO}:ZZ{LINHA_CABECALHO}"
                    print(f"[DEBUG] Buscando cabeçalhos: {range_cab}")
                    result = sheets_service.spreadsheets().values().get(
                        spreadsheetId=ID_PLANILHA_PROJETOS,
                        range=range_cab
                    ).execute()
                    cabecalhos = result.get('values', [[]])[0]
                    print(f"[DEBUG] Cabeçalhos encontrados: {cabecalhos}")
                    
                    lower_map = {str(c).strip().lower(): i for i, c in enumerate(cabecalhos)}

                    # Encontrar índices das colunas
                    col_cliente_idx = lower_map.get('cliente')
                    col_libservidor_idx = lower_map.get('lib.servidor') or lower_map.get('lib servidor')
                    col_status_idx = None
                    for nm in ['status principal', 'status', 'status_principal', 'statusprincipal']:
                        if nm in lower_map:
                            col_status_idx = lower_map[nm]
                            break
                    
                    print(f"[DEBUG] Índices encontrados - Cliente: {col_cliente_idx}, Lib.Servidor: {col_libservidor_idx}, Status: {col_status_idx}")

                    if col_cliente_idx is not None and (col_status_idx is not None or col_libservidor_idx is not None):
                        letra_col_cliente = utils.indice_para_letra_coluna(col_cliente_idx)
                        start_row = LINHA_CABECALHO + 1
                        range_clientes = f"'{NOME_ABA_PLANILHA}'!{letra_col_cliente}{start_row}:{letra_col_cliente}"
                        
                        print(f"[DEBUG] Buscando clientes no range: {range_clientes}")
                        valores = sheets_service.spreadsheets().values().get(
                            spreadsheetId=ID_PLANILHA_PROJETOS,
                            range=range_clientes
                        ).execute().get('values', [])

                        # Encontrar linha do cliente
                        linha_encontrada = None
                        for idx, row in enumerate(valores):
                            if row and row[0].strip() == cliente_sheet:
                                linha_encontrada = start_row + idx
                                break

                        print(f"[DEBUG] Linha encontrada para cliente {cliente_sheet}: {linha_encontrada}")

                        if linha_encontrada:
                            updates = []
                            if col_status_idx is not None:
                                letra_col_status = utils.indice_para_letra_coluna(col_status_idx)
                                range_status = f"'{NOME_ABA_PLANILHA}'!{letra_col_status}{linha_encontrada}"
                                updates.append({
                                    'range': range_status,
                                    'values': [["Em Andamento"]]
                                })
                                print(f"[DEBUG] Adicionada atualização de status: {range_status} = Em Andamento")
                            
                            if col_libservidor_idx is not None:
                                letra_col_lib = utils.indice_para_letra_coluna(col_libservidor_idx)
                                range_lib = f"'{NOME_ABA_PLANILHA}'!{letra_col_lib}{linha_encontrada}"
                                updates.append({
                                    'range': range_lib,
                                    'values': [[data_atual_ddmmyyyy]]
                                })
                                print(f"[DEBUG] Adicionada atualização de Lib.Servidor: {range_lib} = {data_atual_ddmmyyyy}")

                            if updates:
                                print(f"[DEBUG] Executando batch update com {len(updates)} atualizações")
                                result = sheets_service.spreadsheets().values().batchUpdate(
                                    spreadsheetId=ID_PLANILHA_PROJETOS,
                                    body={'valueInputOption': 'USER_ENTERED', 'data': updates}
                                ).execute()
                                print(f"[DEBUG] Resultado do batch update: {result}")
                                mensagens.append('Planilha principal: Status Principal e Lib.Servidor atualizados')
                        else:
                            print(f"[WARNING] Cliente {cliente_sheet} não encontrado na planilha")
                            mensagens.append(f"Aviso: Cliente {cliente_sheet} não encontrado na planilha")
                    else:
                        print(f"[WARNING] Colunas necessárias não encontradas")
                        mensagens.append("Aviso: Colunas necessárias não encontradas na planilha")
                except Exception as e:
                    print(f"[ERROR] Erro ao atualizar planilha: {str(e)}")
                    traceback.print_exc()
                    mensagens.append(f"Aviso: Falha ao atualizar planilha: {e}")

            # 3. Atualizar banco de dados
            try:
                conn = database.get_db_connection()
                cursor = conn.cursor()
                
                # Atualizar data_liberacao_servidor
                cursor.execute(
                    "UPDATE projects SET data_liberacao_servidor = ? WHERE id = ?",
                    (data_atual, projeto_id)
                )
                
                # Atualizar data_ultima_mudanca
                cursor.execute(
                    "UPDATE projects SET data_ultima_mudanca = ? WHERE id = ?",
                    (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), projeto_id)
                )
                
                conn.commit()
                print(f"[DEBUG] Banco de dados atualizado para projeto {projeto_id}")
                mensagens.append("Banco de dados: campos data_liberacao_servidor e data_ultima_mudanca atualizados")
            except Exception as e:
                print(f"[ERROR] Erro ao atualizar banco de dados: {str(e)}")
                mensagens.append(f"Erro ao atualizar banco de dados: {str(e)}")
            finally:
                conn.close()

            # Sincronizar novamente o banco após atualização do campo customizado
            _sincronizar_db_local(projeto_id, access_token, mensagens)

            # Atualizar data_ultima_mudanca após a mudança
            data_ultima_mudanca = _obter_data_ultima_mudanca(projeto_id, access_token)
            if data_ultima_mudanca:
                conn = database.get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE projects SET data_ultima_mudanca = ? WHERE id = ?",
                    (data_ultima_mudanca, projeto_id)
                )
                conn.commit()
                conn.close()
                mensagens.append(f"Data última mudança atualizada após campo customizado: {data_ultima_mudanca}")
            else:
                mensagens.append("Aviso: Não foi possível obter data da última mudança após atualização")

            # Atualizar planilha
            if cliente_sheet:
                try:
                    creds = utils.build_google_credentials_from_session()
                    sheets_service = build('sheets', 'v4', credentials=creds)
                    # Atualizar Status Principal
                    utils.atualizar_status_principal_planilha_por_cliente(sheets_service, cliente_sheet, "Em Andamento")
                    mensagens.append("Status Principal atualizado na planilha")
                    # Atualizar Lib.Servidor
                    utils.atualizar_coluna_planilha_por_cliente(sheets_service, cliente_sheet, "Lib.Servidor", data_atual)
                    mensagens.append("Coluna Lib.Servidor atualizada na planilha")
                except Exception as e:
                    mensagens.append(f"Aviso: Falha ao atualizar planilha: {e}")

        return jsonify({"sucesso": True, "mensagem": "Projeto movido com sucesso.", "detalhes": mensagens})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"sucesso": False, "erro": str(e)}), 500


def _obter_data_ultima_mudanca(projeto_id: str, access_token: str) -> str | None:
    """Obtém a data da última atividade do projeto via feed de atividades."""
    try:
        # Tentar V3 primeiro
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }
        params = {"sort_column": "activity_time", "sort_order": "descending", "per_page": 1}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            activities = data.get('activities', [])
            if activities:
                latest_activity = activities[0]
                activity_time = latest_activity.get('activity_time')
                if activity_time:
                    return activity_time

        # Se V3 falhar, tentar restapi
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            activities = data.get('activities', [])
            if activities:
                latest_activity = activities[0]
                activity_time = latest_activity.get('activity_time')
                if activity_time:
                    return activity_time

        return None
    except Exception as e:
        print(f"Erro ao obter atividades: {e}")
        return None

