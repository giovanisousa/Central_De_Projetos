import requests
import json
import sys

# Obter token
sys.path.insert(0, '.')
from utils import obter_access_token_zoho

# IDs dos projetos perdidos
projetos_perdidos = [
    ("1151 - Serviço de Diagnóstico Santa Paula - AP", "2376502000004257006"),
    ("1150 - Hospital e Clínica Santa Paula - AP", "2376502000004242191"),
    ("1143 - Clinica Tirol - NR/AP", "2376502000004231100"),
    ("1128 - Acesso Saúde Taguatinga - AP", "2376502000004208431"),
    ("Projeto registro de horas NÃO FATURÁVEIS", "2376502000004208211"),
    ("1139 - CDI Porto Ferreira - NR/AP", "2376502000004208003"),
    ("1142 - Hospital São Vicente de Paulo - AP", "2376502000004053440"),
    ("1141 - Imagem X - AP/NR (Sem OA)", "2376502000004053174"),
    ("1118 - DoctorClin - AP", "2376502000003928432"),
    ("1135 - IMR - INSTITUTO MARQUES DE RADIOLOGIA", "2376502000003782093"),
    ("Registros treinamentos - HM Diagnósticos", "2376502000003640439"),
]

PROPRIETARIOS_VALIDOS = ['Giovani', 'willian.anjos']
STATUS_EXCLUIDOS = ['1', '2', '3']  # IDs dos status Cancelado/Finalizado/Concluído

token = obter_access_token_zoho()
headers = {'Authorization': f'Zoho-oauthtoken {token}'}
base_url = "https://projectsapi.zoho.com/restapi/portal/1060003668/projects"

print("="*100)
print("MOTIVO DOS PROJETOS TEREM SIDO IGNORADOS:")
print("="*100)

motivos = {}
for nome, project_id in projetos_perdidos:
    try:
        url = f"{base_url}/{project_id}/"
        resp = requests.get(url, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            project = data.get('projects', [{}])[0]
            owner_name = project.get('owner_name', 'N/A')
            status_name = project.get('status', 'N/A')
            status_id = project.get('status_id', 'N/A')
            
            # Determinar motivo
            proprietario_invalido = owner_name not in PROPRIETARIOS_VALIDOS
            status_excluido = str(status_id) in STATUS_EXCLUIDOS
            
            if proprietario_invalido and status_excluido:
                motivo = f"❌ PROPRIETÁRIO INVÁLIDO ({owner_name}) + STATUS EXCLUÍDO ({status_name})"
            elif proprietario_invalido:
                motivo = f"❌ PROPRIETÁRIO INVÁLIDO ({owner_name})"
            elif status_excluido:
                motivo = f"❌ STATUS EXCLUÍDO ({status_name})"
            else:
                motivo = f"⚠️ DEVERIA TER SIDO SALVO! Proprietário: {owner_name}, Status: {status_name}"
            
            motivos[motivo] = motivos.get(motivo, 0) + 1
            
            print(f"\n{nome[:70]:70} | {motivo}")
        else:
            print(f"\n{nome[:70]:70} | ❌ ERRO API: {resp.status_code}")
    except Exception as e:
        print(f"\n{nome[:70]:70} | ❌ ERRO: {str(e)}")

print("\n" + "="*100)
print("RESUMO DOS MOTIVOS:")
print("="*100)
for motivo, count in sorted(motivos.items(), key=lambda x: -x[1]):
    print(f"{count:2} projetos: {motivo}")
