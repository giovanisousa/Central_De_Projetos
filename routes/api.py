from flask import Blueprint, request, jsonify, session, current_app
import utils
from config import DONOS_PROJETO, ZOHO_PORTAL_ID, DEFAULT_TASKS_CUSTOM_VIEW_ID, BASE_DIR
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


api_bp = Blueprint('api', __name__)

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
            'integ_worklist','integ_laudos','integ_docs','integ_lab','integ_outros',
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
            template_id = utils.escolher_template_zoho(dados)
            if template_id:
                zoho_access_token = utils.obter_access_token_zoho()
                id_do_novo_projeto = utils.criar_projeto_no_zoho(zoho_access_token, dados, template_id)
                print("INFO: Aguardando sincronização das tarefas (15s)...")
                time.sleep(15)
                gp_zpuid = DONOS_PROJETO[dados['gp_selecionado']]
                utils.processar_tarefas_iniciais(zoho_access_token, id_do_novo_projeto, gp_zpuid)
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
    try:
        data = request.json
        gp_selecionado = data.get('gp')
        if not gp_selecionado or gp_selecionado not in DONOS_PROJETO:
            return jsonify({"erro": "GP inválido"}), 400
        id_do_gp = DONOS_PROJETO[gp_selecionado]
        access_token = utils.obter_access_token()
        if not access_token:
            return jsonify({"erro": "Erro de autenticação"}), 401
        lista_completa_projetos = utils.listar_todos_projetos_ativos(access_token)
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
                # Inicialmente vazio; cliente busca por projeto via endpoint dedicado e cache
                'dias_na_fase': '',
                # Total de dias do projeto: sempre calculado localmente pela data de início ou criação
                'dias_total': utils.calcular_dias_total_projeto(projeto.get('start_date', ''), projeto.get('created_time', '')),
                'status_atual': status_kanban,
                'produto': produto_info
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

@api_bp.route('/impeditivos/<project_id>', methods=['GET'])
def api_impeditivos(project_id):
    try:
        # Usa token Zoho que também define a base dinâmica (_map_projects_base)
        access_token = utils.obter_access_token_zoho()
        if not access_token:
            return jsonify({"erro": "Erro de autenticação"}), 401
        info = utils._buscar_tasklist_impeditivos_info(access_token, project_id)
        if not info or not info.get('id'):
            # Se a lista não existe, considera 0 abertos
            return jsonify({"project_id": project_id, "count": 0, "has_impediments": False, "web_url": None})
        count = utils._contar_tarefas_abertas_na_tasklist(access_token, project_id, info['id'])
        web_url = info.get('web_url') or None
        if not web_url:
            # Construção da URL web a partir do portal
            base_web = utils._portal_web_base(access_token) or utils._projects_web_root()
            if base_web:
                # Se base_web já incluir '/portal/<slug>/', usa direto; caso contrário, anexa portal id
                if not base_web.rstrip('/').endswith('/portal') and '/portal/' in base_web:
                    web_base_final = base_web
                else:
                    web_base_final = base_web.rstrip('/') + f"/{ZOHO_PORTAL_ID}/"
                # Usa a visualização fixa "somente tarefas em aberto" se disponível
                web_url = utils._compose_tasklist_web_url(web_base_final, project_id, info['id'], DEFAULT_TASKS_CUSTOM_VIEW_ID)
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

        # Sempre usar o token Zoho unificado (define a base correta e Authorization)
        access_token = utils.obter_access_token_zoho()
        if not access_token:
            return jsonify({"erro": "Erro de autenticação"}), 401

        # 1) Preferir data da última entrada na coluna (por status ou por etiqueta mapeada)
        valor = None
        if use_coluna:
            d = utils.obter_data_ultima_mudanca_status_para_coluna(project_id, access_token, coluna)
            if not d:
                d = utils.obter_data_ultima_mudanca_etiqueta_para_coluna(project_id, access_token, coluna)
            if d:
                dias = (date.today() - d).days
                valor = "Hoje" if dias == 0 else ("Futuro" if dias < 0 else f"{dias}d")

        # 2) Se não achou para a coluna, usa o histórico genérico de mudanças (status/etiquetas)
        if not valor:
            try:
                info_min = { 'data_inicio': '', 'data_criacao': '' }
                valor = utils.calcular_dias_na_fase(info_min, None, project_id=project_id, access_token=access_token)
            except Exception:
                valor = None

        # 3) Fallback final: dias totais desde início/criação (auditar ocorrência)
        if not valor or valor == 'N/D':
            try:
                proj_url = f"{utils._zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
                rproj = requests.get(proj_url, headers=utils._zp_headers(access_token), params={"fields": "start_date,created_time,name,status"}, timeout=20)
                if rproj.status_code == 200:
                    pdata = rproj.json() or {}
                    node = pdata.get('project') if isinstance(pdata, dict) and isinstance(pdata.get('project'), dict) else (pdata if isinstance(pdata, dict) else {})
                    start_date = (node.get('start_date') or node.get('start_date_string') or '') if isinstance(node, dict) else ''
                    created_time = (node.get('created_time') or node.get('created_time_string') or '') if isinstance(node, dict) else ''
                    proj_name = (node.get('name') or '') if isinstance(node, dict) else ''
                    proj_status = (node.get('status', {}).get('name') or node.get('status') or '') if isinstance(node, dict) else ''
                    info_min = { 'data_inicio': start_date, 'data_criacao': created_time }

                    # Log de auditoria (por que caiu no fallback)
                    try:
                        print(f"[AUDIT][dias-na-fase][fallback] project_id={project_id} coluna='{coluna or ''}' name='{proj_name}' status='{proj_status}' start='{start_date}' created='{created_time}'")
                    except Exception:
                        pass

                    valor = utils.calcular_dias_na_fase(info_min, None)
            except Exception as e:
                try:
                    print(f"[AUDIT][dias-na-fase][fallback-error] project_id={project_id} coluna='{coluna or ''}' erro='{e}'")
                except Exception:
                    pass

        # Atualiza cache (se valor não definido por algum motivo, mantém 'N/D')
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

        print(f"[/api/mover_projeto] payload recebido: {payload}")
        print(f"[/api/mover_projeto] projeto_id={projeto_id}, origem='{coluna_origem}', destino='{coluna_destino}'")

        if not projeto_id or not coluna_destino:
            print("[/api/mover_projeto] Parâmetros inválidos")
            return jsonify({"sucesso": False, "erro": "Parâmetros inválidos."}, 400)

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
                access_token = utils.obter_access_token_zoho()
                print(f"[/api/mover_projeto] Access token Zoho obtido? {'SIM' if access_token else 'NAO'}")
            except Exception as e:
                print(f"[/api/mover_projeto] ERRO ao obter token Zoho: {e}")

            # Google Sheets service
            sheets_service = None
            try:
                creds = utils.build_google_credentials_from_session()
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
                    detalhes_zoho = utils.obter_detalhes_projeto(access_token, projeto_id)
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
                    parte = (cliente_lookup or valor_cliente or '').split(' - ')[0].strip()
                    m = re.match(r'^\d+', parte.replace('.', ''))
                    if m:
                        codigo_lookup = m.group(0)
                except Exception:
                    codigo_lookup = None
                if sheets_service and (cliente_lookup or codigo_lookup) and novo_status_sheet:
                    # Tolerante: tenta por cliente completo ou código
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
                print(f"[/api/mover_projeto] ERRO atualização planilha: {e}")
                msg_operacoes.append(f'Falha ao atualizar planilha: {e}')

            # 4) Atualizar status do projeto no Zoho (se mapeado)
            try:
                zoho_status_id = (info_dest.get('zohoStatusId') or '').strip() if isinstance(info_dest.get('zohoStatusId'), str) else info_dest.get('zohoStatusId')
                if access_token and zoho_status_id:
                    url = f"{utils._zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}"
                    payload = {"status": {"id": zoho_status_id}}
                    print(f"[/api/mover_projeto] Atualizando status do projeto: {payload}")
                    r = requests.patch(url, headers=utils._zp_headers(access_token), json=payload, timeout=30)
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
                # 1) Se tivermos o ID da pasta do Drive na descrição do projeto, tentar extrair IPv6
                try:
                    ipv6_encontrado = None
                    if google_drive_folder_id:
                        try:
                            creds = utils.build_google_credentials_from_session()
                            drive_service = build('drive', 'v3', credentials=creds)
                            ipv6_encontrado = utils.buscar_ipv6_por_pasta(drive_service, google_drive_folder_id)
                            print(f"DEBUG: IPv6 encontrado? {ipv6_encontrado}")
                        except Exception as e_busca:
                            print(f"DEBUG: Falha ao buscar IPv6: {e_busca}")
                    # 2) Atualiza planilha: coluna 'VPN' com o IPv6 (se encontrado)
                    if sheets_service and ipv6_encontrado:
                        try:
                            alvo_cliente = (locals().get('cliente_lookup') or locals().get('codigo_lookup') or valor_cliente or '').strip()
                            if alvo_cliente:
                                utils.update_col_value_by_cliente_tolerant(
                                    sheets_service,
                                    alvo_cliente,
                                    "VPN",
                                    ipv6_encontrado
                                )
                                msg_operacoes.append('Planilha: coluna VPN atualizada com IPv6')
                        except Exception as e_upd_vpn:
                            msg_operacoes.append(f'Falha ao atualizar coluna VPN: {e_upd_vpn}')
                except Exception as e:
                    msg_operacoes.append(f'Falha na rotina de extração de IPv6: {e}')

                    # 2) Zoho: status e campo customizado "data_liberacao_servidor"
                    if access_token:
                        try:
                            # Define explicitamente o status Em Andamento
                            status_id = "2376502000000020092"
                            url = f"{utils._zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}"
                            r = requests.patch(url, headers=utils._zp_headers(access_token), json={"status": {"id": status_id}}, timeout=30)
                            if r.status_code in (200, 201):
                                msg_operacoes.append('Zoho: Status do projeto definido para Em Andamento')
                            else:
                                msg_operacoes.append(f"Zoho: falha ao definir status (HTTP {r.status_code})")
                        except Exception as e:
                            msg_operacoes.append(f'Zoho: erro ao definir status (regra específica): {e}')

                        try:
                            # 1) Planilha: atualizar 'Lib.Servidor' com data atual (DD/MM/YYYY), sobrescrevendo
                            try:
                                hoje_br = datetime.now().strftime('%d/%m/%Y')
                                alvo_cliente = (locals().get('cliente_lookup') or locals().get('codigo_lookup') or valor_cliente or '').strip()
                                if sheets_service and alvo_cliente:
                                    # Usa helper tolerante para coluna específica
                                    utils.update_col_value_by_cliente_tolerant(
                                        sheets_service,
                                        alvo_cliente,
                                        "Lib.Servidor",
                                        hoje_br
                                    )
                                    msg_operacoes.append('Planilha: Lib.Servidor atualizada')
                            except Exception as e2:
                                msg_operacoes.append(f'Falha ao atualizar Lib.Servidor: {e2}')

                            # 2) Zoho: atualizar custom field 'data_liberacao_servidor' (YYYY-MM-DD)
                            hoje_iso = datetime.now().strftime('%Y-%m-%d')
                            url = f"{utils._zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}"
                            headers = {**utils._zp_headers(access_token), "Content-Type": "application/json"}

                            # PATCH no campo top-level (formato suportado no seu tenant)
                            payload = {"data_liberacao_servidor": hoje_iso}
                            print(f"[/api/mover_projeto] PATCH top-level payload={payload}")
                            r = requests.patch(url, headers=headers, json=payload, timeout=30)
                            print(f"[/api/mover_projeto] result status={r.status_code} body={r.text[:500]}")
                            if r.status_code in (200, 201):
                                msg_operacoes.append('Zoho: Campo "Data Liberação Servidor" atualizado (top-level)')
                                # GET para confirmar valor salvo
                                try:
                                    rg = requests.get(url, headers=utils._zp_headers(access_token), timeout=20)
                                    body = rg.json() if rg.headers.get('Content-Type','').startswith('application/json') else {"raw": rg.text}
                                    node = body.get('project', body) if isinstance(body, dict) else {}
                                    atual = (node or {}).get('data_liberacao_servidor')
                                    print(f"[/api/mover_projeto] check get data_liberacao_servidor={atual}")
                                except Exception as eg:
                                    print(f"[/api/mover_projeto] GET confirm falhou: {eg}")
                            else:
                                msg_operacoes.append(f"Zoho: falha ao atualizar campo customizado (HTTP {r.status_code})")
                        except Exception as e:
                            print(f"[/api/mover_projeto] EXCEPTION ao atualizar custom_fields data_liberacao_servidor: {e}")
                            msg_operacoes.append(f'Zoho: erro ao atualizar campo customizado (regra específica): {e}')


            # 5) Tags (definir exatamente conforme mapeamento)
            if access_token:
                try:
                    final_tags = [str(t) for t in (info_dest.get('zohoTagsToAdd') or [])]
                    # Se o mapeamento desejar explicitamente remover tags, elas simplesmente não entram no conjunto final
                    utils.set_project_tags_exact(access_token, projeto_id, final_tags)
                    msg_operacoes.append('Tags definidas exatamente conforme mapeamento')
                except Exception as e:
                    print(f"[/api/mover_projeto] ERRO ao definir tags exatas: {e}")
                    msg_operacoes.append(f'Falha ao definir tags: {e}')

            # 6) Ações adicionais por gatilho
            trigger = info_dest.get('triggersAction')
            if trigger and access_token:
                try:
                    if trigger == 'adicionar_comentario_servidor':
                        mentions_text = utils.zoho_mentions(["Giovani Sousa"])
                        comentario = (
                            f"Bom dia {mentions_text}, tudo bem? Realizada reunião de onboarding com o cliente. "
                            "Sendo assim, podemos dar inicio as atividades de infra. Vamos iniciar os grupos. "
                            "Os detalhes do projeto se encontram na descrição do mesmo. Att"
                        )
                        print("[/api/mover_projeto] Buscando tarefa '02.01.01 - Validação do DEIP'...")
                        task_id = utils.find_task_by_name(access_token, projeto_id, "02.01.01 - Validação do DEIP")
                        print(f"[/api/mover_projeto] task_id encontrado: {task_id}")
                        if task_id:
                            utils.add_comment_to_task(access_token, projeto_id, task_id, comentario)
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
                    mentions_text_import = utils.zoho_mentions(["Giovani Sousa"])
                    task_import_id = utils.find_task_by_name(access_token, projeto_id, "Contato inicial com o cliente")
                    if task_import_id:
                        comentario_import = (
                            f"Bom dia {mentions_text_import}, tudo bem? Apenas para informar que o servidor se encontra liberado.\n\n"
                            "Sendo assim, podemos dar inicio as atividades de Importação. Vamos iniciar os grupos. \n\n"
                            "Os detalhes do projeto se encontram na descrição do mesmo. Att"
                        )
                        utils.add_comment_to_task(access_token, projeto_id, task_import_id, comentario_import)
                        msg_operacoes.append('Comentário adicionado na tarefa de importação.')
                    else:
                        msg_operacoes.append('Tarefa de importação não encontrada.')

                    # Comentário na tarefa de integração
                    mentions_text_integ = utils.zoho_mentions(["Giovani Sousa"])
                    task_integ_id = utils.find_task_by_name(access_token, projeto_id, "Solicitar dados ao RIS/HIS para integração de worklist")
                    if task_integ_id:
                        comentario_integ = (
                            f"Bom dia {mentions_text_integ}, tudo bem? Apenas para informar que o servidor se encontra liberado.\n\n"
                            "Sendo assim, podemos dar inicio as atividades de Integração. Vamos iniciar os grupos. \n\n"
                            "Os detalhes do projeto se encontram na descrição do mesmo. Att"
                        )
                        utils.add_comment_to_task(access_token, projeto_id, task_integ_id, comentario_integ)
                        msg_operacoes.append('Comentário adicionado na tarefa de integração.')
                    else:
                        msg_operacoes.append('Tarefa de integração não encontrada.')

                except Exception as e:
                    print(f"[/api/mover_projeto] ERRO ao adicionar comentários em tarefas de 'Em Andamento': {e}")
                    msg_operacoes.append(f'Falha ao adicionar comentários: {e}')

        # Atualiza cache de dias-na-fase apenas para o projeto movido
        try:
            utils._invalidate_dias_cache(projeto_id)
            now_ts = int(time.time())
            chave_hint = f"{projeto_id}|{coluna_destino}"
            current_app.config['_DIAS_FASE_CACHE'][chave_hint] = { 'valor': 'Hoje', 'ts': now_ts }
            current_app.config['_DIAS_FASE_CACHE'][str(projeto_id)] = { 'valor': 'Hoje', 'ts': now_ts }
        except Exception:
            pass

        return jsonify({"sucesso": True, "mensagem": "; ".join(msg_operacoes) or 'Movimentação registrada.'})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"sucesso": False, "erro": str(e)}), 500

@api_bp.route('/projetos/comentar', methods=['POST'])
def comentar_projeto():
    try:
        if 'credentials' not in session:
            return jsonify({"sucesso": False, "erro": "Não autenticado."}),

        data = request.get_json(silent=True) or {}
        projeto_id = str(data.get('projeto_id') or '').strip()
        content = (data.get('content') or '').strip()
        if not projeto_id or not content:
            return jsonify({"sucesso": False, "erro": "Parâmetros inválidos"}), 400

        access_token = utils.obter_access_token()
        url = f"{utils._zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}/comments"

        # Tenta formatos aceitos pela API do Zoho
        last_resp = None
        for payload in ({"comment": content}, {"content": content}):
            try:
                r = requests.post(
                    url,
                    headers={**utils._zp_headers(access_token), "Content-Type": "application/json"},
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

        print(f"[DEBUG:/api/iniciar_implantacao] payload: project_id={project_id}, data_inicio_implantacao={data_inicio_implantacao}, implantador_ris='{implantador_ris}', implantador_pacs='{implantador_pacs}'")

        if not project_id or not data_inicio_implantacao:
            return jsonify({"sucesso": False, "erro": "Parâmetros inválidos."}), 400

        # Serviço do Google Sheets a partir da sessão
        creds = utils.build_google_credentials_from_session()
        sheets_service = build('sheets', 'v4', credentials=creds)

        # Buscar dados do projeto no Zoho para identificar o cliente (chave da planilha)
        access_token = utils.obter_access_token_zoho()
        detalhes_zoho = utils.obter_detalhes_projeto(access_token, project_id)
        proj_name = str((detalhes_zoho or {}).get('name', '') or '')
        # Extrai base 'CODIGO[/ANO] - Cliente' removendo sufixos de produto
        base_cliente = proj_name.split(' - NR')[0].split(' - AP')[0].split(' - NR/AP')[0].strip()
        chave_busca = base_cliente
        print(f"[DEBUG:/api/iniciar_implantacao] proj_name='{proj_name}' base_cliente='{base_cliente}'")
        if not chave_busca:
            return jsonify({"sucesso": False, "erro": "Não foi possível identificar o cliente do projeto."}), 400

        # Formata data para dd/mm/yyyy
        def _fmt_ddmmyyyy(s: str) -> str:
            try:
                y, m, d = s.split('-')
                return f"{d.zfill(2)}/{m.zfill(2)}/{y}"
            except Exception:
                return s

        # Monta valor no formato do dropdown usando apenas o primeiro nome (RIS com exceção opcional p/ Rodrigo)
        def _primeiro_nome(nome: str) -> str:
            nome = (nome or '').strip()
            if not nome:
                return ''
            partes = nome.split()
            # Exceção: se RIS começar com Rodrigo, manter "Rodrigo <sobrenome>"
            return partes[0]
        implant_responsavel = ''
        pacs_first = _primeiro_nome(implantador_pacs)
        ris_first = _primeiro_nome(implantador_ris)
        if pacs_first:
            implant_responsavel = f"Pacs - {pacs_first}"
            if ris_first:
                implant_responsavel += f" + Ris - {ris_first}"
        print(f"[DEBUG:/api/iniciar_implantacao] implant_responsavel='{implant_responsavel}'")

        # 1) Atualiza Dt Inicio Implantação
        try:
            utils.update_col_value_by_cliente_tolerant(
                sheets_service,
                chave_busca,
                'Dt Inicio Implantação',
                _fmt_ddmmyyyy(data_inicio_implantacao)
            )
        except Exception as e:
            print(f"[DEBUG:/api/iniciar_implantacao] erro ao atualizar 'Dt Inicio Implantação': {e}")
            return jsonify({"sucesso": False, "erro": f"Falha ao atualizar data na planilha: {e}"}), 500

        # 2) Atualiza Implant Responsável somente quando houver PACS (para casar com o dropdown)
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
                print(f"[DEBUG:/api/iniciar_implantacao] erro ao atualizar 'Implant Responsável': {e}")
                return jsonify({"sucesso": False, "erro": f"Falha ao atualizar implantador na planilha: {e}"}), 500
        else:
            detalhes_msg.append("Implant Responsável não atualizado (selecione PACS).")

        return jsonify({"sucesso": True, "mensagem": "Implantação agendada e planilha atualizada.", "detalhes": detalhes_msg})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"sucesso": False, "erro": str(e)}), 500