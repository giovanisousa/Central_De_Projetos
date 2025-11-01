# -*- coding: utf-8 -*-
"""
Módulo para sincronização de comentários do Zoho Projects com o banco de dados local.
"""

import requests
import time
from typing import List, Dict, Optional

from config import ZOHO_PORTAL_ID
from database import (
    upsert_comentario,
    get_db_connection,
    atualizar_data_ultimo_comentario,
    limpar_comentarios_projeto
)
from utils import obter_access_token as obter_access_token_zoho, _zp_base, _zp_headers


def buscar_comentarios_projeto_zoho(
    projeto_id: str, 
    access_token: str,
    page: int = 1,
    per_page: int = 100,
    sort_order: str = "DESC"
) -> Dict:
    """
    Busca comentários de um projeto específico no Zoho Projects via API.
    
    Args:
        projeto_id: ID do projeto no Zoho
        access_token: Token de acesso OAuth do Zoho
        page: Número da página (padrão: 1)
        per_page: Comentários por página (padrão: 100, máximo: 100)
        sort_order: Ordem de classificação - ASC ou DESC (padrão: DESC)
    
    Returns:
        Dict contendo:
            - comments: Lista de comentários
            - page_info: Informações de paginação
    
    Raises:
        requests.HTTPError: Se a requisição falhar
    """
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}/comments"
    headers = _zp_headers(access_token)
    
    # Monta parâmetros da requisição
    params = {
        'page': page,
        'per_page': min(per_page, 100),  # Máximo permitido pela API
        'sort_by': f'{sort_order}(created_time)'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        return {
            'comments': data.get('comments', []),
            'page_info': data.get('page_info', {})
        }
    
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            # Projeto pode não ter comentários ou não existir
            print(f"  ⚠️  Projeto {projeto_id} não encontrado ou sem comentários")
            return {'comments': [], 'page_info': {}}
        raise


def buscar_todos_comentarios_projeto(projeto_id: str, access_token: str) -> List[Dict]:
    """
    Busca TODOS os comentários de um projeto, percorrendo todas as páginas.
    
    Args:
        projeto_id: ID do projeto no Zoho
        access_token: Token de acesso OAuth do Zoho
    
    Returns:
        Lista com todos os comentários do projeto
    """
    todos_comentarios = []
    page = 1
    has_next_page = True
    
    print(f"  📝 Buscando comentários do projeto {projeto_id}...")
    
    while has_next_page:
        try:
            resultado = buscar_comentarios_projeto_zoho(
                projeto_id=projeto_id,
                access_token=access_token,
                page=page,
                per_page=100
            )
            
            comentarios_pagina = resultado['comments']
            page_info = resultado['page_info']
            
            if comentarios_pagina:
                todos_comentarios.extend(comentarios_pagina)
                print(f"    ✓ Página {page}: {len(comentarios_pagina)} comentários")
            
            # Verifica se há mais páginas
            has_next_page = page_info.get('has_next_page', 'false').lower() == 'true'
            page += 1
            
            # Pequeno delay para evitar rate limiting
            if has_next_page:
                # Polling: aguarda até 2s ou até que próxima página esteja disponível
                import time
                polling_timeout = 2
                polling_interval = 0.2
                polling_start = time.time()
                while has_next_page and time.time() - polling_start < polling_timeout:
                    print(f"[polling] aguardando próxima página... ({int((time.time()-polling_start)*1000)}ms)")
                    time.sleep(polling_interval)
        
        except Exception as e:
            print(f"    ❌ Erro ao buscar página {page}: {e}")
            break
    
    print(f"  ✅ Total de comentários encontrados: {len(todos_comentarios)}")
    return todos_comentarios


def sincronizar_comentarios_projeto(projeto_id: str, access_token: Optional[str] = None) -> int:
    """
    Sincroniza comentários de um projeto específico do Zoho para o banco local.
    Remove comentários deletados e adiciona/atualiza os existentes.
    
    Args:
        projeto_id: ID do projeto no Zoho
        access_token: Token de acesso OAuth (se None, será obtido automaticamente)
    
    Returns:
        int: Número de comentários sincronizados
    """
    if not access_token:
        access_token = obter_access_token_zoho()
    
    try:
        # Busca todos os comentários do projeto no Zoho
        comentarios = buscar_todos_comentarios_projeto(projeto_id, access_token)
        
        # Limpa os comentários existentes do projeto no banco local
        # Isso garante que comentários deletados no Zoho sejam removidos do banco
        limpar_comentarios_projeto(projeto_id)
        print(f"  🗑️  Comentários antigos do projeto {projeto_id} removidos do banco local")
        
        if not comentarios:
            print(f"  ℹ️  Nenhum comentário encontrado para o projeto {projeto_id}")
            # data_ultimo_comentario já foi zerado por limpar_comentarios_projeto()
            return 0
        
        # Insere cada comentário no banco
        comentarios_inseridos = 0
        for comentario in comentarios:
            try:
                upsert_comentario(comentario, projeto_id)
                comentarios_inseridos += 1
            except Exception as e:
                print(f"    ⚠️  Erro ao inserir comentário {comentario.get('id')}: {e}")
        
        print(f"  ✅ {comentarios_inseridos} comentários sincronizados para o projeto {projeto_id}")
        return comentarios_inseridos
    
    except Exception as e:
        print(f"  ❌ Erro ao sincronizar comentários do projeto {projeto_id}: {e}")
        import traceback
        traceback.print_exc()
        return 0


def sincronizar_comentarios_todos_projetos(forcar_ressincronizacao: bool = False) -> Dict:
    """
    Sincroniza comentários de TODOS os projetos ativos no banco de dados.
    
    Args:
        forcar_ressincronizacao: Se True, limpa comentários existentes antes de sincronizar
    
    Returns:
        Dict com estatísticas da sincronização:
            - total_projetos: Número de projetos processados
            - total_comentarios: Total de comentários sincronizados
            - projetos_com_erros: Lista de IDs de projetos que falharam
    """
    print("\n" + "="*80)
    print("🔄 INICIANDO SINCRONIZAÇÃO DE COMENTÁRIOS DE TODOS OS PROJETOS")
    print("="*80 + "\n")
    
    # Busca todos os projetos no banco
    conn = get_db_connection()
    from sqlalchemy import text
    result = conn.execute(text('SELECT id, nome FROM projects ORDER BY nome'))
    projetos = result.fetchall()
    conn.close()
    
    if not projetos:
        print("⚠️  Nenhum projeto encontrado no banco de dados")
        return {
            'total_projetos': 0,
            'total_comentarios': 0,
            'projetos_com_erros': []
        }
    
    # Obtém token uma única vez para todos os projetos
    access_token = obter_access_token_zoho()
    
    total_comentarios = 0
    projetos_com_erros = []
    
    for idx, projeto in enumerate(projetos, 1):
        projeto_id = projeto['id']
        projeto_nome = projeto['nome']
        
        print(f"\n[{idx}/{len(projetos)}] Projeto: {projeto_nome} (ID: {projeto_id})")
        
        try:
            # Se forçar ressincronização, limpa comentários existentes
            if forcar_ressincronizacao:
                comentarios_removidos = limpar_comentarios_projeto(projeto_id)
                if comentarios_removidos > 0:
                    print(f"  🗑️  {comentarios_removidos} comentários antigos removidos")
            
            # Sincroniza comentários
            comentarios_sincronizados = sincronizar_comentarios_projeto(projeto_id, access_token)
            total_comentarios += comentarios_sincronizados
            
            # Pequeno delay entre projetos para evitar rate limiting
            # Polling: aguarda até 2s ou até que próximo projeto esteja disponível
            import time
            polling_timeout = 2
            polling_interval = 0.3
            polling_start = time.time()
            while time.time() - polling_start < polling_timeout:
                print(f"[polling] aguardando próximo projeto... ({int((time.time()-polling_start)*1000)}ms)")
                time.sleep(polling_interval)
        
        except Exception as e:
            print(f"  ❌ ERRO ao processar projeto {projeto_id}: {e}")
            projetos_com_erros.append(projeto_id)
    
    # Resumo final
    print("\n" + "="*80)
    print("📊 RESUMO DA SINCRONIZAÇÃO")
    print("="*80)
    print(f"✅ Projetos processados: {len(projetos)}")
    print(f"📝 Total de comentários sincronizados: {total_comentarios}")
    print(f"❌ Projetos com erros: {len(projetos_com_erros)}")
    
    if projetos_com_erros:
        print(f"\n⚠️  IDs dos projetos com erros: {', '.join(projetos_com_erros)}")
    
    print("="*80 + "\n")
    
    return {
        'total_projetos': len(projetos),
        'total_comentarios': total_comentarios,
        'projetos_com_erros': projetos_com_erros
    }


def adicionar_comentario_projeto_zoho(
    projeto_id: str,
    conteudo: str,
    access_token: Optional[str] = None
) -> Optional[Dict]:
    """
    Adiciona um novo comentário a um projeto no Zoho Projects via API.
    
    Args:
        projeto_id: ID do projeto no Zoho
        conteudo: Conteúdo do comentário
        access_token: Token de acesso OAuth (se None, será obtido automaticamente)
    
    Returns:
        Dict com dados do comentário criado ou None em caso de erro
    """
    if not access_token:
        access_token = obter_access_token_zoho()
    
    url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{projeto_id}/comments"
    headers = _zp_headers(access_token)
    headers['Content-Type'] = 'application/json'
    
    payload = {
        'content': conteudo
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        # API v3 retorna o objeto dentro de 'comments' (array) ou direto
        data = response.json()
        
        # Tenta extrair o comentário do formato de resposta
        if isinstance(data, dict):
            if 'comments' in data and len(data['comments']) > 0:
                comentario_criado = data['comments'][0]
            elif 'id' in data:
                comentario_criado = data
            else:
                comentario_criado = data
        else:
            comentario_criado = data
        
        # Sincroniza o comentário no banco local imediatamente
        if comentario_criado and isinstance(comentario_criado, dict) and comentario_criado.get('id'):
            try:
                upsert_comentario(comentario_criado, projeto_id)
                print(f"✅ Comentário ID {comentario_criado.get('id')} adicionado ao projeto {projeto_id}")
            except Exception as db_error:
                print(f"⚠️ Comentário criado no Zoho mas erro ao salvar no BD: {db_error}")
        
        return comentario_criado
    
    except requests.HTTPError as e:
        print(f"❌ Erro HTTP ao adicionar comentário: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status: {e.response.status_code}")
            print(f"   Resposta: {e.response.text[:500]}")
        return None
    
    except Exception as e:
        print(f"❌ Erro inesperado ao adicionar comentário: {e}")
        import traceback
        traceback.print_exc()
        return None


# Script de teste (executar apenas se for o módulo principal)
if __name__ == '__main__':
    import sys
    
    print("="*80)
    print("SCRIPT DE SINCRONIZAÇÃO DE COMENTÁRIOS DO ZOHO PROJECTS")
    print("="*80)
    
    # Menu de opções
    print("\nOpções:")
    print("1. Sincronizar comentários de UM projeto específico")
    print("2. Sincronizar comentários de TODOS os projetos")
    print("3. Sincronizar comentários de TODOS os projetos (forçar ressincronização)")
    
    opcao = input("\nEscolha uma opção (1-3): ").strip()
    
    if opcao == '1':
        projeto_id = input("Digite o ID do projeto: ").strip()
        if projeto_id:
            resultado = sincronizar_comentarios_projeto(projeto_id)
            print(f"\n✅ Sincronização concluída: {resultado} comentários")
    
    elif opcao == '2':
        resultado = sincronizar_comentarios_todos_projetos(forcar_ressincronizacao=False)
    
    elif opcao == '3':
        confirmacao = input("⚠️  Isso removerá todos os comentários existentes. Confirma? (s/N): ").strip().lower()
        if confirmacao == 's':
            resultado = sincronizar_comentarios_todos_projetos(forcar_ressincronizacao=True)
        else:
            print("❌ Operação cancelada")
    
    else:
        print("❌ Opção inválida")
