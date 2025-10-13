# -*- coding: utf-8 -*-
"""
Teste rápido para validar extração do nome do cliente
"""

import re

def extrair_nome_cliente(nome_projeto):
    """
    Extrai o nome limpo do cliente a partir do nome do projeto.
    
    Remove:
    - Prefixo numérico no início (ex: "9876 - ")
    - Sufixos " - NR", " - AP", " - NR/AP"
    - Códigos numéricos no final (ex: " 001", " 002")
    
    Exemplos:
        "9876 - Projeto teste ultimo" → "Projeto teste ultimo"
        "Hospital ABC - NR 001" → "Hospital ABC"
        "1234 - Clínica XYZ - AP 002" → "Clínica XYZ"
        "Santa Casa" → "Santa Casa"
    """
    import re
    
    nome_cliente = nome_projeto
    
    # 1. Remover prefixo numérico no início (ex: "9876 - ", "1234 - ")
    nome_cliente = re.sub(r'^\d+\s*-\s*', '', nome_cliente).strip()
    
    # 2. Remover " - NR", " - AP", " - NR/AP" e código numérico
    for padrao in [' - NR/AP', ' - NR', ' - AP']:
        if padrao in nome_cliente:
            nome_cliente = nome_cliente.split(padrao)[0].strip()
            break
    
    # 3. Remover código numérico no final (ex: " 001", " 002", etc.)
    nome_cliente = re.sub(r'\s+\d+$', '', nome_cliente).strip()
    
    return nome_cliente


# Testes
casos_teste = [
    # Padrão novo: prefixo numérico
    ("9876 - Projeto teste ultimo", "Projeto teste ultimo"),
    ("1234 - Hospital ABC", "Hospital ABC"),
    ("5678 - Clínica XYZ - AP 002", "Clínica XYZ"),
    
    # Padrões antigos
    ("Hospital ABC - NR 001", "Hospital ABC"),
    ("Clínica XYZ - AP 002", "Clínica XYZ"),
    ("Centro Médico - NR/AP 003", "Centro Médico"),
    ("Santa Casa de Misericórdia - NR 123", "Santa Casa de Misericórdia"),
    ("Instituto de Diagnóstico - AP 456", "Instituto de Diagnóstico"),
    ("Policlínica São José - NR/AP 789", "Policlínica São José"),
    
    # Casos especiais
    ("Hospital Regional", "Hospital Regional"),  # Sem prefixo/sufixo
    ("Clínica Popular 001", "Clínica Popular"),  # Sem sufixo mas com código final
    ("999 - Centro Médico - NR 001", "Centro Médico"),  # Prefixo + sufixo + código
]

print("\n" + "="*70)
print("TESTE DE EXTRAÇÃO DO NOME DO CLIENTE")
print("="*70 + "\n")

todos_passaram = True

for nome_projeto, esperado in casos_teste:
    resultado = extrair_nome_cliente(nome_projeto)
    passou = resultado == esperado
    
    simbolo = "✅" if passou else "❌"
    print(f"{simbolo} {nome_projeto}")
    print(f"   Esperado: '{esperado}'")
    print(f"   Obtido:   '{resultado}'")
    
    if not passou:
        todos_passaram = False
    print()

print("="*70)
if todos_passaram:
    print("🎉 TODOS OS TESTES PASSARAM! 🎉")
else:
    print("⚠️ ALGUNS TESTES FALHARAM ⚠️")
print("="*70 + "\n")
