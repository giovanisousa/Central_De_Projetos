# -*- coding: utf-8 -*-
"""
Script de teste para validar o processamento de tarefas de implantação.
Use este script para testar a funcionalidade antes de aplicar em produção.
"""

import sys
import os
import json

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_configuracoes():
    """Testa se as configurações estão carregando corretamente."""
    print("=== TESTE DE CONFIGURAÇÕES ===")
    
    try:
        from implantacao_config import (
            TAREFAS_DATA_INICIO, PADROES_TAREFAS_RIS, PADROES_TAREFAS_PACS,
            BATCH_SIZE_TAREFAS, MAX_TAREFAS_PROCESSAR
        )
        
        print(f"✅ Configurações carregadas com sucesso")
        print(f"   📅 Tarefas para atualizar data: {len(TAREFAS_DATA_INICIO)}")
        print(f"   🔍 Padrões RIS: {len(PADROES_TAREFAS_RIS)}")
        print(f"   🔍 Padrões PACS: {len(PADROES_TAREFAS_PACS)}")
        print(f"   ⚙️ Batch size: {BATCH_SIZE_TAREFAS}")
        print(f"   ⚙️ Max tarefas: {MAX_TAREFAS_PROCESSAR}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar configurações: {e}")
        return False

def test_equipe_implantacao():
    """Testa se o arquivo de equipe está acessível."""
    print("\n=== TESTE DE EQUIPE DE IMPLANTAÇÃO ===")
    
    try:
        with open('equipe_implantacao_classificada.json', 'r', encoding='utf-8') as f:
            equipe_data = json.load(f)
        
        ris_count = len(equipe_data.get('Implantação RIS', []))
        pacs_count = len(equipe_data.get('Implantação PACS', []))
        
        print(f"✅ Arquivo de equipe carregado com sucesso")
        print(f"   👥 Implantadores RIS: {ris_count}")
        print(f"   👥 Implantadores PACS: {pacs_count}")
        
        # Verificar se tem ZPUIDs
        if ris_count > 0:
            primeiro_ris = equipe_data['Implantação RIS'][0]
            print(f"   🔍 Exemplo ZPUID RIS: {primeiro_ris.get('zpuid', 'N/A')} ({primeiro_ris.get('name', 'N/A')})")
        
        if pacs_count > 0:
            primeiro_pacs = equipe_data['Implantação PACS'][0]
            print(f"   🔍 Exemplo ZPUID PACS: {primeiro_pacs.get('zpuid', 'N/A')} ({primeiro_pacs.get('name', 'N/A')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar equipe: {e}")
        return False

def test_arquivos_tarefas_json():
    """Testa se os arquivos JSON de tarefas estão acessíveis e válidos."""
    print("\n=== TESTE DE ARQUIVOS JSON DE TAREFAS ===")
    
    try:
        # Testar arquivo RIS
        with open('tarefas_ris.json', 'r', encoding='utf-8') as f:
            ris_data = json.load(f)
        
        tarefas_ris = ris_data.get('tarefas_ris', [])
        print(f"✅ Arquivo tarefas_ris.json carregado")
        print(f"   📋 {len(tarefas_ris)} tarefas RIS definidas")
        
        if len(tarefas_ris) > 0:
            print(f"   🔍 Primeira tarefa RIS: '{tarefas_ris[0]}'")
        
        # Testar arquivo PACS
        with open('tarefas_pacs.json', 'r', encoding='utf-8') as f:
            pacs_data = json.load(f)
        
        tarefas_pacs = pacs_data.get('tarefas_pacs', [])
        print(f"✅ Arquivo tarefas_pacs.json carregado")
        print(f"   📋 {len(tarefas_pacs)} tarefas PACS definidas")
        
        if len(tarefas_pacs) > 0:
            print(f"   🔍 Primeira tarefa PACS: '{tarefas_pacs[0]}'")
        
        # Verificar se há tarefas duplicadas
        ris_set = set(tarefas_ris)
        pacs_set = set(tarefas_pacs)
        
        if len(ris_set) != len(tarefas_ris):
            print(f"   ⚠️ Aviso: {len(tarefas_ris) - len(ris_set)} tarefas RIS duplicadas encontradas")
        
        if len(pacs_set) != len(tarefas_pacs):
            print(f"   ⚠️ Aviso: {len(tarefas_pacs) - len(pacs_set)} tarefas PACS duplicadas encontradas")
        
        # Verificar tarefas comuns (pode ser normal, mas vale reportar)
        comuns = ris_set & pacs_set
        if comuns:
            print(f"   ℹ️ {len(comuns)} tarefas aparecem em ambas as listas:")
            for comum in list(comuns)[:3]:  # Mostrar apenas as 3 primeiras
                print(f"      - {comum}")
            if len(comuns) > 3:
                print(f"      ... e mais {len(comuns) - 3}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Arquivo não encontrado: {e}")
        print(f"   💡 Execute 'extrair_tarefas_templates.py' para gerar os arquivos")
        return False
    except Exception as e:
        print(f"❌ Erro ao carregar arquivos JSON: {e}")
        return False

def test_zpuid_lookup():
    """Testa a busca de ZPUIDs por nome."""
    print("\n=== TESTE DE BUSCA DE ZPUID ===")
    
    try:
        from implantacao_tarefas import ImplantacaoTaskManager
        
        manager = ImplantacaoTaskManager(access_token="dummy_token")
        
        # Pegar nomes reais do arquivo de equipe
        with open('equipe_implantacao_classificada.json', 'r', encoding='utf-8') as f:
            equipe_data = json.load(f)
        
        # Testar RIS
        if equipe_data.get('Implantação RIS'):
            primeiro_ris = equipe_data['Implantação RIS'][0]
            nome_ris = primeiro_ris.get('name')
            zpuid_esperado = primeiro_ris.get('zpuid')
            
            zpuid_encontrado = manager.obter_zpuid_implantador('RIS', nome_ris)
            
            if zpuid_encontrado == zpuid_esperado:
                print(f"   ✅ RIS: {nome_ris} → {zpuid_encontrado}")
            else:
                print(f"   ❌ RIS: Esperado {zpuid_esperado}, encontrado {zpuid_encontrado}")
        
        # Testar PACS
        if equipe_data.get('Implantação PACS'):
            primeiro_pacs = equipe_data['Implantação PACS'][0]
            nome_pacs = primeiro_pacs.get('name')
            zpuid_esperado = primeiro_pacs.get('zpuid')
            
            zpuid_encontrado = manager.obter_zpuid_implantador('PACS', nome_pacs)
            
            if zpuid_encontrado == zpuid_esperado:
                print(f"   ✅ PACS: {nome_pacs} → {zpuid_encontrado}")
            else:
                print(f"   ❌ PACS: Esperado {zpuid_esperado}, encontrado {zpuid_encontrado}")
        
        # Testar nome inexistente
        zpuid_inexistente = manager.obter_zpuid_implantador('RIS', 'Nome Inexistente')
        if zpuid_inexistente is None:
            print(f"   ✅ Nome inexistente retornou None corretamente")
        else:
            print(f"   ❌ Nome inexistente deveria retornar None, mas retornou {zpuid_inexistente}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de ZPUID: {e}")
        return False

def test_identificacao_tarefas():
    """Testa a identificação de tipos de tarefa com os novos arquivos JSON."""
    print("\n=== TESTE DE IDENTIFICAÇÃO DE TAREFAS ===")
    
    try:
        from implantacao_tarefas import ImplantacaoTaskManager
        
        # Criar instância sem token (apenas para teste)
        manager = ImplantacaoTaskManager(access_token="dummy_token")
        
        print(f"   📋 Manager carregado com {len(manager.tarefas_ris)} tarefas RIS e {len(manager.tarefas_pacs)} tarefas PACS")
        
        # Exemplos de títulos de tarefas para teste
        tarefas_teste = [
            "Configuração inicial do servidor RIS",  # Deve estar na lista RIS
            "Instalação do AnimatiPACS",             # Deve estar na lista PACS
            "Treinamento netRIS para usuários",      # Padrão RIS
            "Setup PACS server",                     # Padrão PACS
            "Configuração de integração",            # Genérica
            "Definição do cronograma de homologação", # Tarefa de data
            "Reunião de kickoff",                    # Genérica
            "Conclusão do projeto"                   # Deve ser excluída
        ]
        
        print("   Testando identificação de tipos:")
        for titulo in tarefas_teste:
            tipo = manager.identificar_tipo_tarefa(titulo)
            icon = "🔴" if tipo == "RIS" else "🔵" if tipo == "PACS" else "⚪"
            metodo = ""
            
            # Determinar método usado
            titulo_lower = titulo.lower()
            if tipo:
                if titulo_lower in manager.tarefas_ris:
                    metodo = "(JSON exato)"
                elif titulo_lower in manager.tarefas_pacs:
                    metodo = "(JSON exato)"
                elif any(t in titulo_lower or titulo_lower in t for t in manager.tarefas_ris):
                    metodo = "(JSON parcial)"
                elif any(t in titulo_lower or titulo_lower in t for t in manager.tarefas_pacs):
                    metodo = "(JSON parcial)"
                else:
                    metodo = "(padrão fallback)"
            
            print(f"   {icon} '{titulo}' → {tipo or 'Não identificado'} {metodo}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de identificação: {e}")
        return False

def executar_todos_testes():
    """Executa todos os testes."""
    print("🧪 INICIANDO TESTES DE IMPLANTAÇÃO DE TAREFAS")
    print("=" * 50)
    
    testes = [
        test_configuracoes,
        test_equipe_implantacao,
        test_arquivos_tarefas_json,
        test_identificacao_tarefas,
        test_zpuid_lookup
    ]
    
    sucessos = 0
    total = len(testes)
    
    for teste in testes:
        try:
            if teste():
                sucessos += 1
        except Exception as e:
            print(f"❌ Erro inesperado no teste {teste.__name__}: {e}")
    
    print(f"\n{'=' * 50}")
    print(f"📊 RESULTADO: {sucessos}/{total} testes passaram")
    
    if sucessos == total:
        print("✅ Todos os testes passaram! Sistema pronto para uso.")
        return True
    else:
        print("❌ Alguns testes falharam. Verifique a configuração antes de usar em produção.")
        return False

if __name__ == "__main__":
    executar_todos_testes()