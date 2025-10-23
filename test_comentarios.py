# -*- coding: utf-8 -*-
"""
Script de teste para validar as funcionalidades de comentários.
Execute este script APÓS atualizar o token OAuth com o escopo de comentários.
"""

import sys
from datetime import datetime
from database import (
    get_comentarios_projeto,
    get_ultimo_comentario_projeto,
    contar_comentarios_projeto,
    get_db_connection
)
from sync_comentarios import (
    sincronizar_comentarios_projeto,
    adicionar_comentario_projeto_zoho
)


def exibir_separador(titulo=""):
    """Exibe um separador visual bonito."""
    print("\n" + "="*80)
    if titulo:
        print(f"  {titulo}")
        print("="*80)
    print()


def listar_projetos_disponiveis():
    """Lista os primeiros 10 projetos do banco para teste."""
    print("📋 Projetos disponíveis para teste:\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, cliente FROM projects LIMIT 10')
    projetos = cursor.fetchall()
    conn.close()
    
    if not projetos:
        print("❌ Nenhum projeto encontrado no banco de dados")
        print("   Execute 'python sync_zoho.py' primeiro para sincronizar projetos")
        return None
    
    for idx, projeto in enumerate(projetos, 1):
        print(f"{idx}. {projeto['nome']}")
        print(f"   Cliente: {projeto['cliente']}")
        print(f"   ID: {projeto['id']}")
        print()
    
    return projetos


def teste_sincronizacao_comentarios(projeto_id):
    """Testa a sincronização de comentários de um projeto."""
    exibir_separador("🔄 TESTE 1: Sincronizar Comentários do Zoho")
    
    print(f"Projeto ID: {projeto_id}")
    print("Iniciando sincronização...\n")
    
    try:
        total = sincronizar_comentarios_projeto(projeto_id)
        
        if total > 0:
            print(f"\n✅ SUCESSO: {total} comentários sincronizados")
            return True
        else:
            print(f"\n⚠️  Nenhum comentário encontrado para este projeto")
            print("   Isto pode ser normal se o projeto não tem comentários ainda")
            return True
    
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print("\nPossíveis causas:")
        print("1. Token OAuth sem escopo ZohoProjects.comments.ALL")
        print("2. Projeto ID inválido")
        print("3. Problemas de conexão com API do Zoho")
        return False


def teste_buscar_comentarios_banco(projeto_id):
    """Testa a busca de comentários no banco de dados."""
    exibir_separador("📖 TESTE 2: Buscar Comentários do Banco de Dados")
    
    print(f"Projeto ID: {projeto_id}\n")
    
    # Conta total de comentários
    total = contar_comentarios_projeto(projeto_id)
    print(f"Total de comentários: {total}\n")
    
    if total == 0:
        print("⚠️  Nenhum comentário encontrado no banco")
        print("   Execute o Teste 1 primeiro para sincronizar")
        return False
    
    # Busca os últimos 5 comentários
    print("📝 Últimos 5 comentários:\n")
    comentarios = get_comentarios_projeto(projeto_id, limit=5)
    
    for idx, comentario in enumerate(comentarios, 1):
        print(f"{idx}. {comentario['autor_nome']}")
        print(f"   Data: {comentario['data_criacao']}")
        print(f"   Via: {comentario['adicionado_via']}")
        print(f"   Conteúdo: {comentario['conteudo'][:100]}...")
        print()
    
    # Busca o comentário mais recente
    ultimo = get_ultimo_comentario_projeto(projeto_id)
    if ultimo:
        print("🆕 Comentário mais recente:")
        print(f"   Autor: {ultimo['autor_nome']}")
        print(f"   Data: {ultimo['data_criacao']}")
        print(f"   Conteúdo: {ultimo['conteudo'][:150]}")
        print()
    
    print("✅ SUCESSO: Comentários recuperados do banco")
    return True


def teste_adicionar_comentario(projeto_id):
    """Testa a adição de um novo comentário via API."""
    exibir_separador("➕ TESTE 3: Adicionar Novo Comentário via API")
    
    print(f"Projeto ID: {projeto_id}\n")
    
    # Solicita confirmação
    print("⚠️  ATENÇÃO: Isto adicionará um comentário REAL ao projeto no Zoho!")
    resposta = input("Deseja continuar? (s/N): ").strip().lower()
    
    if resposta != 's':
        print("❌ Teste cancelado pelo usuário")
        return False
    
    # Cria comentário de teste
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conteudo = f"🧪 Comentário de teste automático - {timestamp}"
    
    print(f"\nAdicionando comentário: '{conteudo}'")
    
    try:
        comentario = adicionar_comentario_projeto_zoho(projeto_id, conteudo)
        
        if comentario and comentario.get('id'):
            print(f"\n✅ SUCESSO: Comentário adicionado")
            print(f"   ID: {comentario['id']}")
            print(f"   Conteúdo: {comentario.get('content', conteudo)}")
            
            # Verifica se foi salvo no banco
            print("\nVerificando se foi salvo no banco...")
            comentarios = get_comentarios_projeto(projeto_id, limit=1)
            if comentarios and comentarios[0]['id'] == comentario['id']:
                print("✅ Comentário sincronizado no banco local")
            else:
                print("⚠️  Comentário não encontrado no banco (pode demorar)")
            
            return True
        else:
            print(f"\n⚠️  Comentário criado mas sem ID na resposta")
            return False
    
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print("\nPossíveis causas:")
        print("1. Token OAuth sem escopo ZohoProjects.comments.ALL")
        print("2. Projeto ID inválido")
        print("3. Permissões insuficientes no projeto")
        return False


def teste_verificar_data_ultimo_comentario(projeto_id):
    """Verifica se a data do último comentário está atualizada no projeto."""
    exibir_separador("📅 TESTE 4: Verificar Data do Último Comentário")
    
    print(f"Projeto ID: {projeto_id}\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT nome, data_ultimo_comentario FROM projects WHERE id = ?',
        (projeto_id,)
    )
    projeto = cursor.fetchone()
    conn.close()
    
    if not projeto:
        print("❌ Projeto não encontrado no banco")
        return False
    
    print(f"Projeto: {projeto['nome']}")
    print(f"Data do último comentário: {projeto['data_ultimo_comentario']}")
    print()
    
    # Busca o comentário mais recente do banco
    ultimo_comentario = get_ultimo_comentario_projeto(projeto_id)
    
    if ultimo_comentario:
        print(f"Último comentário no banco:")
        print(f"   Autor: {ultimo_comentario['autor_nome']}")
        print(f"   Data: {ultimo_comentario['data_criacao']}")
        print()
        
        # Verifica consistência
        if projeto['data_ultimo_comentario'] == ultimo_comentario['data_criacao']:
            print("✅ SUCESSO: Data do último comentário está consistente")
            return True
        else:
            print("⚠️  AVISO: Data do último comentário está inconsistente")
            print(f"   Projeto: {projeto['data_ultimo_comentario']}")
            print(f"   Comentário: {ultimo_comentario['data_criacao']}")
            return False
    else:
        if projeto['data_ultimo_comentario'] is None:
            print("✅ SUCESSO: Projeto sem comentários (data NULL)")
            return True
        else:
            print("⚠️  AVISO: Projeto tem data mas sem comentários no banco")
            return False


def menu_principal():
    """Menu principal do script de testes."""
    exibir_separador("🧪 SCRIPT DE TESTE - FUNCIONALIDADES DE COMENTÁRIOS")
    
    print("Este script testa as funcionalidades de comentários do sistema.\n")
    print("Escolha uma opção:\n")
    print("1. Listar projetos disponíveis")
    print("2. Executar TODOS os testes em um projeto")
    print("3. Executar testes individuais")
    print("0. Sair\n")
    
    opcao = input("Opção: ").strip()
    return opcao


def executar_todos_testes(projeto_id):
    """Executa todos os testes em sequência."""
    exibir_separador("🚀 EXECUTANDO TODOS OS TESTES")
    
    resultados = {
        'Sincronização': False,
        'Busca no Banco': False,
        'Adicionar Comentário': False,
        'Verificar Data': False
    }
    
    # Teste 1: Sincronização
    resultados['Sincronização'] = teste_sincronizacao_comentarios(projeto_id)
    
    # Teste 2: Busca no banco
    if resultados['Sincronização']:
        resultados['Busca no Banco'] = teste_buscar_comentarios_banco(projeto_id)
    
    # Teste 3: Adicionar comentário
    resultados['Adicionar Comentário'] = teste_adicionar_comentario(projeto_id)
    
    # Teste 4: Verificar data
    resultados['Verificar Data'] = teste_verificar_data_ultimo_comentario(projeto_id)
    
    # Resumo final
    exibir_separador("📊 RESUMO DOS TESTES")
    
    for teste, resultado in resultados.items():
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{teste}: {status}")
    
    total_passou = sum(1 for r in resultados.values() if r)
    total_testes = len(resultados)
    
    print(f"\nTotal: {total_passou}/{total_testes} testes passaram")
    
    if total_passou == total_testes:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os logs acima.")


def main():
    """Função principal."""
    while True:
        opcao = menu_principal()
        
        if opcao == '0':
            print("\n👋 Encerrando...")
            break
        
        elif opcao == '1':
            listar_projetos_disponiveis()
            input("\nPressione ENTER para continuar...")
        
        elif opcao == '2':
            projetos = listar_projetos_disponiveis()
            if projetos:
                escolha = input("\nEscolha o número do projeto (1-10) ou digite o ID: ").strip()
                
                try:
                    # Tenta interpretar como número da lista
                    if escolha.isdigit() and 1 <= int(escolha) <= len(projetos):
                        projeto_id = projetos[int(escolha) - 1]['id']
                    else:
                        # Usa como ID direto
                        projeto_id = escolha
                    
                    executar_todos_testes(projeto_id)
                except Exception as e:
                    print(f"\n❌ Erro: {e}")
                
                input("\nPressione ENTER para continuar...")
        
        elif opcao == '3':
            print("\n🔧 Testes individuais:")
            print("1. Sincronização")
            print("2. Busca no Banco")
            print("3. Adicionar Comentário")
            print("4. Verificar Data")
            
            teste = input("\nEscolha o teste: ").strip()
            projeto_id = input("Digite o ID do projeto: ").strip()
            
            if teste == '1':
                teste_sincronizacao_comentarios(projeto_id)
            elif teste == '2':
                teste_buscar_comentarios_banco(projeto_id)
            elif teste == '3':
                teste_adicionar_comentario(projeto_id)
            elif teste == '4':
                teste_verificar_data_ultimo_comentario(projeto_id)
            else:
                print("❌ Opção inválida")
            
            input("\nPressione ENTER para continuar...")
        
        else:
            print("\n❌ Opção inválida")
            input("Pressione ENTER para continuar...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Encerrando...")
        sys.exit(0)
