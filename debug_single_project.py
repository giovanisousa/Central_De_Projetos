"""
Script para debugar sincronização de um projeto específico
Compara dados do Zoho com dados do banco
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def obter_access_token():
    """Obtém token de acesso do Zoho"""
    import utils
    return utils.obter_access_token_zoho()

def buscar_projeto_zoho(project_id, access_token):
    """Busca projeto específico na API do Zoho"""
    from config import ZOHO_PORTAL_ID
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('projects', [{}])[0] if 'projects' in data else data
    except Exception as e:
        print(f"❌ Erro ao buscar projeto do Zoho: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Resposta: {e.response.text}")
        return None

def comparar_projeto(project_id, db_url):
    """Compara projeto do Zoho com banco de dados"""
    # Import Project aqui para não conflitar
    from database import Project
    
    print("="*100)
    print(f"🔍 DEBUGANDO PROJETO: {project_id}")
    print("="*100)
    
    # Busca do Zoho
    print("\n📡 Buscando projeto do Zoho API...")
    access_token = obter_access_token()
    zoho_data = buscar_projeto_zoho(project_id, access_token)
    
    if not zoho_data:
        print("❌ Não foi possível buscar dados do Zoho")
        return
    
    print(f"\n✅ Dados do Zoho:")
    print(f"   Nome: {zoho_data.get('name')}")
    print(f"   Status ID: {zoho_data.get('status', {}).get('id')}")
    print(f"   Status Nome: {zoho_data.get('status', {}).get('name')}")
    
    # Tags do Zoho
    zoho_tags = zoho_data.get('tags', [])
    print(f"\n   Tags ({len(zoho_tags)} tags):")
    if zoho_tags:
        for tag in zoho_tags:
            print(f"      - {tag.get('name')} (ID: {tag.get('id')})")
    else:
        print(f"      (sem tags)")
    
    # Busca do banco
    print(f"\n💾 Buscando projeto do banco de dados...")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    db_project = session.query(Project).filter(Project.id == project_id).first()
    
    if not db_project:
        print("❌ Projeto não encontrado no banco de dados")
        session.close()
        return
    
    print(f"\n✅ Dados do Banco:")
    print(f"   Nome: {db_project.nome}")
    print(f"   status_id: {db_project.status_id}")
    print(f"   status_atual: {db_project.status_atual}")
    
    # Tags do banco
    print(f"\n   Tags (coluna tags):")
    if db_project.tags:
        try:
            db_tags = json.loads(db_project.tags)
            print(f"      ({len(db_tags)} tags):")
            for tag in db_tags:
                if isinstance(tag, dict):
                    print(f"      - {tag.get('name')} (ID: {tag.get('id')})")
                else:
                    print(f"      - {tag}")
        except Exception as e:
            print(f"      ❌ Erro ao parsear tags: {e}")
            print(f"      Valor bruto: {db_project.tags[:200]}")
    else:
        print(f"      (sem tags)")
    
    # Comparação
    print(f"\n{'='*100}")
    print("📊 COMPARAÇÃO")
    print("="*100)
    
    # Status ID
    zoho_status_id = str(zoho_data.get('status', {}).get('id', ''))
    db_status_id = str(db_project.status_id or '')
    
    if zoho_status_id == db_status_id:
        print(f"✅ status_id CORRETO: {db_status_id}")
    else:
        print(f"❌ status_id DIVERGENTE:")
        print(f"   Zoho: {zoho_status_id}")
        print(f"   Banco: {db_status_id}")
    
    # Status Nome
    zoho_status_name = zoho_data.get('status', {}).get('name', '')
    if zoho_status_name == db_project.status_atual:
        print(f"✅ status_atual CORRETO: {db_project.status_atual}")
    else:
        print(f"❌ status_atual DIVERGENTE:")
        print(f"   Zoho: {zoho_status_name}")
        print(f"   Banco: {db_project.status_atual}")
    
    # Tags
    zoho_tag_ids = {str(tag.get('id')) for tag in zoho_tags if tag.get('id')}
    db_tag_ids = set()
    
    if db_project.tags:
        try:
            db_tags_parsed = json.loads(db_project.tags)
            for tag in db_tags_parsed:
                if isinstance(tag, dict):
                    db_tag_ids.add(str(tag.get('id', '')))
                else:
                    db_tag_ids.add(str(tag))
        except:
            pass
    
    if zoho_tag_ids == db_tag_ids:
        print(f"✅ Tags CORRETAS: {len(db_tag_ids)} tags")
    else:
        print(f"❌ Tags DIVERGENTES:")
        print(f"   Tags no Zoho mas NÃO no banco: {zoho_tag_ids - db_tag_ids}")
        print(f"   Tags no banco mas NÃO no Zoho: {db_tag_ids - zoho_tag_ids}")
    
    # Mapeamento esperado
    print(f"\n{'='*100}")
    print("🎯 MAPEAMENTO KANBAN")
    print("="*100)
    
    # Carrega mapeamento
    mapeamento_path = os.path.join(os.path.dirname(__file__), 'mapeamento_colunas.json')
    with open(mapeamento_path, 'r', encoding='utf-8') as f:
        mapeamento = json.load(f)
    
    # Encontra coluna esperada baseado no Zoho
    print(f"\n📍 Com base nos dados do ZOHO:")
    print(f"   Status ID: {zoho_status_id}")
    print(f"   Tag IDs: {zoho_tag_ids}")
    
    for coluna, config in mapeamento.items():
        if config.get('zohoStatusId') == zoho_status_id:
            tags_required = set(config.get('zohoTagsToAdd', []))
            if tags_required:
                if tags_required.issubset(zoho_tag_ids):
                    print(f"\n   ✅ DEVE estar em: '{coluna}'")
                    print(f"      (status_id={zoho_status_id} + tags={tags_required})")
                    break
            else:
                print(f"\n   ✅ DEVE estar em: '{coluna}'")
                print(f"      (status_id={zoho_status_id}, sem tags específicas)")
                break
    
    # Encontra coluna atual baseado no banco
    import utils
    coluna_atual = utils.determinar_coluna_projeto_from_db(db_project)
    print(f"\n📍 Com base nos dados do BANCO:")
    print(f"   Coluna determinada: '{coluna_atual}'")
    
    session.close()
    
    print(f"\n{'='*100}")
    print("🔧 AÇÕES NECESSÁRIAS")
    print("="*100)
    
    if zoho_status_id != db_status_id or zoho_tag_ids != db_tag_ids:
        print("\n❌ PROJETO PRECISA SER SINCRONIZADO")
        print("\nVou tentar sincronizar este projeto agora...")
        
        # ✅ Reconfigura database.py para usar a URL externa
        print(f"\n🔧 Reconfigurando database.py para usar URL externa...")
        import database
        database.engine = create_engine(db_url)
        database.Session = sessionmaker(bind=database.engine)
        
        # Tenta sincronizar
        from database import upsert_project
        try:
            print("\n🔄 Chamando upsert_project()...")
            upsert_project(zoho_data)  # ✅ Agora usa a URL externa
            
            print("✅ Sincronização executada!")
            
            # Verifica novamente
            Session = sessionmaker(bind=create_engine(db_url))
            session_verify = Session()
            from database import Project
            
            db_project_new = session_verify.query(Project).filter(Project.id == project_id).first()
            print(f"\n📋 Verificando dados atualizados no banco:")
            print(f"   status_id: {db_project_new.status_id}")
            print(f"   status_atual: {db_project_new.status_atual}")
            
            # Parse tags
            if db_project_new.tags:
                try:
                    tags_updated = json.loads(db_project_new.tags)
                    print(f"   tags ({len(tags_updated)} tags):")
                    for tag in tags_updated[:3]:  # Mostra até 3 tags
                        if isinstance(tag, dict):
                            print(f"      - {tag.get('name')} (ID: {tag.get('id')})")
                except:
                    print(f"   tags (erro ao parsear): {db_project_new.tags[:100]}")
            else:
                print(f"   tags: (sem tags)")
            
            import utils
            coluna_nova = utils.determinar_coluna_projeto_from_db(db_project_new)
            print(f"\n   Coluna Kanban agora: '{coluna_nova}'")
            
            session_verify.close()
            
        except Exception as e:
            print(f"\n❌ Erro ao sincronizar: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n✅ PROJETO JÁ ESTÁ CORRETO NO BANCO")
    
    print(f"\n{'='*100}\n")

if __name__ == '__main__':
    print("\n" + "="*100)
    print("🐛 DEBUG DE SINCRONIZAÇÃO - PROJETO ESPECÍFICO")
    print("="*100 + "\n")
    
    # Solicita dados
    project_id = input("📝 Digite o ID do projeto para debugar: ").strip()
    db_url = input("📝 Cole a URL do PostgreSQL do Railway: ").strip()
    
    if not project_id or not db_url:
        print("\n❌ Projeto ID e URL do banco são obrigatórios!")
        sys.exit(1)
    
    comparar_projeto(project_id, db_url)
    
    print("\n✅ Debug concluído!")
