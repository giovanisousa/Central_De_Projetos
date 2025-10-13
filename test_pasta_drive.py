#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da lógica de criação de pastas no Google Drive
Verifica se as pastas estão sendo criadas nos diretórios corretos
"""

from config import ID_PASTA_PAI_NETRIS, ID_PASTA_PAI_ANIMATIPACS

def testar_logica_pasta():
    """Testa a lógica de seleção de pasta baseada no produto"""
    
    # Mapeamento dos produtos (mesmo do utils.py)
    produto_map = {
        "netRIS": "1", 
        "AnimatiPACS": "2", 
        "netRIS e AnimatiPACS": "3",
        "AnimatiPACS/netRIS": "3"
    }
    
    # Casos de teste
    casos_teste = [
        {
            "produto": "netRIS",
            "pasta_esperada": ID_PASTA_PAI_NETRIS,
            "descricao": "Somente netRIS"
        },
        {
            "produto": "AnimatiPACS", 
            "pasta_esperada": ID_PASTA_PAI_ANIMATIPACS,
            "descricao": "Somente AnimatiPACS"
        },
        {
            "produto": "AnimatiPACS/netRIS",
            "pasta_esperada": ID_PASTA_PAI_NETRIS, 
            "descricao": "Híbrido (AnimatiPACS + netRIS)"
        },
        {
            "produto": "netRIS e AnimatiPACS",
            "pasta_esperada": ID_PASTA_PAI_NETRIS,
            "descricao": "Híbrido (netRIS + AnimatiPACS)"
        }
    ]
    
    print("🧪 TESTE DA LÓGICA DE CRIAÇÃO DE PASTAS NO GOOGLE DRIVE")
    print("=" * 60)
    print(f"📁 Pasta netRIS/Híbrido: {ID_PASTA_PAI_NETRIS}")
    print(f"📁 Pasta AnimatiPACS: {ID_PASTA_PAI_ANIMATIPACS}")
    print("=" * 60)
    
    todos_passaram = True
    
    for caso in casos_teste:
        produto_selecionado = caso["produto"]
        produto_id = produto_map.get(produto_selecionado, "2")
        
        # Lógica do utils.py
        id_pasta_pai = ID_PASTA_PAI_NETRIS if produto_id in ['1', '3'] else ID_PASTA_PAI_ANIMATIPACS
        
        passou = id_pasta_pai == caso["pasta_esperada"]
        status = "✅ PASSOU" if passou else "❌ FALHOU"
        
        print(f"{status} {caso['descricao']}")
        print(f"   Produto: '{produto_selecionado}' (ID: {produto_id})")
        print(f"   Pasta escolhida: {id_pasta_pai}")
        print(f"   Pasta esperada: {caso['pasta_esperada']}")
        print()
        
        if not passou:
            todos_passaram = False
    
    print("=" * 60)
    if todos_passaram:
        print("🎉 TODOS OS TESTES PASSARAM! A lógica está correta.")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM! Verificar a lógica.")
    
    return todos_passaram

if __name__ == "__main__":
    testar_logica_pasta()