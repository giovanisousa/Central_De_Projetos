#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste rápido da extração de nome do cliente"""

import re

def extrair_nome_cliente(nome_projeto: str) -> str:
    """
    Extrai o nome limpo do cliente removendo códigos numéricos e sufixos técnicos.
    
    Exemplos:
        "9876 - Projeto teste ultimo - NR/AP" → "Projeto teste ultimo"
        "Hospital ABC - NR 001" → "Hospital ABC"
        "1234 - Clínica XYZ" → "Clínica XYZ"
    """
    nome_cliente = nome_projeto.strip()
    
    # 1. Remove prefixo numérico do tipo "9876 - "
    nome_cliente = re.sub(r'^\d+\s*-\s*', '', nome_cliente)
    
    # 2. Remove sufixos conhecidos (NR, AP, NR/AP)
    for padrao in [' - NR/AP', ' - NR', ' - AP']:
        if padrao in nome_cliente:
            nome_cliente = nome_cliente.split(padrao)[0]
            break
    
    # 3. Remove código numérico no final do tipo " 001"
    nome_cliente = re.sub(r'\s+\d+$', '', nome_cliente)
    
    return nome_cliente.strip()

# Testes
testes = [
    ("9876 - Projeto teste ultimo - NR/AP", "Projeto teste ultimo"),
    ("Hospital ABC - NR 001", "Hospital ABC"),
    ("1234 - Clínica XYZ", "Clínica XYZ"),
    ("5678 - Centro Médico - AP 002", "Centro Médico"),
    ("Projeto Sem Código - NR/AP", "Projeto Sem Código"),
]

print("=" * 70)
print("TESTE DE EXTRAÇÃO DE NOME DO CLIENTE")
print("=" * 70)

sucessos = 0
falhas = 0

for entrada, esperado in testes:
    resultado = extrair_nome_cliente(entrada)
    status = "✅ PASS" if resultado == esperado else "❌ FAIL"
    
    if resultado == esperado:
        sucessos += 1
    else:
        falhas += 1
    
    print(f"\n{status}")
    print(f"  Entrada:  '{entrada}'")
    print(f"  Esperado: '{esperado}'")
    print(f"  Obtido:   '{resultado}'")

print("\n" + "=" * 70)
print(f"RESULTADO: {sucessos} passaram, {falhas} falharam")
print("=" * 70)
