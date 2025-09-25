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
)
import traceback
import os
from werkzeug.utils import secure_filename
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, date
import json
import re
import requests

# Imports para o cache de banco de dados e sincronização
import database
from sync_zoho import synchronize_projects
# Coletor robusto de tarefas (paginação e status)
from buscar_tarefas import listar_tarefas_do_projeto

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
                novo_projeto = {
                    "id": str(id_do_novo_projeto),
                    "nome": utils.construir_titulo_projeto(dados),
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
            "Em Homologação", "Em Virada", "Em Operação Assistida",
            "Aguardando Encerramento", "Projeto Parado", "Finalizado",
            "Cancelado", "Status Desconhecido"
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
    try:
        if 'credentials' not in session:
            return jsonify({"sucesso": False, "erro": "Usuário não autenticado."}),

        payload = request.get_json(force=True) or {}
        projeto_id = str(payload.get('projeto_id') or '').strip()
        coluna_origem = (payload.get('coluna_origem') or '').strip()
        coluna_destino = (payload.get('coluna_destino') or '').strip()
        cliente_sheet = (payload.get('cliente_sheet') or '').strip()

        if not projeto_id or not coluna_destino:
            return jsonify({"sucesso": False, "erro": "Parâmetros inválidos."}), 400

        msg_operacoes = []
        
        project_row = database.get_project_by_id(projeto_id)
        if not project_row:
            return jsonify({"sucesso": False, "erro": f"Projeto {projeto_id} não encontrado no cache."}), 404
        detalhes_zoho = json.loads(project_row['full_data_json'])

        # Valida refresh_token antes de usar Google Sheets
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
            access_token = utils.obter_access_token_zoho()
            sheets_service = build('sheets', 'v4', credentials=utils.build_google_credentials_from_session())

            # 2) Descobrir valor do cliente ("codigo - nome") a partir do nome do projeto no Zoho
            nome_projeto_zoho = (detalhes_zoho or {}).get('name', '')
            valor_cliente = nome_projeto_zoho.split(' - NR')[0].split(' - AP')[0].split(' - NR/AP')[0].strip()
            description = (detalhes_zoho or {}).get('description', '')
            match = re.search(r'/folders/([a-zA-Z0-9_-]+)', description)
            google_drive_folder_id = match.group(1) if match else None

            # 3) Atualizar planilha: Status Principal por valor exato da coluna "Cliente"
            try:
                novo_status_sheet = info_dest.get('sheetStatus')
                _cli_raw = (cliente_sheet or '').strip()
                if _cli_raw.lower().startswith('cliente não informado') or _cli_raw.lower() in {'', 'n/a', 'na', 'null', 'none'}:
                    cliente_lookup = (valor_cliente or '').strip()
                else:
                    cliente_lookup = _cli_raw
                
                codigo_lookup = None
                try:
                    parte = (cliente_lookup or valor_cliente or '').split(' - ')[0].strip()
                    m = re.match(r'^\d+', parte.replace('.', ''))
                    if m:
                        codigo_lookup = m.group(0)
                except Exception:
                    codigo_lookup = None

                if sheets_service and (cliente_lookup or codigo_lookup) and novo_status_sheet:
                    try:
                        utils._update_status_planilha_principal(sheets_service, cliente_lookup or valor_cliente or codigo_lookup, novo_status_sheet)
                        msg_operacoes.append('Planilha principal: Status Principal atualizado')
                    except Exception as e_upd1:
                        try:
                            chave_alt = valor_cliente or cliente_lookup or ''
                            utils._update_status_planilha_principal(sheets_service, chave_alt, novo_status_sheet)
                            msg_operacoes.append('Planilha principal: Status Principal atualizado (fallback)')
                        except Exception as e_upd2:
                            msg_operacoes.append(f'Falha ao atualizar planilha (Status Principal): {e_upd2}')
                else:
                    msg_operacoes.append('Planilha não atualizada (serviço/cliente/status indisponível)')
            except Exception as e:
                msg_operacoes.append(f'Falha ao atualizar planilha: {e}')

            # 4) Atualizar status do projeto no Zoho (se mapeado)
            try:
                zoho_status_id = (info_dest.get('zohoStatusId') or '').strip() if isinstance(info_dest.get('zohoStatusId'), str) else info_dest.get('zohoStatusId')
                if access_token and zoho_status_id:
                    url = f"{utils._zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}"
                    payload = {"status": {"id": zoho_status_id}}
                    r = requests.patch(url, headers=utils._zp_headers(access_token), json=payload, timeout=30)
                    if r.status_code in (200, 201):
                        msg_operacoes.append('Status do projeto atualizado no Zoho')
                    else:
                        msg_operacoes.append(f'Falha ao atualizar status no Zoho: HTTP {r.status_code}')
            except Exception as e:
                msg_operacoes.append(f'Erro ao atualizar status no Zoho: {e}')

        return jsonify({"sucesso": True, "mensagem": "; ".join(msg_operacoes) or 'Movimentação registrada.'})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"sucesso": False, "erro": str(e)}), 500

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

        try:
            utils.update_col_value_by_cliente_tolerant(
                sheets_service,
                chave_busca,
                'Dt Inicio Implantação',
                _fmt_ddmmyyyy(data_inicio_implantacao)
            )
        except Exception as e:
            return jsonify({"sucesso": False, "erro": f"Falha ao atualizar data na planilha: {e}"}), 500

        detalhes_msg = []
        if implant_responsavel:
            try:
                utils.update_col_value_by_cliente_tolerant(
                    sheets_service,
                    chave_busca,
                    'Implant Responsável',
                    implant_responsavel
                )
                detalhes_msg.append("Implant Responsável atualizado.")
            except Exception as e:
                return jsonify({"sucesso": False, "erro": f"Falha ao atualizar implantador na planilha: {e}"}), 500
        else:
            detalhes_msg.append("Implant Responsável não atualizado (selecione PACS).")

        return jsonify({"sucesso": True, "mensagem": "Implantação agendada e planilha atualizada.", "detalhes": detalhes_msg})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"sucesso": False, "erro": str(e)}), 500