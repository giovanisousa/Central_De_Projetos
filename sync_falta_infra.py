"""
Sincroniza todos os projetos de uma lista de IDs
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database

def obter_access_token():
    import utils
    return utils.obter_access_token_zoho()

# Lista de IDs para sincronizar (Falta Liberar Servidor Infra)
ids_para_sincronizar = [
    '2376502000006322069',  # 9842 - Teste de projeto - NR/AP
    '2376502000006294245',  # 9851 - ultimo - AP
    '2376502000005824705',  # 1195 - Hospital de Clínicas de Carazinho - AP
    '2376502000005993043',  # 1208 -Diagmed Centro de Diagnostico em Medicina Ltda - AP
    '2376502000006264023',  # 1211 - Clinica Start Diagnósticos - AP
    '2376502000005542081',  # 0548 - Med-X Serviços de Diagnóstico Por Imagem - NR/AP
    '2376502000005235445',  # 1117 - Unica Imagem - NR/AP
    '2376502000003549073',  # 1119 - Policlínica Vida Paraíba - AP
    '2376502000005726003',  # 1192 - Viavita Serviços Médicos - NR/AP
    '2376502000005824904',  # 1205 - RAIO X LAGOS DIAGNÓSTICOS POR IMAGEM - NR/AP
    '2376502000005705146',  # 1194 - Santa Cecília - Centro de Diagnósticos - AP
    '2376502000004257006',  # 1151 - Serviço de Diagnóstico Santa Paula - AP
    '2376502000004242191',  # 1150 - Hospital e Clínica Santa Paula - AP
    '2376502000004208431',  # 1128 - Acesso Saúde Taguatinga - AP
    '2376502000003459595',  # 1120 - Diagnósticos Via Imagem - NR/AP (SEM OA)
    '2376502000004208003',  # 1139 - CDI Porto Ferreira - NR/AP
]

print("="*100)
print("🔄 SINCRONIZAÇÃO DE PROJETOS")
print("="*100)
print(f"\nTotal de projetos a sincronizar: {len(ids_para_sincronizar)}")
print()

db_url = input("📝 Cole a URL do PostgreSQL do Railway: ").strip()

if not db_url:
    print("\n❌ URL do banco é obrigatória!")
    sys.exit(1)

# Reconfigura database para usar URL externa
print("\n🔧 Reconfigurando database...")
engine = create_engine(db_url)
database.engine = engine
database.Session = sessionmaker(bind=engine)

from database import upsert_project
from config import ZOHO_PORTAL_ID

print("\n🔄 Iniciando sincronização...")
print("   (Isso pode demorar alguns minutos...)\n")

sincronizados = 0
erros = 0

for idx, project_id in enumerate(ids_para_sincronizar, 1):
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
            print(f"   ⚠️  {idx}/{len(ids_para_sincronizar)}: ID {project_id} - Dados inválidos do Zoho")
            erros += 1
            continue
        
        # Sincroniza
        upsert_project(zoho_data)
        
        # Mostra info
        nome = zoho_data.get('name', 'Sem nome')
        status_nome = zoho_data.get('status', {}).get('name', 'Sem status')
        tags = zoho_data.get('tags', [])
        tag_names = [tag.get('name', 'Sem nome') for tag in tags if isinstance(tag, dict)]
        
        print(f"   ✅ {idx}/{len(ids_para_sincronizar)}: {nome}")
        print(f"      Status: {status_nome}")
        if tag_names:
            print(f"      Tags: {', '.join(tag_names)}")
        
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
                print(f"   ✅ {idx}/{len(ids_para_sincronizar)}: {zoho_data.get('name', 'Sem nome')}")
                sincronizados += 1
            except:
                print(f"   ❌ {idx}/{len(ids_para_sincronizar)}: ID {project_id} - Erro mesmo após renovar token")
                erros += 1
        elif e.response.status_code == 410:
            print(f"   ⚠️  {idx}/{len(ids_para_sincronizar)}: ID {project_id} - Projeto excluído no Zoho (410)")
            erros += 1
        else:
            print(f"   ❌ {idx}/{len(ids_para_sincronizar)}: ID {project_id} - Erro HTTP {e.response.status_code}")
            erros += 1
    except Exception as e:
        print(f"   ❌ {idx}/{len(ids_para_sincronizar)}: ID {project_id} - {str(e)[:50]}")
        erros += 1

print(f"\n{'='*100}")
print("📊 SINCRONIZAÇÃO CONCLUÍDA")
print("="*100)
print(f"✅ Sincronizados: {sincronizados}/{len(ids_para_sincronizar)}")
print(f"❌ Erros: {erros}/{len(ids_para_sincronizar)}")
print()

if sincronizados > 0:
    print("💡 Agora execute novamente o check_falta_infra.py para verificar!")

print("\n✅ Concluído!")
