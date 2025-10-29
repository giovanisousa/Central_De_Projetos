"""
Script para atualizar o template/layout de projetos específicos no Zoho Projects.

Atualiza todos os projetos onde o GP (owner) é:
- Giovani Sousa
- Willian dos Anjos

Para usar o template correto: layout_id = 2376502000005584766
"""

import requests
import time
import json
from config import ZOHO_PORTAL_ID
import utils

# Template/Layout ID correto
TEMPLATE_ID_CORRETO = "2376502000005584766"

# MODO TESTE: Deixe vazio [] para atualizar todos, ou adicione IDs específicos para testar
PROJETOS_TESTE = []  # Desativado, irá atualizar todos os projetos filtrados

# GPs que terão seus projetos atualizados
GPS_PARA_ATUALIZAR = [
    "Giovani",
    "willian.anjos"
]

# Status de projetos a EXCLUIR da atualização
STATUS_EXCLUIDOS = [
    "Completed",
    "Cancelado",
    "Concluído",
    "Finalizado"
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
    range_size = 200  # Máximo permitido pela API
    
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
                print(f"   Resposta: {response.text[:500]}")
                break
            
            data = response.json()
            
            # A API pode retornar como lista direta ou como objeto com 'projects'
            if isinstance(data, list):
                projetos = data
            elif isinstance(data, dict):
                projetos = data.get('projects', [])
            else:
                print(f"❌ Formato de resposta inesperado: {type(data)}")
                break
            
            if not projetos:
                break
            
            todos_projetos.extend(projetos)
            print(f"   ✅ Encontrados {len(projetos)} projetos neste lote")
            
            # Se retornou menos que o range, não há mais projetos
            if len(projetos) < range_size:
                break
            
            index += range_size
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"❌ Erro ao buscar projetos: {e}")
            break
    
    print(f"\n✅ Total de projetos encontrados: {len(todos_projetos)}\n")
    return todos_projetos


def filtrar_projetos_por_gp(projetos, gps_lista):
    """Filtra projetos pelos GPs especificados e exclui projetos concluídos/cancelados."""
    print(f"🔍 Filtrando projetos por GPs: {', '.join(gps_lista)}...")
    print(f"🔍 Excluindo projetos com status: {', '.join(STATUS_EXCLUIDOS)}...")
    
    # Se PROJETOS_TESTE está definido, filtrar apenas esses IDs
    if PROJETOS_TESTE:
        print(f"⚠️  MODO TESTE ATIVADO: Apenas {len(PROJETOS_TESTE)} projeto(s) será(ão) processado(s)")
    
    projetos_filtrados = []
    projetos_excluidos_status = 0
    
    for projeto in projetos:
        # Se modo teste, filtrar apenas os IDs especificados
        if PROJETOS_TESTE:
            if str(projeto.get('id')) not in PROJETOS_TESTE:
                continue
        
        owner = projeto.get('owner', {})
        owner_name = owner.get('name', '').strip()
        
        # Verificar se é um dos GPs alvo
        if owner_name in gps_lista:
            # Verificar status do projeto
            status = projeto.get('status', {})
            status_name = status.get('name', '').strip()
            
            # Excluir se for concluído/cancelado
            if status_name in STATUS_EXCLUIDOS:
                projetos_excluidos_status += 1
                continue
            
            projetos_filtrados.append({
                'id': projeto.get('id'),
                'name': projeto.get('name'),
                'owner': owner_name,
                'status': status_name,
                'layout_id': projeto.get('layout_id', 'Não definido')
            })
    
    print(f"✅ Encontrados {len(projetos_filtrados)} projetos ativos dos GPs especificados")
    if projetos_excluidos_status > 0:
        print(f"⏭️  Excluídos {projetos_excluidos_status} projetos concluídos/cancelados")
    print()
    return projetos_filtrados


def atualizar_template_projeto(access_token, projeto_id, template_id):
    """Atualiza o template/layout de um projeto específico."""
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}"
    
    # Formato correto conforme documentação do Zoho
    payload = {
        "layout": {
            "id": template_id
        }
    }
    
    try:
        response = requests.patch(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            return True, "Sucesso"
        else:
            return False, f"Status {response.status_code}: {response.text[:200]}"
    
    except Exception as e:
        return False, str(e)


def main():
    """Função principal."""
    print("=" * 80)
    print("🚀 ATUALIZAÇÃO DE TEMPLATE DE PROJETOS")
    print("=" * 80)
    print(f"Template ID a ser aplicado: {TEMPLATE_ID_CORRETO}")
    print(f"GPs alvo: {', '.join(GPS_PARA_ATUALIZAR)}")
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
    
    # Filtrar projetos pelos GPs
    projetos_para_atualizar = filtrar_projetos_por_gp(todos_projetos, GPS_PARA_ATUALIZAR)
    
    if not projetos_para_atualizar:
        print("❌ Nenhum projeto encontrado para os GPs especificados. Abortando.")
        return
    
    # Mostrar projetos que serão atualizados
    print("📋 PROJETOS QUE SERÃO ATUALIZADOS:")
    print("-" * 80)
    for i, proj in enumerate(projetos_para_atualizar, 1):
        print(f"{i:3d}. {proj['name']}")
        print(f"     ID: {proj['id']}")
        print(f"     GP: {proj['owner']}")
        print(f"     Status: {proj['status']}")
        print(f"     Layout atual: {proj['layout_id']}")
        print()
    
    # Confirmação
    print("=" * 80)
    resposta = input(f"\n⚠️  Deseja atualizar {len(projetos_para_atualizar)} projetos? (sim/não): ").strip().lower()
    
    if resposta not in ['sim', 's', 'yes', 'y']:
        print("\n❌ Operação cancelada pelo usuário.")
        return
    
    print("\n" + "=" * 80)
    print("🔄 INICIANDO ATUALIZAÇÃO DOS PROJETOS...")
    print("=" * 80)
    print()
    
    # Atualizar cada projeto
    sucessos = []
    erros = []
    
    for i, proj in enumerate(projetos_para_atualizar, 1):
        print(f"[{i}/{len(projetos_para_atualizar)}] Atualizando: {proj['name']}")
        
        # Verificar se já está com o template correto
        if str(proj['layout_id']) == str(TEMPLATE_ID_CORRETO):
            print(f"   ⏭️  Projeto já usa o template correto. Pulando...")
            sucessos.append(proj)
            continue
        
        sucesso, mensagem = atualizar_template_projeto(access_token, proj['id'], TEMPLATE_ID_CORRETO)
        
        if sucesso:
            print(f"   ✅ Template atualizado com sucesso!")
            sucessos.append(proj)
        else:
            print(f"   ❌ Erro: {mensagem}")
            erros.append({
                'projeto': proj,
                'erro': mensagem
            })
        
        # Rate limiting
        time.sleep(0.3)
        print()
    
    # Relatório final
    print("\n" + "=" * 80)
    print("📊 RELATÓRIO FINAL")
    print("=" * 80)
    print(f"✅ Sucessos: {len(sucessos)}")
    print(f"❌ Erros: {len(erros)}")
    print()
    
    if erros:
        print("❌ PROJETOS COM ERRO:")
        print("-" * 80)
        for erro in erros:
            print(f"  • {erro['projeto']['name']}")
            print(f"    ID: {erro['projeto']['id']}")
            print(f"    Erro: {erro['erro']}")
            print()
    
    # Salvar relatório em arquivo
    relatorio = {
        'data_execucao': time.strftime('%Y-%m-%d %H:%M:%S'),
        'template_id': TEMPLATE_ID_CORRETO,
        'gps_alvo': GPS_PARA_ATUALIZAR,
        'total_projetos': len(projetos_para_atualizar),
        'sucessos': len(sucessos),
        'erros': len(erros),
        'projetos_atualizados': [
            {
                'id': p['id'],
                'nome': p['name'],
                'gp': p['owner']
            } for p in sucessos
        ],
        'projetos_com_erro': [
            {
                'id': e['projeto']['id'],
                'nome': e['projeto']['name'],
                'gp': e['projeto']['owner'],
                'erro': e['erro']
            } for e in erros
        ]
    }
    
    nome_arquivo = f"relatorio_atualizacao_templates_{time.strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Relatório salvo em: {nome_arquivo}")
    print()
    print("=" * 80)
    print("✅ PROCESSO CONCLUÍDO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
