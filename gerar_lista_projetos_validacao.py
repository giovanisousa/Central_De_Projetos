"""
Script para gerar arquivo CSV com lista de projetos para validação.
Filtra projetos dos GPs Giovani e willian.anjos que não estão Completed/Cancelado.
"""

import requests
import csv
import json
import time
from config import ZOHO_PORTAL_ID
import utils

# GPs para filtrar
GPS_PARA_FILTRAR = [
    "Giovani",
    "willian.anjos"
]

# Status a EXCLUIR
STATUS_EXCLUIDOS = [
    "Completed",
    "Cancelado"
]


def buscar_todos_projetos(access_token):
    """Busca todos os projetos do portal."""
    print("🔍 Buscando todos os projetos do portal...")
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects"
    
    todos_projetos = []
    index = 1
    range_size = 200
    
    while True:
        params = {
            "index": index,
            "range": range_size
        }
        
        print(f"   Buscando projetos {index} a {index + range_size - 1}...")
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Erro ao buscar projetos: {response.status_code}")
                break
            
            data = response.json()
            
            # A API retorna diretamente uma lista de projetos
            if isinstance(data, list):
                projetos = data
            else:
                projetos = data.get('projects', [])
            
            if not projetos:
                break
            
            todos_projetos.extend(projetos)
            print(f"   ✅ Encontrados {len(projetos)} projetos neste lote")
            
            if len(projetos) < range_size:
                break
            
            index += range_size
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Erro ao buscar projetos: {e}")
            break
    
    print(f"\n✅ Total de projetos encontrados: {len(todos_projetos)}\n")
    return todos_projetos


def filtrar_projetos(projetos, gps_lista, status_excluidos):
    """Filtra projetos pelos GPs e exclui status específicos."""
    print(f"🔍 Filtrando projetos...")
    print(f"   GPs: {', '.join(gps_lista)}")
    print(f"   Excluindo status: {', '.join(status_excluidos)}")
    
    projetos_filtrados = []
    
    for projeto in projetos:
        owner = projeto.get('owner', {})
        owner_name = owner.get('name', '').strip()
        
        # Verificar se é um dos GPs
        if owner_name in gps_lista:
            status = projeto.get('status', {})
            status_name = status.get('name', '').strip()
            
            # Excluir se estiver nos status excluídos
            if status_name in status_excluidos:
                continue
            
            projetos_filtrados.append({
                'id': projeto.get('id'),
                'name': projeto.get('name'),
                'owner': owner_name,
                'status': status_name,
                'layout_id': projeto.get('layout_id', ''),
                'created_time': projeto.get('created_time', ''),
                'start_date': projeto.get('start_date', ''),
                'end_date': projeto.get('end_date', '')
            })
    
    print(f"\n✅ Total de projetos filtrados: {len(projetos_filtrados)}\n")
    return projetos_filtrados


def salvar_csv(projetos, nome_arquivo):
    """Salva lista de projetos em arquivo CSV."""
    print(f"💾 Salvando projetos em {nome_arquivo}...")
    
    with open(nome_arquivo, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['id', 'name', 'owner', 'status', 'layout_id', 'created_time', 'start_date', 'end_date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for projeto in projetos:
            writer.writerow(projeto)
    
    print(f"✅ Arquivo CSV salvo com sucesso!\n")


def salvar_json(projetos, nome_arquivo):
    """Salva lista de projetos em arquivo JSON."""
    print(f"💾 Salvando projetos em {nome_arquivo}...")
    
    with open(nome_arquivo, 'w', encoding='utf-8') as jsonfile:
        json.dump(projetos, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"✅ Arquivo JSON salvo com sucesso!\n")


def main():
    """Função principal."""
    print("=" * 80)
    print("📋 GERAÇÃO DE LISTA DE PROJETOS PARA VALIDAÇÃO")
    print("=" * 80)
    print(f"GPs: {', '.join(GPS_PARA_FILTRAR)}")
    print(f"Excluindo status: {', '.join(STATUS_EXCLUIDOS)}")
    print("=" * 80)
    print()
    
    # Obter access token
    try:
        access_token = utils.obter_access_token()
        print("✅ Access token obtido com sucesso\n")
    except Exception as e:
        print(f"❌ Erro ao obter access token: {e}")
        return
    
    # Buscar todos os projetos
    todos_projetos = buscar_todos_projetos(access_token)
    
    if not todos_projetos:
        print("❌ Nenhum projeto encontrado. Abortando.")
        return
    
    # Filtrar projetos
    projetos_filtrados = filtrar_projetos(todos_projetos, GPS_PARA_FILTRAR, STATUS_EXCLUIDOS)
    
    if not projetos_filtrados:
        print("❌ Nenhum projeto encontrado após filtros. Abortando.")
        return
    
    # Gerar nomes de arquivos com timestamp
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    nome_csv = f"projetos_validacao_{timestamp}.csv"
    nome_json = f"projetos_validacao_{timestamp}.json"
    
    # Salvar em CSV
    salvar_csv(projetos_filtrados, nome_csv)
    
    # Salvar em JSON
    salvar_json(projetos_filtrados, nome_json)
    
    # Resumo
    print("=" * 80)
    print("📊 RESUMO")
    print("=" * 80)
    print(f"Total de projetos encontrados: {len(todos_projetos)}")
    print(f"Projetos filtrados (ativos): {len(projetos_filtrados)}")
    print()
    print(f"📁 Arquivo CSV: {nome_csv}")
    print(f"📁 Arquivo JSON: {nome_json}")
    print()
    
    # Estatísticas por GP
    print("📊 PROJETOS POR GP:")
    print("-" * 80)
    contagem_gp = {}
    for projeto in projetos_filtrados:
        gp = projeto['owner']
        contagem_gp[gp] = contagem_gp.get(gp, 0) + 1
    
    for gp, qtd in sorted(contagem_gp.items()):
        print(f"  {gp}: {qtd} projetos")
    
    print()
    
    # Estatísticas por status
    print("📊 PROJETOS POR STATUS:")
    print("-" * 80)
    contagem_status = {}
    for projeto in projetos_filtrados:
        status = projeto['status']
        contagem_status[status] = contagem_status.get(status, 0) + 1
    
    for status, qtd in sorted(contagem_status.items(), key=lambda x: x[1], reverse=True):
        print(f"  {status}: {qtd} projetos")
    
    print()
    print("=" * 80)
    print("✅ PROCESSO CONCLUÍDO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
