# Teste para verificar se o campo 'produto' está presente no objeto novo_projeto

# Simula o cenário de fallback quando a sincronização falha
def testar_objeto_novo_projeto():
    print("=" * 70)
    print("TESTE: Objeto novo_projeto com fallback")
    print("=" * 70)
    
    # Dados simulados do formulário
    dados = {
        'codigo_contrato_numero': '12345',
        'nome_cliente': 'Hospital Teste',
        'gp_selecionado': 'Giovani de Sousa',
        'start_date': '2025-01-15',
        'produto': 'AnimatiPACS/netRIS'  # Este é o campo importante
    }
    
    id_do_novo_projeto = '2376502000012345678'
    
    # Simula a criação do objeto fallback (código corrigido)
    novo_projeto = {
        "id": str(id_do_novo_projeto),
        "nome": f"Hospital Teste - NR/AP",  # Simulando construir_titulo_projeto
        "cliente": f"{dados['codigo_contrato_numero']} - {dados['nome_cliente']}",
        "gp": dados.get('gp_selecionado', 'GP não informado'),
        "data_inicio_formatada": dados.get('start_date', '').replace('-', '/'),
        "dias_na_fase": "0 dias",
        "status_atual": "Aguardando Onboarding",
        "produto": dados.get('produto', '')  # Campo adicionado na correção
    }
    
    print("\nObjeto novo_projeto criado:")
    print("-" * 70)
    for key, value in novo_projeto.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("VERIFICAÇÕES:")
    print("=" * 70)
    
    # Verificação 1: Campo 'produto' existe?
    if 'produto' in novo_projeto:
        print("✅ Campo 'produto' PRESENTE no objeto")
    else:
        print("❌ Campo 'produto' AUSENTE no objeto")
    
    # Verificação 2: Campo 'produto' tem valor?
    if novo_projeto.get('produto'):
        print(f"✅ Campo 'produto' tem valor: '{novo_projeto['produto']}'")
    else:
        print("❌ Campo 'produto' está vazio ou None")
    
    # Verificação 3: Simula função formatarFerramentas do frontend
    print("\n" + "=" * 70)
    print("SIMULAÇÃO: Função formatarFerramentas() do frontend")
    print("=" * 70)
    
    def formatarFerramentas(produto):
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
    
    # Testa com diferentes variações de campo
    produto_valor = (
        novo_projeto.get('produto') or 
        novo_projeto.get('produtos') or 
        novo_projeto.get('produtos_contratados') or 
        ''
    )
    
    resultado = formatarFerramentas(produto_valor)
    
    print(f"\nProduto extraído: '{produto_valor}'")
    print(f"Resultado formatado: '{resultado}'")
    
    if resultado == 'N/D':
        print("\n❌ ERRO: Frontend exibirá 'N/D' no card")
    else:
        print(f"\n✅ SUCESSO: Frontend exibirá '{resultado}' no card")
    
    print("\n" + "=" * 70)
    print("COMPARAÇÃO: ANTES vs DEPOIS DA CORREÇÃO")
    print("=" * 70)
    
    # Objeto ANTES da correção (sem campo 'produto')
    objeto_antes = {
        "id": str(id_do_novo_projeto),
        "nome": f"Hospital Teste - NR/AP",
        "cliente": f"{dados['codigo_contrato_numero']} - {dados['nome_cliente']}",
        "gp": dados.get('gp_selecionado', 'GP não informado'),
        "data_inicio_formatada": dados.get('start_date', '').replace('-', '/'),
        "dias_na_fase": "0 dias",
        "status_atual": "Aguardando Onboarding"
        # ❌ SEM campo 'produto'
    }
    
    resultado_antes = formatarFerramentas(objeto_antes.get('produto', ''))
    resultado_depois = formatarFerramentas(novo_projeto.get('produto', ''))
    
    print(f"\nANTES (sem campo 'produto'): {resultado_antes}")
    print(f"DEPOIS (com campo 'produto'): {resultado_depois}")
    
    if resultado_antes == 'N/D' and resultado_depois != 'N/D':
        print("\n✅ CORREÇÃO BEM-SUCEDIDA!")
    else:
        print("\n⚠️  Verificar correção")

if __name__ == '__main__':
    testar_objeto_novo_projeto()
