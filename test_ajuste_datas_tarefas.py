# -*- coding: utf-8 -*-
"""
Script de teste para validar a funcionalidade de ajuste de datas
de tarefas específicas durante o agendamento de implantação.

Testa a remoção de prefixos e a identificação correta das tarefas.
"""

import sys
from implantacao_tarefas import ImplantacaoTaskManager

def testar_remocao_prefixos():
    """Testa a função de remoção de prefixos."""
    print("\n" + "="*80)
    print("TESTE 1: Remoção de Prefixos")
    print("="*80)
    
    manager = ImplantacaoTaskManager()
    
    casos_teste = [
        # (titulo_original, titulo_esperado_sem_prefixos)
        ("1. Realizar reunião com cliente", "Realizar reunião com cliente"),
        ("2.1 Checar o DEIP", "Checar o DEIP"),
        ("3.2.1 Enviar documentação", "Enviar documentação"),
        ("[RIS] Realizar reunião com cliente", "Realizar reunião com cliente"),
        ("[PACS] Checar o DEIP", "Checar o DEIP"),
        ("(RIS) Realizar reunião", "Realizar reunião"),
        ("1.2 [RIS] Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)", 
         "Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"),
        ("   5.   Tarefa com espaços   ", "Tarefa com espaços"),
    ]
    
    sucesso = 0
    falhas = 0
    
    for titulo_original, titulo_esperado in casos_teste:
        resultado = manager._remover_prefixos_tarefa(titulo_original)
        
        if resultado == titulo_esperado:
            print(f"✅ PASS: '{titulo_original}'")
            print(f"   → '{resultado}'")
            sucesso += 1
        else:
            print(f"❌ FAIL: '{titulo_original}'")
            print(f"   Esperado: '{titulo_esperado}'")
            print(f"   Obtido:   '{resultado}'")
            falhas += 1
        print()
    
    print(f"\nResultado: {sucesso} sucessos, {falhas} falhas")
    return falhas == 0


def testar_identificacao_tarefas():
    """Testa a função de identificação de tarefas que precisam ajuste de data."""
    print("\n" + "="*80)
    print("TESTE 2: Identificação de Tarefas para Ajuste de Data")
    print("="*80)
    
    manager = ImplantacaoTaskManager()
    
    # Tarefas que DEVEM ser identificadas
    tarefas_devem_identificar = [
        "Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)",
        "Realizar reunião com cliente para entendimento do fluxo do cliente (PACS)",
        "Checar o DEIP e os Docs de Infra",
        # Com prefixos
        "1. Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)",
        "2.1 [RIS] Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)",
        "[PACS] Realizar reunião com cliente para entendimento do fluxo do cliente (PACS)",
        "5. Checar o DEIP e os Docs de Infra",
    ]
    
    # Tarefas que NÃO devem ser identificadas
    tarefas_nao_devem_identificar = [
        "Realizar reunião de kickoff",
        "Checar apenas o DEIP",
        "Agendar reunião com equipe",
        "Realizar testes de integração",
        "Enviar relatório para cliente",
    ]
    
    sucesso = 0
    falhas = 0
    
    print("\n📋 Tarefas que DEVEM ser identificadas:")
    print("-" * 80)
    for tarefa in tarefas_devem_identificar:
        resultado = manager._verificar_tarefa_ajuste_data(tarefa)
        
        if resultado:
            print(f"✅ PASS: '{tarefa[:70]}'")
            sucesso += 1
        else:
            print(f"❌ FAIL: '{tarefa[:70]}' (não foi identificada)")
            falhas += 1
    
    print("\n📋 Tarefas que NÃO devem ser identificadas:")
    print("-" * 80)
    for tarefa in tarefas_nao_devem_identificar:
        resultado = manager._verificar_tarefa_ajuste_data(tarefa)
        
        if not resultado:
            print(f"✅ PASS: '{tarefa[:70]}' (corretamente ignorada)")
            sucesso += 1
        else:
            print(f"❌ FAIL: '{tarefa[:70]}' (foi identificada incorretamente)")
            falhas += 1
    
    print(f"\n\nResultado: {sucesso} sucessos, {falhas} falhas")
    return falhas == 0


def testar_casos_limite():
    """Testa casos limite e edge cases."""
    print("\n" + "="*80)
    print("TESTE 3: Casos Limite")
    print("="*80)
    
    manager = ImplantacaoTaskManager()
    
    casos_teste = [
        # (titulo, deve_identificar, descricao)
        ("", False, "String vazia"),
        ("   ", False, "Apenas espaços"),
        ("REALIZAR REUNIÃO COM CLIENTE PARA ENTENDIMENTO DO FLUXO DO CLIENTE (RIS)", 
         True, "Título em maiúsculas"),
        ("realizar reunião com cliente para entendimento do fluxo do cliente (ris)", 
         True, "Título em minúsculas"),
        ("1.2.3.4.5 [RIS][PACS] Checar o DEIP e os Docs de Infra (URGENTE)", 
         True, "Múltiplos prefixos e sufixos"),
    ]
    
    sucesso = 0
    falhas = 0
    
    for titulo, deve_identificar, descricao in casos_teste:
        resultado = manager._verificar_tarefa_ajuste_data(titulo)
        
        if resultado == deve_identificar:
            print(f"✅ PASS: {descricao}")
            print(f"   Título: '{titulo}'")
            print(f"   Esperado: {deve_identificar}, Obtido: {resultado}")
            sucesso += 1
        else:
            print(f"❌ FAIL: {descricao}")
            print(f"   Título: '{titulo}'")
            print(f"   Esperado: {deve_identificar}, Obtido: {resultado}")
            falhas += 1
        print()
    
    print(f"\nResultado: {sucesso} sucessos, {falhas} falhas")
    return falhas == 0


def executar_todos_testes():
    """Executa todos os testes e exibe relatório final."""
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "TESTE DE AJUSTE DE DATAS - TAREFAS ESPECÍFICAS" + " "*12 + "║")
    print("╚" + "═"*78 + "╝")
    
    resultados = []
    
    # Teste 1
    try:
        resultados.append(("Remoção de Prefixos", testar_remocao_prefixos()))
    except Exception as e:
        print(f"\n❌ ERRO no Teste 1: {e}")
        import traceback
        traceback.print_exc()
        resultados.append(("Remoção de Prefixos", False))
    
    # Teste 2
    try:
        resultados.append(("Identificação de Tarefas", testar_identificacao_tarefas()))
    except Exception as e:
        print(f"\n❌ ERRO no Teste 2: {e}")
        import traceback
        traceback.print_exc()
        resultados.append(("Identificação de Tarefas", False))
    
    # Teste 3
    try:
        resultados.append(("Casos Limite", testar_casos_limite()))
    except Exception as e:
        print(f"\n❌ ERRO no Teste 3: {e}")
        import traceback
        traceback.print_exc()
        resultados.append(("Casos Limite", False))
    
    # Relatório Final
    print("\n\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*30 + "RELATÓRIO FINAL" + " "*33 + "║")
    print("╚" + "═"*78 + "╝")
    print()
    
    total_sucesso = 0
    total_falhas = 0
    
    for nome_teste, passou in resultados:
        status = "✅ PASSOU" if passou else "❌ FALHOU"
        print(f"{status} - {nome_teste}")
        
        if passou:
            total_sucesso += 1
        else:
            total_falhas += 1
    
    print()
    print("─" * 80)
    print(f"Total: {total_sucesso} testes passaram, {total_falhas} testes falharam")
    print("─" * 80)
    
    if total_falhas == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM! 🎉")
        return 0
    else:
        print(f"\n⚠️  {total_falhas} TESTE(S) FALHARAM")
        return 1


if __name__ == "__main__":
    sys.exit(executar_todos_testes())
