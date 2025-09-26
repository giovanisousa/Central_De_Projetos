import requests
import time

# Importa as configurações e funções necessárias dos outros módulos do projeto
from config import ZOHO_PORTAL_ID
from database import (
    get_last_sync_time,
    upsert_project,
    upsert_fase,
    upsert_lista_de_tarefas,
    upsert_tarefa,
)
from utils import obter_access_token as obter_access_token_zoho, _zp_base, _zp_headers


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


def synchronize_single_project(project_id: str, access_token: str | None = None):
    """Sincroniza apenas um projeto específico (e seus detalhes) com o banco local."""
    if not project_id:
        return None

    try:
        token = access_token or obter_access_token_zoho()
        headers = _zp_headers(token)
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
        response = requests.get(url, headers=headers, timeout=45)
        response.raise_for_status()
        project = _extract_project_from_response(response.json(), project_id)
        if not project:
            print(f"WARN: Projeto {project_id} não encontrado na resposta do Zoho.")
            return None

        upsert_project(project)
        print(f"  -> Sincronizado projeto individual: {project.get('name')} (ID: {project.get('id')})")

        fases_do_projeto = sync_fases(project_id, token)
        id_fase_impeditivos = None
        for fase in fases_do_projeto:
            if fase.get('name') == "00 - Itens impeditivos de virada":
                id_fase_impeditivos = fase.get('id')
                break
        sync_listas_e_tarefas(project_id, token, id_fase_impeditivos)

        return project
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao sincronizar projeto {project_id}: {e}")
        if e.response is not None:
            print(f"Detalhes: {e.response.text[:400]}")
        return None
    except Exception as e:
        print(f"ERRO inesperado no sync individual do projeto {project_id}: {e}")
        return None


def synchronize_projects():
    """
    Sincroniza os projetos do Zoho com o banco de dados local, incluindo fases, listas e tarefas.
    """
    DEBUG_PROJECT_ID = "2376502000002326783"
    NOME_FASE_IMPEDITIVOS = "00 - Itens impeditivos de virada"

    if DEBUG_PROJECT_ID:
        print(f"--- MODO DE DEBUG: Sincronizando apenas o projeto ID: {DEBUG_PROJECT_ID} ---")
        try:
            access_token = obter_access_token_zoho()
            url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{DEBUG_PROJECT_ID}"
            headers = _zp_headers(access_token)
            response = requests.get(url, headers=headers, timeout=45)
            response.raise_for_status()
            data = response.json()
            project = None

            if isinstance(data, dict) and data.get('id') == DEBUG_PROJECT_ID:
                project = data
            elif isinstance(data, dict) and 'projects' in data and data['projects']:
                project = data['projects'][0]

            if project:
                upsert_project(project)
                print(f"  -> Sincronizado projeto: {project.get('name')} (ID: {project.get('id')})")
                project_id = project.get('id')
                if project_id:
                    print(f"    - Sincronizando detalhes para o projeto...")
                    fases_do_projeto = sync_fases(project_id, access_token)

                    id_fase_impeditivos = None
                    for fase in fases_do_projeto:
                        if fase.get('name') == NOME_FASE_IMPEDITIVOS:
                            id_fase_impeditivos = fase.get('id')
                            print(f"    - Fase de impeditivos encontrada (ID: {id_fase_impeditivos}).")
                            break

                    sync_listas_e_tarefas(project_id, access_token, id_fase_impeditivos)

                print("\n--- Sincronização de debug concluída. ---")
            else:
                print(f"ERRO: Projeto de debug não encontrado. Resposta da API: {data}")

        except Exception as e:
            print(f"\nERRO INESPERADO no modo de debug: {e}")
        return

    print("--- Iniciando sincronização completa do Zoho ---")
    try:
        access_token = obter_access_token_zoho()
        last_sync_time = get_last_sync_time()
        print(f"Buscando projetos modificados desde: {last_sync_time}")
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects"
        headers = _zp_headers(access_token)
        page = 1
        total_synced = 0
        while True:
            params = {"page": page, "per_page": 50, "last_modified_time": last_sync_time}
            print(f"Buscando página {page} de projetos...")
            response = requests.get(url, headers=headers, params=params, timeout=45)
            response.raise_for_status()
            data = response.json()
            projects = []
            if isinstance(data, dict):
                projects = data.get('projects', [])
            elif isinstance(data, list):
                projects = data
            if not projects:
                print("Nenhum projeto novo ou modificado encontrado.")
                break
            for project in projects:
                try:
                    upsert_project(project)
                    print(f"  -> Sincronizado projeto: {project.get('name')} (ID: {project.get('id')})")
                    total_synced += 1
                    project_id = project.get('id')
                    if project_id:
                        print(f"    - Sincronizando detalhes para o projeto...")
                        fases_do_projeto = sync_fases(project_id, access_token)
                        id_fase_impeditivos = None
                        for fase in fases_do_projeto:
                            if fase.get('name') == NOME_FASE_IMPEDITIVOS:
                                id_fase_impeditivos = fase.get('id')
                                print(f"    - Fase de impeditivos encontrada (ID: {id_fase_impeditivos}).")
                                break
                        sync_listas_e_tarefas(project_id, access_token, id_fase_impeditivos)
                except Exception as e:
                    print(f"ERRO ao salvar o projeto {project.get('id_string')}: {e}")
            if len(projects) < 50:
                break
            page += 1
            time.sleep(1)
        print(f"\n--- Sincronização concluída. {total_synced} projetos foram atualizados/inseridos. ---")
    except requests.exceptions.RequestException as e:
        print(f"\nERRO DE API: Falha ao comunicar com o Zoho. {e}")
        if e.response is not None:
            print(f"Detalhes: {e.response.text}")
    except Exception as e:
        print(f"\nERRO INESPERADO: Ocorreu um erro durante a sincronização: {e}")


if __name__ == "__main__":
    synchronize_projects()
