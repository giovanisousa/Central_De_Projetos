"""
Script para validar REVERSO: projetos no banco que aparecem em uma coluna
mas NÃO deveriam estar (não estão nesta coluna no Zoho)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Project
import utils

def validar_coluna_reverso(coluna_nome, db_url, projetos_corretos_zoho):
    """
    Valida que APENAS os projetos corretos aparecem na coluna do banco
    projetos_corretos_zoho: lista de IDs que DEVEM estar na coluna
    """
    print("="*100)
    print(f"🔍 VALIDAÇÃO REVERSA: Projetos no BANCO que aparecem em '{coluna_nome}'")
    print("="*100)
    
    # Conecta ao banco
    print(f"\n💾 Conectando ao banco de dados...")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Busca TODOS os projetos do banco
    print(f"\n📊 Buscando todos os projetos do banco...")
    all_projects = session.query(Project).all()
    print(f"✅ Total de projetos no banco: {len(all_projects)}")
    
    # Filtra projetos que aparecem nesta coluna segundo o banco
    print(f"\n🔍 Filtrando projetos que o banco classifica como '{coluna_nome}'...")
    projetos_banco_nesta_coluna = []
    
    for project in all_projects:
        coluna_determinada = utils.determinar_coluna_projeto_from_db(project)
        if coluna_determinada == coluna_nome:
            projetos_banco_nesta_coluna.append(project)
    
    print(f"✅ Projetos no banco classificados como '{coluna_nome}': {len(projetos_banco_nesta_coluna)}")
    
    # Compara com lista do Zoho
    ids_corretos = set(projetos_corretos_zoho)
    ids_no_banco = {p.id for p in projetos_banco_nesta_coluna}
    
    # Projetos que ESTÃO no banco mas NÃO deveriam (não estão no Zoho)
    ids_sobrando = ids_no_banco - ids_corretos
    
    # Projetos que DEVERIAM estar mas NÃO estão (estão no Zoho mas não no banco)
    ids_faltando = ids_corretos - ids_no_banco
    
    print(f"\n{'='*100}")
    print("📊 ANÁLISE")
    print("="*100)
    print(f"✅ Projetos CORRETOS (no Zoho E no banco): {len(ids_corretos & ids_no_banco)}")
    print(f"❌ Projetos SOBRANDO (no banco mas NÃO no Zoho): {len(ids_sobrando)}")
    print(f"⚠️  Projetos FALTANDO (no Zoho mas NÃO no banco): {len(ids_faltando)}")
    
    # Lista projetos sobrando (problema principal)
    if ids_sobrando:
        print(f"\n{'='*100}")
        print(f"❌ PROJETOS QUE NÃO DEVERIAM ESTAR EM '{coluna_nome}'")
        print("="*100)
        print(f"Esses {len(ids_sobrando)} projetos aparecem no Kanban em '{coluna_nome}' mas não estão nesta coluna no Zoho:\n")
        
        for project in projetos_banco_nesta_coluna:
            if project.id in ids_sobrando:
                print(f"❌ {project.nome}")
                print(f"   ID: {project.id}")
                print(f"   status_id: {project.status_id}")
                print(f"   status_atual: {project.status_atual}")
                
                # Parse tags
                if project.tags:
                    try:
                        tags_parsed = json.loads(project.tags)
                        tag_ids = [str(tag.get('id')) for tag in tags_parsed if isinstance(tag, dict)]
                        print(f"   tags: {tag_ids}")
                    except:
                        print(f"   tags: {project.tags[:100]}")
                else:
                    print(f"   tags: (sem tags)")
                
                # Tenta descobrir onde DEVERIA estar
                print(f"   💡 Para descobrir onde deveria estar, execute:")
                print(f"      python debug_single_project.py")
                print(f"      ID: {project.id}")
                print()
    
    # Lista projetos faltando (menos crítico, pois podem ter sido sincronizados)
    if ids_faltando:
        print(f"\n{'='*100}")
        print(f"⚠️  PROJETOS DO ZOHO QUE NÃO APARECEM NO BANCO")
        print("="*100)
        print(f"Esses {len(ids_faltando)} projetos estão em '{coluna_nome}' no Zoho mas não aparecem assim no banco:")
        print(f"(Esses precisam de sincronização)")
        print()
        for project_id in list(ids_faltando)[:5]:  # Mostra até 5
            print(f"   - ID: {project_id}")
    
    session.close()
    
    print(f"\n{'='*100}")
    print("📈 RESUMO FINAL")
    print("="*100)
    print(f"Projetos no Zoho: {len(ids_corretos)}")
    print(f"Projetos no Banco: {len(ids_no_banco)}")
    print(f"✅ Corretos: {len(ids_corretos & ids_no_banco)}")
    print(f"❌ Sobrando no banco: {len(ids_sobrando)}")
    print(f"⚠️  Faltando no banco: {len(ids_faltando)}")
    print()
    
    if ids_sobrando:
        print("🔧 AÇÃO NECESSÁRIA:")
        print(f"   {len(ids_sobrando)} projetos precisam ser sincronizados")
        print(f"   Execute o debug em cada um para descobrir a coluna correta")
    
    print(f"\n{'='*100}\n")
    
    return list(ids_sobrando)

if __name__ == '__main__':
    print("\n" + "="*100)
    print("🔍 VALIDAÇÃO REVERSA - Projetos que aparecem incorretamente em uma coluna")
    print("="*100 + "\n")
    
    # Para "Aguardando Onboarding", já sabemos os 8 IDs corretos do Zoho
    print("📋 Coluna: Aguardando Onboarding")
    print("✅ IDs corretos do Zoho (da validação anterior):")
    
    # IDs dos 8 projetos corretos
    ids_corretos = [
        '2376502000005828547',  # 1189 - Assemed Laudos Telerradiologia e Telemedicina - AP
        '2376502000005758112',  # 1212 - Amaral Costa Medicina Diagnóstica - AP
        '2376502000005544297',  # 1182 - Serviço de Radiodiagnóstico de Londrina - AP
        '2376502000005512303',  # 1185 - Ecocardio Vascular Serviço de Imagenologia - AP
        '2376502000005511003',  # 1183 - Ultra X Diagnósticos por Imagem - AP
        '2376502000005994875',  # 1165 - IDX - Instituto de Diagnóstico Por Imagem - NR/AP
        '2376502000005828025',  # 1200 - Bio Imagem – Ressonância Magnética - NR/AP
        '2376502000005705007',  # 1198 - Invasc - Instituto Vascular de Passo Fundo - AP
    ]
    
    for i, project_id in enumerate(ids_corretos, 1):
        print(f"   {i}. {project_id}")
    
    print(f"\n📊 Esperado: 8 projetos")
    print(f"📊 No Kanban: 28 projetos")
    print(f"❌ Diferença: 20 projetos sobrando")
    
    db_url = input("\n📝 Cole a URL do PostgreSQL do Railway: ").strip()
    
    if not db_url:
        print("\n❌ URL do banco é obrigatória!")
        sys.exit(1)
    
    ids_sobrando = validar_coluna_reverso("Aguardando Onboarding", db_url, ids_corretos)
    
    if ids_sobrando:
        resposta = input("\n❓ Deseja sincronizar os projetos incorretos agora? (s/N): ").strip().lower()
        if resposta == 's':
            print("\n🔄 Sincronizando projetos...")
            print("   (Isso pode demorar alguns minutos...)\n")
            
            # Reconfigura database para usar URL externa
            import database
            engine = create_engine(db_url)
            database.engine = engine
            database.Session = sessionmaker(bind=engine)
            
            from database import upsert_project
            import requests
            from config import ZOHO_PORTAL_ID
            
            def obter_access_token():
                import utils
                return utils.obter_access_token_zoho()
            
            sincronizados = 0
            erros = 0
            
            for idx, project_id in enumerate(ids_sobrando, 1):
                try:
                    # Busca dados atualizados do Zoho
                    access_token = obter_access_token()
                    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
                    headers = {'Authorization': f'Zoho-oauthtoken {access_token}'}
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    if isinstance(data, list):
                        zoho_data = data[0] if data else None
                    else:
                        zoho_data = data.get('projects', [{}])[0] if 'projects' in data else data
                    
                    if not zoho_data or not zoho_data.get('id'):
                        print(f"   ⚠️  {idx}/{len(ids_sobrando)}: ID {project_id} - Dados inválidos do Zoho")
                        erros += 1
                        continue
                    
                    # Sincroniza
                    upsert_project(zoho_data)
                    print(f"   ✅ {idx}/{len(ids_sobrando)}: {zoho_data.get('name', 'Sem nome')}")
                    sincronizados += 1
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        print(f"   ⚠️  Token expirado, renovando...")
                        # Tenta novamente com token renovado
                        try:
                            access_token = obter_access_token()
                            url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
                            headers = {'Authorization': f'Zoho-oauthtoken {access_token}'}
                            response = requests.get(url, headers=headers)
                            response.raise_for_status()
                            data = response.json()
                            zoho_data = data.get('projects', [{}])[0] if 'projects' in data else data
                            upsert_project(zoho_data)
                            print(f"   ✅ {idx}/{len(ids_sobrando)}: {zoho_data.get('name', 'Sem nome')}")
                            sincronizados += 1
                        except:
                            print(f"   ❌ {idx}/{len(ids_sobrando)}: ID {project_id} - Erro mesmo após renovar token")
                            erros += 1
                    else:
                        print(f"   ❌ {idx}/{len(ids_sobrando)}: ID {project_id} - Erro HTTP {e.response.status_code}")
                        erros += 1
                except Exception as e:
                    print(f"   ❌ {idx}/{len(ids_sobrando)}: ID {project_id} - {str(e)[:50]}")
                    erros += 1
            
            print(f"\n{'='*100}")
            print("📊 SINCRONIZAÇÃO CONCLUÍDA")
            print("="*100)
            print(f"✅ Sincronizados: {sincronizados}/{len(ids_sobrando)}")
            print(f"❌ Erros: {erros}/{len(ids_sobrando)}")
            print()
            
            if sincronizados > 0:
                print("💡 Recomendação: Execute a validação novamente para confirmar!")
    
    print("\n✅ Validação concluída!")
