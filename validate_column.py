"""
Script para validar uma coluna específica do Kanban
Busca projetos do Zoho e compara com banco de dados
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Project
import utils

def obter_access_token():
    """Obtém token de acesso do Zoho"""
    return utils.obter_access_token_zoho()

def buscar_projetos_zoho(access_token):
    """Busca TODOS os projetos do Zoho (com paginação)"""
    from config import ZOHO_PORTAL_ID
    
    all_projects = []
    page = 1
    per_page = 50
    
    print("\n📡 Buscando projetos do Zoho API...")
    
    while True:
        url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
        params = {
            'page': page,
            'per_page': per_page,
            'last_modified_time': '2000-01-01T00:00:00Z'  # Pega todos os projetos
        }
        headers = {
            'Authorization': f'Zoho-oauthtoken {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            print(f"   Página {page}...", end=' ')
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # A API pode retornar diretamente a lista ou um objeto com 'projects'
            if isinstance(data, list):
                projects = data
            else:
                projects = data.get('projects', [])
            
            if not projects:
                print("(vazia)")
                break
            
            print(f"({len(projects)} projetos)")
            all_projects.extend(projects)
            
            # Verifica se tem mais páginas
            if len(projects) < per_page:
                break
            
            page += 1
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"\n❌ Erro 401: OAuth token expirado. Renovando...")
                access_token = obter_access_token()
                continue
            else:
                print(f"\n❌ Erro HTTP: {e}")
                if hasattr(e, 'response'):
                    print(f"   Resposta: {e.response.text}")
                break
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            break
    
    print(f"\n✅ Total de projetos do Zoho: {len(all_projects)}")
    return all_projects

def filtrar_projetos_por_coluna(projects, coluna_nome, mapeamento, owner_zpuid=None):
    """
    Filtra projetos que pertencem a uma coluna específica
    
    Args:
        projects: Lista de projetos do Zoho
        coluna_nome: Nome da coluna do Kanban
        mapeamento: Dicionário de mapeamento de colunas
        owner_zpuid: (Opcional) ZPUID do proprietário para filtrar. Ex: '2376502000000057291' para Giovani
    """
    config = mapeamento.get(coluna_nome, {})
    status_id_esperado = config.get('zohoStatusId')
    tags_esperadas = set(config.get('zohoTagsToAdd', []))
    
    projetos_filtrados = []
    
    for project in projects:
        # Filtrar por proprietário se especificado
        if owner_zpuid:
            project_owner_zpuid = project.get('owner', {}).get('zpuid', '')
            if project_owner_zpuid != owner_zpuid:
                continue
        
        # Verifica status ID
        project_status_id = str(project.get('status', {}).get('id', ''))
        if project_status_id != status_id_esperado:
            continue
        
        # Verifica tags
        project_tags = project.get('tags', [])
        project_tag_ids = {str(tag.get('id')) for tag in project_tags if tag.get('id')}
        
        # Se a coluna exige tags específicas, verifica se tem
        if tags_esperadas:
            if not tags_esperadas.issubset(project_tag_ids):
                continue
        else:
            # Se a coluna NÃO exige tags, verifica que não tem tags de outras colunas
            # (ex: "Em Operação Assistida" não deve ter tag de "Aguardando Encerramento")
            tags_conflitantes = set()
            for outra_coluna, outra_config in mapeamento.items():
                if outra_coluna != coluna_nome and outra_config.get('zohoStatusId') == status_id_esperado:
                    tags_conflitantes.update(outra_config.get('zohoTagsToAdd', []))
            
            if tags_conflitantes and tags_conflitantes.intersection(project_tag_ids):
                continue
        
        projetos_filtrados.append(project)
    
    return projetos_filtrados

def validar_coluna(coluna_nome, db_url, owner_zpuid=None):
    """
    Valida todos os projetos de uma coluna
    
    Args:
        coluna_nome: Nome da coluna do Kanban
        db_url: URL do banco PostgreSQL
        owner_zpuid: (Opcional) ZPUID do proprietário para filtrar. Ex: '2376502000000057291' para Giovani
    """
    print("="*100)
    print(f"🔍 VALIDANDO COLUNA: {coluna_nome}")
    print("="*100)
    
    # Carrega mapeamento
    mapeamento_path = os.path.join(os.path.dirname(__file__), 'mapeamento_colunas.json')
    with open(mapeamento_path, 'r', encoding='utf-8') as f:
        mapeamento = json.load(f)
    
    config = mapeamento.get(coluna_nome)
    if not config:
        print(f"❌ Coluna '{coluna_nome}' não encontrada no mapeamento!")
        return
    
    print(f"\n📋 Configuração da coluna:")
    print(f"   Status ID: {config.get('zohoStatusId')}")
    print(f"   Tags exigidas: {config.get('zohoTagsToAdd', [])}")
    if owner_zpuid:
        print(f"   Filtro proprietário: ZPUID {owner_zpuid}")
    
    # Busca projetos do Zoho
    access_token = obter_access_token()
    all_projects = buscar_projetos_zoho(access_token)
    
    # Filtra por coluna (e por proprietário se especificado)
    print(f"\n🔍 Filtrando projetos da coluna '{coluna_nome}'...")
    projetos_zoho = filtrar_projetos_por_coluna(all_projects, coluna_nome, mapeamento, owner_zpuid)
    
    print(f"✅ Projetos no Zoho na coluna '{coluna_nome}': {len(projetos_zoho)}")
    
    if not projetos_zoho:
        print(f"\n✅ Nenhum projeto encontrado nesta coluna no Zoho!")
        return
    
    # Busca projetos do banco
    print(f"\n💾 Conectando ao banco de dados...")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Compara projeto por projeto
    print(f"\n{'='*100}")
    print("📊 COMPARAÇÃO PROJETO POR PROJETO")
    print("="*100)
    
    projetos_corretos = 0
    projetos_incorretos = []
    
    for idx, zoho_project in enumerate(projetos_zoho, 1):
        project_id = zoho_project.get('id')
        project_name = zoho_project.get('name', 'Sem nome')
        
        # Busca no banco
        db_project = session.query(Project).filter(Project.id == project_id).first()
        
        if not db_project:
            print(f"\n⚠️  {idx}. {project_name}")
            print(f"   ID: {project_id}")
            print(f"   Status: NÃO EXISTE NO BANCO")
            projetos_incorretos.append({
                'id': project_id,
                'nome': project_name,
                'problema': 'Não existe no banco'
            })
            continue
        
        # Determina coluna pelo banco
        coluna_banco = utils.determinar_coluna_projeto_from_db(db_project)
        
        if coluna_banco == coluna_nome:
            print(f"✅ {idx}. {project_name}")
            projetos_corretos += 1
        else:
            print(f"❌ {idx}. {project_name}")
            print(f"   ID: {project_id}")
            print(f"   Zoho: '{coluna_nome}'")
            print(f"   Banco: '{coluna_banco}'")
            
            # Mostra diferenças
            zoho_tags = {str(tag.get('id')) for tag in zoho_project.get('tags', []) if tag.get('id')}
            db_tags = set()
            if db_project.tags:
                try:
                    db_tags_parsed = json.loads(db_project.tags)
                    for tag in db_tags_parsed:
                        if isinstance(tag, dict):
                            db_tags.add(str(tag.get('id', '')))
                except:
                    pass
            
            if zoho_tags != db_tags:
                print(f"   Tags Zoho: {zoho_tags}")
                print(f"   Tags Banco: {db_tags}")
            
            projetos_incorretos.append({
                'id': project_id,
                'nome': project_name,
                'problema': f"Banco mostra '{coluna_banco}' em vez de '{coluna_nome}'"
            })
    
    session.close()
    
    # Resumo
    print(f"\n{'='*100}")
    print("📈 RESUMO")
    print("="*100)
    print(f"✅ Projetos corretos: {projetos_corretos}/{len(projetos_zoho)}")
    print(f"❌ Projetos incorretos: {len(projetos_incorretos)}/{len(projetos_zoho)}")
    
    if projetos_incorretos:
        print(f"\n🔧 PROJETOS QUE PRECISAM SINCRONIZAÇÃO:")
        for projeto in projetos_incorretos[:10]:  # Mostra até 10
            print(f"   - {projeto['nome']} (ID: {projeto['id']})")
            print(f"     Problema: {projeto['problema']}")
        
        if len(projetos_incorretos) > 10:
            print(f"   ... e mais {len(projetos_incorretos) - 10} projetos")
        
        print(f"\n💡 SUGESTÃO:")
        print(f"   Execute 'python sync_projects_by_ids.py' passando os IDs acima para sincronizá-los")
    
    print(f"\n{'='*100}\n")
    
    return projetos_incorretos

if __name__ == '__main__':
    print("\n" + "="*100)
    print("🔍 VALIDAÇÃO DE COLUNA KANBAN")
    print("="*100 + "\n")
    
    # Lista colunas disponíveis
    mapeamento_path = os.path.join(os.path.dirname(__file__), 'mapeamento_colunas.json')
    with open(mapeamento_path, 'r', encoding='utf-8') as f:
        mapeamento = json.load(f)
    
    print("📋 Colunas disponíveis:")
    for idx, coluna in enumerate(mapeamento.keys(), 1):
        print(f"   {idx}. {coluna}")
    
    # Solicita dados
    print()
    coluna_nome = input("📝 Digite o nome da coluna para validar (padrão: Aguardando Onboarding): ").strip()
    if not coluna_nome:
        coluna_nome = "Aguardando Onboarding"
    
    db_url = input("📝 Cole a URL do PostgreSQL do Railway: ").strip()
    
    if not db_url:
        print("\n❌ URL do banco é obrigatória!")
        sys.exit(1)
    
    # Pergunta se quer filtrar por proprietário
    filtrar_owner = input("\n❓ Filtrar apenas projetos do Giovani? (S/n): ").strip().lower()
    owner_zpuid = '2376502000000057291' if filtrar_owner != 'n' else None  # Default: SIM
    
    if owner_zpuid:
        print("✅ Filtrando apenas projetos do Giovani (ZPUID: 2376502000000057291)")
    else:
        print("ℹ️ Considerando projetos de todos os proprietários")
    
    projetos_incorretos = validar_coluna(coluna_nome, db_url, owner_zpuid)
    
    print("\n✅ Validação concluída!")
    
    # Pergunta se quer sincronizar
    if projetos_incorretos:
        resposta = input("\n❓ Deseja sincronizar os projetos incorretos agora? (s/N): ").strip().lower()
        if resposta == 's':
            print("\n🔄 Sincronizando projetos...")
            
            # Reconfigura database para usar URL externa
            import database
            engine = create_engine(db_url)
            database.engine = engine
            database.Session = sessionmaker(bind=engine)
            
            from database import upsert_project
            
            sincronizados = 0
            erros = 0
            
            for projeto in projetos_incorretos:
                try:
                    # Busca dados atualizados do Zoho
                    access_token = obter_access_token()
                    from config import ZOHO_PORTAL_ID
                    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{projeto['id']}"
                    headers = {'Authorization': f'Zoho-oauthtoken {access_token}'}
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    zoho_data = response.json().get('projects', [{}])[0]
                    
                    # Sincroniza
                    upsert_project(zoho_data)
                    print(f"   ✅ {projeto['nome']}")
                    sincronizados += 1
                    
                except Exception as e:
                    print(f"   ❌ {projeto['nome']}: {e}")
                    erros += 1
            
            print(f"\n📊 Sincronização concluída:")
            print(f"   ✅ Sincronizados: {sincronizados}")
            print(f"   ❌ Erros: {erros}")
