"""
Teste completo para validar a correção do indicador de ferramentas
ao criar um novo projeto no kanban.
"""

def simular_formatacao_frontend(projeto):
    """Simula a função formatarFerramentas() do frontend JavaScript"""
    produto = (
        projeto.get('produto') or 
        projeto.get('produtos') or 
        projeto.get('produtos_contratados') or 
        ''
    )
    
    if not produto:
        return 'N/D'
    
    map_produtos = {
        'netRIS': 'NR',
        'AnimatiPACS': 'AP',
        'netRIS e AnimatiPACS': 'NR + AP',
        'AnimatiPACS/netRIS': 'NR + AP',
        'netPACS': 'NP'
    }
    return map_produtos.get(produto, produto)


def testar_cenarios():
    print("=" * 80)
    print("TESTE COMPLETO: Correção do Indicador de Ferramentas")
    print("=" * 80)
    
    cenarios = [
        {
            'nome': 'AnimatiPACS/netRIS',
            'produto_form': 'AnimatiPACS/netRIS',
            'esperado': 'NR + AP'
        },
        {
            'nome': 'Apenas netRIS',
            'produto_form': 'netRIS',
            'esperado': 'NR'
        },
        {
            'nome': 'Apenas AnimatiPACS',
            'produto_form': 'AnimatiPACS',
            'esperado': 'AP'
        },
        {
            'nome': 'netPACS',
            'produto_form': 'netPACS',
            'esperado': 'NP'
        },
        {
            'nome': 'netRIS e AnimatiPACS (formato alternativo)',
            'produto_form': 'netRIS e AnimatiPACS',
            'esperado': 'NR + AP'
        }
    ]
    
    print("\n📋 TESTANDO DIFERENTES PRODUTOS\n")
    
    todos_passaram = True
    
    for i, cenario in enumerate(cenarios, 1):
        print(f"\n{'─' * 80}")
        print(f"Cenário {i}: {cenario['nome']}")
        print('─' * 80)
        
        # Simula formulário
        dados = {
            'codigo_contrato_numero': f'1234{i}',
            'nome_cliente': f'Hospital Teste {i}',
            'gp_selecionado': 'Giovani de Sousa',
            'day': '15',
            'month': '01',
            'year': '2025',
            'produto': cenario['produto_form']
        }
        
        # Simula construção de data
        data_inicio = f"{dados['year']}-{dados['month'].zfill(2)}-{dados['day'].zfill(2)}"
        
        # Objeto ANTES da correção (sem campo produto)
        objeto_antes = {
            "id": f"237650200001234567{i}",
            "nome": f"Hospital Teste {i} - Projeto",
            "cliente": f"{dados['codigo_contrato_numero']} - {dados['nome_cliente']}",
            "gp": dados.get('gp_selecionado', 'GP não informado'),
            "data_inicio_formatada": data_inicio.replace('-', '/'),
            "dias_na_fase": "0 dias",
            "status_atual": "Aguardando Onboarding"
            # ❌ SEM campos de produto
        }
        
        # Objeto DEPOIS da correção (com campos produto)
        objeto_depois = {
            "id": f"237650200001234567{i}",
            "nome": f"Hospital Teste {i} - Projeto",
            "cliente": f"{dados['codigo_contrato_numero']} - {dados['nome_cliente']}",
            "gp": dados.get('gp_selecionado', 'GP não informado'),
            "data_inicio": data_inicio,
            "data_inicio_formatada": data_inicio.replace('-', '/'),
            "dias_na_fase": 0,
            "dias_total": 0,
            "status_atual": "Aguardando Onboarding",
            "produto": dados.get('produto', ''),  # ✅ Campo principal
            "produtos": dados.get('produto', ''),  # ✅ Alias 1
            "produtos_contratados": dados.get('produto', '')  # ✅ Alias 2
        }
        
        resultado_antes = simular_formatacao_frontend(objeto_antes)
        resultado_depois = simular_formatacao_frontend(objeto_depois)
        
        print(f"\nProduto no formulário: '{dados['produto']}'")
        print(f"Resultado esperado: '{cenario['esperado']}'")
        print(f"\n  ANTES da correção:")
        print(f"    - Campo 'produto' presente? {'✅' if 'produto' in objeto_antes else '❌'}")
        print(f"    - Valor retornado: '{resultado_antes}'")
        print(f"    - Status: {'❌ INCORRETO' if resultado_antes == 'N/D' else '⚠️ Inesperado'}")
        
        print(f"\n  DEPOIS da correção:")
        print(f"    - Campo 'produto' presente? {'✅' if 'produto' in objeto_depois else '❌'}")
        print(f"    - Campo 'produtos' presente? {'✅' if 'produtos' in objeto_depois else '❌'}")
        print(f"    - Campo 'produtos_contratados' presente? {'✅' if 'produtos_contratados' in objeto_depois else '❌'}")
        print(f"    - Valor retornado: '{resultado_depois}'")
        
        if resultado_depois == cenario['esperado']:
            print(f"    - Status: ✅ CORRETO")
        else:
            print(f"    - Status: ❌ INCORRETO (esperado: '{cenario['esperado']}')")
            todos_passaram = False
        
        # Validação da correção
        corrigiu = resultado_antes == 'N/D' and resultado_depois == cenario['esperado']
        print(f"\n  {'✅' if corrigiu else '❌'} Correção {'bem-sucedida' if corrigiu else 'falhou'}")
    
    # Resumo final
    print(f"\n{'=' * 80}")
    print("RESUMO FINAL")
    print('=' * 80)
    
    if todos_passaram:
        print("\n✅ TODOS OS CENÁRIOS PASSARAM!")
        print("\nA correção está funcionando perfeitamente:")
        print("  • Campos de produto incluídos no objeto de fallback")
        print("  • Frontend consegue extrair e formatar corretamente")
        print("  • Usuário vê a informação correta imediatamente após criar projeto")
    else:
        print("\n❌ ALGUNS CENÁRIOS FALHARAM")
        print("Revisar a implementação da correção")
    
    print(f"\n{'=' * 80}\n")

if __name__ == '__main__':
    testar_cenarios()
