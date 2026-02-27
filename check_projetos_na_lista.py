import requests
import sys

sys.path.insert(0, '.')
from utils import obter_access_token_zoho

# IDs dos projetos perdidos
ids_perdidos = {
    "2376502000004257006", "2376502000004242191", "2376502000004231100",
    "2376502000004208431", "2376502000004208211", "2376502000004208003",
    "2376502000004053440", "2376502000004053174", "2376502000003928432",
    "2376502000003782093", "2376502000003640439"
}

token = obter_access_token_zoho()
headers = {'Authorization': f'Zoho-oauthtoken {token}'}
base_url = "https://projectsapi.zoho.com/restapi/portal/1060003668/projects"

print("="*100)
print("VERIFICANDO SE PROJETOS AINDA APARECEM NA LISTA GERAL DA API:")
print("="*100)

encontrados_na_lista = set()
index = 1
while True:
    params = {'index': index, 'range': 100}
    resp = requests.get(base_url, headers=headers, params=params, timeout=30)
    
    if resp.status_code != 200:
        print(f"\n❌ Erro na página {index}: {resp.status_code}")
        break
    
    data = resp.json()
    projects = data.get('projects', [])
    
    if not projects:
        break
    
    print(f"\nPágina {index}: {len(projects)} projetos")
    
    for project in projects:
        project_id = str(project['id'])
        if project_id in ids_perdidos:
            nome = project.get('name', 'N/A')
            owner = project.get('owner_name', 'N/A')
            status = project.get('status', 'N/A')
            print(f"  ✓ ENCONTRADO: {nome[:60]} | Proprietário: {owner} | Status: {status}")
            encontrados_na_lista.add(project_id)
    
    index += 100

print("\n" + "="*100)
print("RESULTADO:")
print("="*100)
print(f"Projetos perdidos: {len(ids_perdidos)}")
print(f"Encontrados na lista geral: {len(encontrados_na_lista)}")
print(f"NÃO encontrados (realmente deletados/sem acesso): {len(ids_perdidos - encontrados_na_lista)}")

if ids_perdidos - encontrados_na_lista:
    print("\nIDs não encontrados em nenhuma busca:")
    for id_perdido in sorted(ids_perdidos - encontrados_na_lista):
        print(f"  - {id_perdido}")
