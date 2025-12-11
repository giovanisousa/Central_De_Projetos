import requests
import time
import json
from pathlib import Path

# Importa as configurações e funções necessárias dos outros módulos do projeto
from config import (
    ZOHO_PORTAL_ID,
    PROPRIETARIOS_VALIDOS,
    STATUS_CANCELADO_ID,
    STATUS_FINALIZADO_ID,
    STATUS_CONCLUIDO_ID
)
from database import (
    get_last_sync_time,
    upsert_project,
    upsert_fase,
    upsert_lista_de_tarefas,
    upsert_tarefa,
    Session,
    Project
)
from utils import obter_access_token as obter_access_token_zoho, _zp_base, _zp_headers

# IDs dos status que devem ser EXCLUÍDOS da sincronização
STATUS_EXCLUIDOS = {
    STATUS_CANCELADO_ID,    # Cancelado
    STATUS_FINALIZADO_ID,   # Finalizado / Completed
    STATUS_CONCLUIDO_ID     # Concluído
}


def projeto_deve_ser_salvo(project_data):
    """
    Verifica se um projeto atende aos critérios para ser salvo no banco.
    
    Critérios:
    1. Proprietário (owner) deve ser Giovani OU Willian
    2. Status NÃO deve ser Cancelado, Finalizado ou Concluído
    
    Args:
        project_data: Dicionário com os dados do projeto da API do Zoho
        
    Returns:
        bool: True se o projeto deve ser salvo, False caso contrário
    """
    # Valida proprietário
    owner = project_data.get('owner', {})
    owner_name = owner.get('name', '')
    proprietario_valido = owner_name in PROPRIETARIOS_VALIDOS

    # Valida status - EXCLUIR Cancelado, Finalizado e Concluído
    # ATENÇÃO: Mudança de lógica para aceitar TODOS os status EXCETO os excluídos
    status = project_data.get('status', {})
    status_id = str(status.get('id', ''))
    status_name = status.get('name', 'Desconhecido')
    
    # Aceita o projeto se o status NÃO está na lista de excluídos
    status_valido = status_id not in STATUS_EXCLUIDOS

    # LOG DETALHADO DO FILTRO
    if not proprietario_valido:
        print(f"[FILTRO] Projeto ignorado por proprietário inválido: {project_data.get('name')} - Proprietário: {owner_name} (Válidos: {PROPRIETARIOS_VALIDOS})")
    if not status_valido:
        print(f"[FILTRO] Projeto ignorado por status excluído: {project_data.get('name')} - Status: {status_name} (ID: {status_id})")

    # Retorna True apenas se AMBOS os critérios forem atendidos
    return proprietario_valido and status_valido


def _extract_project_from_response(data, project_id):
    """Normaliza a resposta da API de projetos do Zoho."""
    if isinstance(data, dict):
        if str(data.get('id')) == str(project_id):
            return data
        if 'project' in data and isinstance(data['project'], dict):
            if str(data['project'].get('id')) == str(project_id):
                return data['project']
        if 'projects' in data and data['projects']:
            for item in data['projects']:
                if str(item.get('id')) == str(project_id):
                    return item
    return None


def sync_fases(projeto_id, access_token):
    """Busca a lista de fases e, em seguida, busca o detalhe de cada uma para obter o percentual de conclusão."""
    try:
        list_url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}/phases"
        headers = _zp_headers(access_token)
        list_response = requests.get(list_url, headers=headers, timeout=45)
        list_response.raise_for_status()
        fases_summary = list_response.json().get('milestones', [])

        print(f"    - Encontradas {len(fases_summary)} fases. Buscando detalhes...")

        fases_detailed = []
        for fase_summary in fases_summary:
            fase_id = fase_summary.get('id')
            if not fase_id:
                continue

            time.sleep(0.5)
            # Polling: aguarda até 2s ou até que resposta da API esteja disponível
            polling_timeout = 2
            polling_interval = 0.5
            polling_start = time.time()
            while time.time() - polling_start < polling_timeout:
                print(f"[polling] aguardando resposta da API... ({int((time.time()-polling_start)*1000)}ms)")
                time.sleep(polling_interval)

            try:
                detail_url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}/phases/{fase_id}"
                detail_response = requests.get(detail_url, headers=headers, timeout=45)
                detail_response.raise_for_status()
                fase_detail_data = detail_response.json()

                final_fase_data = None
                if isinstance(fase_detail_data, dict) and fase_detail_data.get('id') == fase_id:
                    final_fase_data = fase_detail_data
                elif isinstance(fase_detail_data, dict) and 'phases' in fase_detail_data and fase_detail_data['phases']:
                    final_fase_data = fase_detail_data['phases'][0]
                elif isinstance(fase_detail_data, dict) and 'milestones' in fase_detail_data and fase_detail_data['milestones']:
                    final_fase_data = fase_detail_data['milestones'][0]

                if final_fase_data:
                    upsert_fase(final_fase_data, projeto_id)
                    fases_detailed.append(final_fase_data)

            except requests.exceptions.RequestException as e:
                print(f"      - ERRO ao buscar detalhes da fase {fase_id}: {e}")
                continue

        return fases_detailed

    except requests.exceptions.RequestException as e:
        print(f"    - ERRO ao buscar a lista de fases do projeto {projeto_id}: {e}")
        return []


def sync_listas_e_tarefas(projeto_id, access_token, id_fase_impeditivos):
    """Busca e sincroniza as listas de tarefas. Busca tarefas APENAS para as listas que pertencem à fase de impeditivos."""
    try:
        url_listas = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}/tasklists"
        headers = _zp_headers(access_token)
        response_listas = requests.get(url_listas, headers=headers, timeout=45)
        response_listas.raise_for_status()
        listas_summary = response_listas.json().get('tasklists', [])
        print(f"    - Encontradas {len(listas_summary)} listas de tarefas.")

        for lista_data in listas_summary:
            # A informação da lista resumida é suficiente para o filtro e cadastro inicial.
            upsert_lista_de_tarefas(lista_data, projeto_id)

            fase_id_da_lista = lista_data.get('milestone', {}).get('id')
            lista_id = lista_data.get('id')

            # Apenas busca tarefas se a lista pertencer à fase de impeditivos
            if id_fase_impeditivos and str(fase_id_da_lista) == str(id_fase_impeditivos):
                print(f"      - Lista '{lista_data.get('name')}' pertence à fase de impeditivos. Buscando tarefas...")
                time.sleep(0.5)  # Pausa para não sobrecarregar a API
            # Polling: aguarda até 2s ou até que tarefas estejam disponíveis
            import time
            polling_timeout = 2
            polling_interval = 0.5
            polling_start = time.time()
            while time.time() - polling_start < polling_timeout:
                print(f"[polling] aguardando tarefas... ({int((time.time()-polling_start)*1000)}ms)")
                time.sleep(polling_interval)
                try:
                    url_tarefas = (
                        f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}/tasklists/{lista_id}/tasks/"
                    )
                    response_tarefas = requests.get(url_tarefas, headers=headers, timeout=45)
                    response_tarefas.raise_for_status()
                    tarefas = response_tarefas.json().get('tasks', [])

                    print(f"        - Encontradas {len(tarefas)} tarefas.")
                    for tarefa in tarefas:
                        upsert_tarefa(tarefa, lista_id, fase_id_da_lista, projeto_id)
                except requests.exceptions.RequestException as e:
                    print(f"        - ERRO ao buscar tarefas da lista {lista_id}: {e}")

    except requests.exceptions.RequestException as e:
        print(f"    - ERRO ao buscar listas de tarefas do projeto {projeto_id}: {e}")





def synchronize_projects():
    """
    Sincroniza os projetos do Zoho com o banco de dados local.
    
    ESTRATÉGIA OTIMIZADA (2 fases):
    1. FASE 1: Busca RÁPIDA de todos os IDs dos projetos (sem detalhes)
    2. FASE 2: Sincroniza detalhes de cada projeto (com renovação de token)
    
    Isso evita expiração do token durante paginação.
    """
    NOME_FASE_IMPEDITIVOS = "00 - Itens impeditivos de virada"
    QUEUE_FILE = Path("sync_queue_projects.json")
    
    print("=" * 80)
    print("  SINCRONIZAÇÃO OTIMIZADA DE PROJETOS")
    print("=" * 80)
    print(f"[DEBUG] PROPRIETARIOS_VALIDOS: {PROPRIETARIOS_VALIDOS}\n")
    
    try:
        # Verificar se existe fila de sincronização
        if QUEUE_FILE.exists():
            print("[RESUMINDO] Arquivo de fila encontrado. Continuando sincronização...\n")
            with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                queue_data = json.load(f)
                projects_to_sync = queue_data.get('projects', [])
                processed = set(queue_data.get('processed', []))
            
            print(f"  - Total na fila: {len(projects_to_sync)}")
            print(f"  - Já processados: {len(processed)}")
            print(f"  - Faltam: {len(projects_to_sync) - len(processed)}\n")
        else:
            # FASE 1: Buscar todos os IDs dos projetos (RÁPIDO)
            print("=" * 80)
            print("[FASE 1/2] BUSCANDO IDs DE TODOS OS PROJETOS")
            print("=" * 80)
            print("Esta etapa é RÁPIDA - apenas coleta IDs, sem detalhes.\n")
            
            access_token = obter_access_token_zoho()
            
            # Verificar modo de sincronização
            session = Session()
            try:
                total_projetos_no_banco = session.query(Project).count()
            finally:
                session.close()
            
            force_full_sync = total_projetos_no_banco < 100
            
            if force_full_sync:
                print(f"[MODO COMPLETO] Banco tem apenas {total_projetos_no_banco} projetos.")
                print("Buscando TODOS os projetos do Zoho (sem filtro de data)...\n")
                last_sync_time = None
            else:
                last_sync_time = get_last_sync_time()
                print(f"[MODO INCREMENTAL] Buscando projetos modificados desde: {last_sync_time}\n")
            
            url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects"
            headers = _zp_headers(access_token)
            
            projects_to_sync = []
            page = 1
            
            while True:
                params = {"page": page, "per_page": 50}
                if last_sync_time:
                    params["last_modified_time"] = last_sync_time
                
                print(f"  Buscando página {page}...", end=" ")
                
                try:
                    response = requests.get(url, headers=headers, params=params, timeout=45)
                    response.raise_for_status()
                    data = response.json()
                    
                    projects = data.get('projects', []) if isinstance(data, dict) else data
                    
                    if not projects:
                        print("(vazia - fim da paginação)")
                        break
                    
                    # Filtrar e adicionar à fila
                    filtered_count = 0
                    for project in projects:
                        if projeto_deve_ser_salvo(project):
                            projects_to_sync.append({
                                'id': project.get('id'),
                                'nome': project.get('name', 'Sem nome'),
                                'data': project  # Guardar dados completos
                            })
                            filtered_count += 1
                    
                    print(f"({len(projects)} projetos, {filtered_count} válidos)")
                    
                    if len(projects) < 50:
                        break
                    
                    page += 1
                    time.sleep(0.5)  # Pequena pausa entre páginas
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        print("\n[AVISO] Token expirado. Renovando...")
                        access_token = obter_access_token_zoho()
                        headers = _zp_headers(access_token)
                        continue
                    else:
                        raise
            
            print(f"\n[RESULTADO FASE 1] {len(projects_to_sync)} projetos válidos encontrados.\n")
            
            if len(projects_to_sync) == 0:
                print("Nenhum projeto para sincronizar.")
                return
            
            # Criar arquivo de fila
            processed = set()
            queue_data = {
                'projects': projects_to_sync,
                'processed': list(processed),
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
                json.dump(queue_data, f, ensure_ascii=False, indent=2)
            
            print(f"[QUEUE] Arquivo de fila criado: {QUEUE_FILE}\n")
        
        # FASE 2: Sincronizar detalhes de cada projeto
        print("=" * 80)
        print("[FASE 2/2] SINCRONIZANDO DETALHES DOS PROJETOS")
        print("=" * 80)
        print(f"Processando {len(projects_to_sync)} projetos com renovação automática de token.\n")
        
        access_token = obter_access_token_zoho()
        token_renovado_em = time.time()
        total_synced = 0
        
        for idx, project_info in enumerate(projects_to_sync, 1):
            project_id = project_info['id']
            
            # Pular se já foi processado
            if project_id in processed:
                continue
            
            # Renovar token a cada 30 projetos ou se passou mais de 45 minutos
            if idx % 30 == 0 or (time.time() - token_renovado_em) > 2700:
                print(f"\n[TOKEN] Renovando token preventivamente...")
                access_token = obter_access_token_zoho()
                token_renovado_em = time.time()
            
            print(f"[{idx}/{len(projects_to_sync)}] Sincronizando: {project_info['nome'][:50]}...")
            
            try:
                # Inserir/atualizar projeto
                projeto_salvo = upsert_project(project_info['data'])
                
                if not projeto_salvo:
                    print(f"  ✗ ERRO: Falha ao salvar projeto no banco - pulando para próximo")
                    continue
                
                # Sincronizar fases
                fases_do_projeto = sync_fases(project_id, access_token)
                
                # Buscar fase de impeditivos
                id_fase_impeditivos = None
                for fase in fases_do_projeto:
                    if fase.get('name') == NOME_FASE_IMPEDITIVOS:
                        id_fase_impeditivos = fase.get('id')
                        break
                
                # Sincronizar listas e tarefas
                sync_listas_e_tarefas(project_id, access_token, id_fase_impeditivos)
                
                # ✅ Só marca como processado se realmente salvou no banco
                processed.add(project_id)
                total_synced += 1
                
                # Persistir progresso a cada 5 projetos
                if idx % 5 == 0:
                    queue_data['processed'] = list(processed)
                    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(queue_data, f, ensure_ascii=False, indent=2)
                
                print(f"  ✓ Concluído ({len(fases_do_projeto)} fases)")
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    print(f"  ⚠ Token expirado. Renovando e tentando novamente...")
                    access_token = obter_access_token_zoho()
                    token_renovado_em = time.time()
                    # Reprocessar este projeto
                    continue
                else:
                    print(f"  ✗ ERRO HTTP {e.response.status_code}: {e}")
                    
            except Exception as e:
                print(f"  ✗ ERRO: {e}")
            
            time.sleep(0.3)  # Pequena pausa entre projetos
        
        # Salvar progresso final
        queue_data['processed'] = list(processed)
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(queue_data, f, ensure_ascii=False, indent=2)
        
        # Remover arquivo de fila se concluído
        if len(processed) == len(projects_to_sync):
            QUEUE_FILE.unlink()
            print(f"\n[CLEANUP] Arquivo de fila removido (sincronização completa).")
        
        print("\n" + "=" * 80)
        print(f"[SUCESSO] {total_synced} projetos sincronizados!")
        print("=" * 80 + "\n")
        
    except requests.exceptions.RequestException as e:
        print(f"\n[ERRO DE API] Falha ao comunicar com o Zoho: {e}")
        if e.response is not None:
            print(f"Detalhes: {e.response.text}")
    except KeyboardInterrupt:
        print(f"\n[INTERROMPIDO] Sincronização pausada pelo usuário.")
        print(f"Execute novamente para continuar de onde parou.")
        print(f"Progresso salvo: {len(processed)}/{len(projects_to_sync)} projetos\n")
    except Exception as e:
        print(f"\n[ERRO INESPERADO] {e}")
        import traceback
        traceback.print_exc()


def synchronize_single_project(project_id, access_token):
    """
    Sincroniza um projeto específico do Zoho Projects para o banco local.
    Retorna True se o projeto foi encontrado e sincronizado, False caso contrário.
    """
    try:
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
        headers = _zp_headers(access_token)
        response = requests.get(url, headers=headers, timeout=45)
        response.raise_for_status()
        data = response.json()

        project = _extract_project_from_response(data, project_id)
        if project:
            # Aplica filtro antes de salvar
            if not projeto_deve_ser_salvo(project):
                owner_name = project.get('owner', {}).get('name', 'Desconhecido')
                status_name = project.get('status', {}).get('name', 'Desconhecido')
                print(f"Projeto ignorado (não atende critérios): {project.get('name')} - Proprietário: {owner_name}, Status: {status_name}")
                return False
            
            # ✅ Verificar se realmente salvou no banco
            projeto_salvo = upsert_project(project)
            if not projeto_salvo:
                print(f"✗ ERRO: Falha ao salvar projeto {project.get('name')} no banco")
                return False
            
            print(f"Sincronizado projeto único: {project.get('name')} (ID: {project.get('id')})")
            
            # Sincronizar também as fases/milestones do projeto
            print(f"  - Sincronizando fases do projeto {project_id}...")
            try:
                sync_fases(project_id, access_token)
                print(f"  - Fases sincronizadas com sucesso para o projeto {project_id}")
            except Exception as e:
                print(f"  - Erro ao sincronizar fases do projeto {project_id}: {e}")
            
            return True
        else:
            print(f"Projeto {project_id} não encontrado na resposta da API")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Erro ao sincronizar projeto único {project_id}: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao sincronizar projeto único {project_id}: {e}")
        return False


def sync_all_phases_for_existing_projects(queue_file_path: str = None):
    """
    Sincroniza todas as fases de todos os projetos existentes no banco de dados.
    Processo resiliente que primeiro coleta a lista de projetos (IDs) a serem
    processados e grava um arquivo de fila para poder retomar caso ocorra
    falha ou interrupção.
    """
    from database import Session, Project, Fase

    queue_file = Path(queue_file_path or "sync_queue_phases.json")

    print("\n=== SINCRONIZANDO FASES DE TODOS OS PROJETOS (modo resiliente) ===\n")

    # Se existir arquivo de fila, carregue-o (resume); caso contrário, monte a fila
    if queue_file.exists():
        try:
            with queue_file.open("r", encoding="utf-8") as f:
                state = json.load(f)
            project_list = state.get("projects", [])
            processed = set(state.get("processed", []))
            print(f"[RESUME] Encontrado arquivo de fila com {len(project_list)} projetos, {len(processed)} processados")
        except Exception as e:
            print(f"[ERRO] Ao ler arquivo de fila {queue_file}: {e}. Removendo arquivo corrompido.")
            try:
                queue_file.unlink()
            except:
                pass
            project_list = []
            processed = set()
    else:
        # Montar lista a partir do banco
        session = Session()
        try:
            projetos = session.query(Project).all()
            project_list = [{"id": p.id, "nome": p.nome or ""} for p in projetos]
        finally:
            try:
                session.close()
            except:
                pass
        processed = set()
        # Salvar fila inicial
        state = {"projects": project_list, "processed": list(processed)}
        with queue_file.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print(f"[INIT] Arquivo de fila criado com {len(project_list)} projetos")

    total = len(project_list)
    if total == 0:
        print("Nenhum projeto encontrado para sincronizar.")
        return

    # Obter token inicial
    try:
        access_token = obter_access_token_zoho()
        token_acquired_at = time.time()
    except Exception as e:
        print(f"✗ Erro ao obter access token: {e}")
        return

    sucessos = 0
    falhas = 0
    fases_total_sincronizadas = 0

    # Função auxiliar para persistir estado
    def persist_state():
        tmp = queue_file.with_suffix('.tmp')
        state = {"projects": project_list, "processed": list(processed)}
        with tmp.open('w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        tmp.replace(queue_file)

    # Iterar pela lista de projetos (ordem fixa)
    for idx, proj in enumerate(project_list, 1):
        project_id = proj.get("id")
        project_name = proj.get("nome") or "Sem nome"

        if project_id in processed:
            print(f"[{idx}/{total}] {project_name} (ID: {project_id}) - ja processado, pulando")
            continue

        print(f"[{idx}/{total}] Sincronizando fases do projeto: {project_name} (ID: {project_id})")

        # Renovar token a cada 50 minutos (segurança)
        if time.time() - token_acquired_at > (50 * 60):
            try:
                access_token = obter_access_token_zoho()
                token_acquired_at = time.time()
                print("  [INFO] Token Zoho renovado automaticamente")
            except Exception as e:
                print(f"  [ERRO] Falha ao renovar token: {e}")

        # Tentar sincronizar com retries em caso de falha transitória
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                fases_sincronizadas = sync_fases(project_id, access_token)
                num_fases = len(fases_sincronizadas)
                if num_fases > 0:
                    print(f"  ✓ {num_fases} fases sincronizadas")
                    sucessos += 1
                    fases_total_sincronizadas += num_fases
                else:
                    print(f"  ⚠ 0 fases (projeto pode não ter milestones)")
                    falhas += 1
                # Marcar como processado e persistir imediatamente
                processed.add(project_id)
                persist_state()
                break
            except Exception as e:
                msg = str(e)
                print(f"  [ERRO] Tentativa {attempt}/{max_attempts} ao sincronizar {project_id}: {msg}")
                # Se token inválido, renovar e retry
                if 'INVALID_OAUTHTOKEN' in msg or '401' in msg or 'Invalid OAuth access token' in msg:
                    try:
                        access_token = obter_access_token_zoho()
                        token_acquired_at = time.time()
                        print("  [INFO] Token Zoho renovado (por 401)")
                        time.sleep(1)
                        continue
                    except Exception as tok_err:
                        print(f"  [ERRO] Nao foi possivel renovar token: {tok_err}")
                        break
                # Erro de conexão com banco (SSL fechado) - aguardar e retry
                if 'SSL connection' in msg or 'connection has been closed' in msg.lower():
                    print("  [AVISO] Conexao SSL fechada inesperadamente. Aguardando 5s e tentando novamente...")
                    time.sleep(5)
                    continue
                # Rate limit
                if '429' in msg or 'THROTTLES_LIMIT_EXCEEDED' in msg:
                    print("  [AVISO] Rate limit detectado. Aguardando 120s...")
                    time.sleep(120)
                    continue
                # Caso geral, aguardar e tentar novamente
                time.sleep(2)
        else:
            print(f"  ✗ Falha ao sincronizar {project_id} apos {max_attempts} tentativas")

        # Pequena pausa entre projetos
        time.sleep(1)

    # Fim do processamento - remover arquivo de fila
    try:
        if queue_file.exists():
            queue_file.unlink()
            print(f"[CLEANUP] Arquivo de fila removido: {queue_file}")
    except Exception as e:
        print(f"[AVISO] Nao foi possivel remover arquivo de fila: {e}")

    print(f"\n{'='*80}")
    print(f"Resumo da sincronização:")
    print(f"- ✓ Sucessos: {sucessos}")
    print(f"- ✗ Falhas: {falhas}")
    print(f"- 📊 Fases sincronizadas nesta execução: {fases_total_sincronizadas}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    synchronize_projects()
