"""
Script robusto para sincronização completa de todos os projetos do Zoho
com renovação automática de token OAuth e recuperação de erros
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import requests
import time
from datetime import datetime

from config import (
    ZOHO_PORTAL_ID, 
    PROPRIETARIOS_VALIDOS,
    STATUS_CANCELADO_ID,
    STATUS_FINALIZADO_ID,
    STATUS_CONCLUIDO_ID
)
from database import upsert_project, get_last_sync_time
from utils import obter_access_token as obter_access_token_zoho, _zp_base, _zp_headers
from sync_zoho import projeto_deve_ser_salvo, sync_fases, sync_listas_e_tarefas

# IDs dos status que devem ser EXCLUÍDOS da sincronização
STATUS_EXCLUIDOS = {
    STATUS_CANCELADO_ID,    # Cancelado
    STATUS_FINALIZADO_ID,   # Finalizado / Completed
    STATUS_CONCLUIDO_ID     # Concluído
}

# ✅ Conexão com Railway PostgreSQL (externa)
print("\n" + "="*80)
print("🚀 SINCRONIZAÇÃO COMPLETA DE PROJETOS DO ZOHO")
print("="*80)
DATABASE_URL = input("\n📋 Cole a URL do PostgreSQL do Railway: ").strip()

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Configurações
NOME_FASE_IMPEDITIVOS = "00 - Itens impeditivos de virada"
MAX_RETRIES = 3
PROJECTS_PER_PAGE = 50

def renovar_token_se_necessario(error_response):
    """
    Verifica se o erro é de token expirado e renova se necessário
    
    Returns:
        str: Novo access_token ou None se não foi possível renovar
    """
    if error_response.status_code == 401:
        print("\n⚠️  Token OAuth expirado! Renovando...")
        try:
            novo_token = obter_access_token_zoho()
            print("✅ Token renovado com sucesso!")
            return novo_token
        except Exception as e:
            print(f"❌ Erro ao renovar token: {e}")
            return None
    return None

def sync_project_details(project_id, project_name, access_token, session_obj):
    """
    Sincroniza fases, listas e tarefas de um projeto
    
    Returns:
        bool: True se sucesso, False se erro
    """
    try:
        print(f"    - Sincronizando detalhes...")
        fases_do_projeto = sync_fases(project_id, access_token)
        
        id_fase_impeditivos = None
        for fase in fases_do_projeto:
            if fase.get('name') == NOME_FASE_IMPEDITIVOS:
                id_fase_impeditivos = fase.get('id')
                print(f"    - Fase de impeditivos encontrada (ID: {id_fase_impeditivos}).")
                break
        
        sync_listas_e_tarefas(project_id, access_token, id_fase_impeditivos)
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"    ⚠️  Token expirado ao buscar detalhes do projeto {project_name}")
            return False
        else:
            print(f"    ⚠️  Erro HTTP ao buscar detalhes: {e}")
            return True  # Não é erro de token, continua
    except Exception as e:
        print(f"    ⚠️  Erro ao sincronizar detalhes: {e}")
        return True  # Erro não crítico, continua

def synchronize_all_projects_robust():
    """
    Sincronização robusta com renovação automática de token
    """
    print("\n--- Iniciando sincronização completa do Zoho ---")
    print(f"📊 Proprietários válidos: {PROPRIETARIOS_VALIDOS}")
    print(f"🚫 Status excluídos: {STATUS_EXCLUIDOS}")
    
    session = Session()
    
    try:
        access_token = obter_access_token_zoho()
        last_sync_time = get_last_sync_time()
        print(f"⏰ Buscando projetos modificados desde: {last_sync_time}")
        
        url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects"
        page = 1
        total_synced = 0
        total_ignored = 0
        total_errors = 0
        
        while True:
            print(f"\n{'='*80}")
            print(f"📄 Buscando página {page} de projetos...")
            print(f"{'='*80}")
            
            params = {
                "page": page, 
                "per_page": PROJECTS_PER_PAGE, 
                "last_modified_time": last_sync_time
            }
            
            retry_count = 0
            success = False
            
            while retry_count < MAX_RETRIES and not success:
                try:
                    headers = _zp_headers(access_token)
                    response = requests.get(url, headers=headers, params=params, timeout=45)
                    
                    # Verifica se token expirou
                    if response.status_code == 401:
                        novo_token = renovar_token_se_necessario(response)
                        if novo_token:
                            access_token = novo_token
                            retry_count += 1
                            continue
                        else:
                            print("\n❌ Não foi possível renovar o token. Abortando sincronização.")
                            return
                    
                    response.raise_for_status()
                    success = True
                    
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    print(f"⚠️  Erro na requisição (tentativa {retry_count}/{MAX_RETRIES}): {e}")
                    if retry_count < MAX_RETRIES:
                        print(f"   Aguardando 5 segundos antes de tentar novamente...")
                        time.sleep(5)
                    else:
                        print(f"❌ Falha após {MAX_RETRIES} tentativas. Abortando.")
                        return
            
            # Processa resposta
            data = response.json()
            projects = []
            
            if isinstance(data, dict):
                projects = data.get('projects', [])
            elif isinstance(data, list):
                projects = data
            
            if not projects:
                print("\n✅ Nenhum projeto novo ou modificado encontrado nesta página.")
                break
            
            print(f"📊 Encontrados {len(projects)} projetos nesta página")
            
            # Processa cada projeto
            for idx, project in enumerate(projects, 1):
                project_name = project.get('name', 'Sem nome')
                project_id = project.get('id')
                
                print(f"\n[{idx}/{len(projects)}] 🔄 Processando: {project_name}")
                
                try:
                    # Aplica filtro
                    if not projeto_deve_ser_salvo(project):
                        owner_name = project.get('owner', {}).get('name', 'Desconhecido')
                        status_name = project.get('status', {}).get('name', 'Desconhecido')
                        print(f"  ⏭️  IGNORADO - Proprietário: {owner_name}, Status: {status_name}")
                        total_ignored += 1
                        continue
                    
                    # Salva projeto
                    upsert_project(project)
                    print(f"  ✅ Projeto sincronizado (ID: {project_id})")
                    total_synced += 1
                    
                    # Sincroniza detalhes (fases, listas, tarefas)
                    if project_id:
                        detail_success = sync_project_details(project_id, project_name, access_token, session)
                        
                        # Se falhou por token expirado, renova e tenta novamente
                        if not detail_success:
                            novo_token = obter_access_token_zoho()
                            if novo_token:
                                access_token = novo_token
                                sync_project_details(project_id, project_name, access_token, session)
                    
                except Exception as e:
                    print(f"  ❌ ERRO ao processar projeto: {e}")
                    total_errors += 1
            
            # Verifica se há mais páginas
            if len(projects) < PROJECTS_PER_PAGE:
                print(f"\n✅ Última página processada (menos de {PROJECTS_PER_PAGE} projetos)")
                break
            
            page += 1
            print(f"\n⏳ Aguardando 2 segundos antes da próxima página...")
            time.sleep(2)
        
        # Resumo final
        print("\n" + "="*80)
        print("✅ ✅ ✅ SINCRONIZAÇÃO CONCLUÍDA! ✅ ✅ ✅")
        print("="*80)
        print(f"📊 Estatísticas:")
        print(f"   ✅ Projetos sincronizados: {total_synced}")
        print(f"   ⏭️  Projetos ignorados: {total_ignored}")
        print(f"   ❌ Erros: {total_errors}")
        print(f"   📄 Páginas processadas: {page}")
        print("="*80)
        
        print(f"\n📋 Próximos passos:")
        print(f"   1. Teste o Kanban na aplicação")
        print(f"   2. Verifique se todos os projetos aparecem nas colunas corretas")
        print(f"   3. Valide que projetos 'Em Operação Assistida' estão na coluna correta")
        
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    synchronize_all_projects_robust()
