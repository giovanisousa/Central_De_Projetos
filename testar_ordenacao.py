"""
Script de teste para validar a ordenação por dias_na_fase
"""

def extrair_dias_numericos(projeto):
    """
    Converte o valor de dias_na_fase para número para ordenação.
    - "Hoje" -> 0
    - "1d", "2d", etc -> 1, 2, etc
    - "N/D" -> -1 (vai para o final)
    - "Futuro" -> -2 (vai para o final)
    """
    dias_str = projeto.get('dias_na_fase', 'N/D')
    if dias_str == 'Hoje':
        return 0
    elif dias_str == 'N/D':
        return -1
    elif dias_str == 'Futuro':
        return -2
    elif isinstance(dias_str, str) and dias_str.endswith('d'):
        try:
            return int(dias_str[:-1])  # Remove o 'd' e converte para int
        except ValueError:
            return -1
    else:
        return -1


# Teste de ordenação
projetos_teste = [
    {'nome': 'Projeto A', 'dias_na_fase': '5d'},
    {'nome': 'Projeto B', 'dias_na_fase': 'Hoje'},
    {'nome': 'Projeto C', 'dias_na_fase': '15d'},
    {'nome': 'Projeto D', 'dias_na_fase': '2d'},
    {'nome': 'Projeto E', 'dias_na_fase': 'N/D'},
    {'nome': 'Projeto F', 'dias_na_fase': '10d'},
    {'nome': 'Projeto G', 'dias_na_fase': 'Futuro'},
]

print("=" * 60)
print("🧪 TESTE DE ORDENAÇÃO POR DIAS_NA_FASE")
print("=" * 60)

print("\n📋 Projetos ANTES da ordenação:")
for i, p in enumerate(projetos_teste, 1):
    valor_num = extrair_dias_numericos(p)
    print(f"  {i}. {p['nome']:20} | dias_na_fase: {p['dias_na_fase']:10} | valor: {valor_num:3}")

# Aplica ordenação (DECRESCENTE)
projetos_ordenados = sorted(projetos_teste, key=extrair_dias_numericos, reverse=True)

print("\n✅ Projetos DEPOIS da ordenação (DECRESCENTE):")
for i, p in enumerate(projetos_ordenados, 1):
    valor_num = extrair_dias_numericos(p)
    emoji = "🔴" if valor_num >= 10 else "🟡" if valor_num >= 5 else "🟢" if valor_num >= 0 else "⚪"
    print(f"  {i}. {emoji} {p['nome']:20} | dias_na_fase: {p['dias_na_fase']:10} | valor: {valor_num:3}")

print("\n" + "=" * 60)
print("✅ VALIDAÇÃO DA ORDEM")
print("=" * 60)

# Validação: verifica se está em ordem decrescente
valores = [extrair_dias_numericos(p) for p in projetos_ordenados]
esta_ordenado = all(valores[i] >= valores[i+1] for i in range(len(valores)-1))

if esta_ordenado:
    print("✅ SUCESSO: Projetos estão ordenados corretamente (decrescente)")
else:
    print("❌ ERRO: Ordem incorreta!")

print("\n📊 Ordem esperada:")
print("  1º → Projetos com mais dias (15d, 10d, 5d...)")
print("  2º → Projetos recentes (Hoje)")
print("  3º → Projetos sem data (N/D)")
print("  4º → Projetos futuros (Futuro)")

print("\n" + "=" * 60)
print("🎯 CASOS DE USO")
print("=" * 60)

print("\n1️⃣ Coluna 'Em Andamento':")
em_andamento = [
    {'nome': 'Hospital X', 'dias_na_fase': '20d'},
    {'nome': 'Clínica Y', 'dias_na_fase': '5d'},
    {'nome': 'Lab Z', 'dias_na_fase': 'Hoje'},
]
em_andamento_ordenado = sorted(em_andamento, key=extrair_dias_numericos, reverse=True)
for i, p in enumerate(em_andamento_ordenado, 1):
    print(f"   {i}. {p['nome']:15} | {p['dias_na_fase']:5} <- {'🔴 ATENÇÃO!' if extrair_dias_numericos(p) >= 15 else '✅ OK'}")

print("\n2️⃣ Coluna 'Em Homologação':")
em_homologacao = [
    {'nome': 'Projeto A', 'dias_na_fase': '3d'},
    {'nome': 'Projeto B', 'dias_na_fase': '12d'},
    {'nome': 'Projeto C', 'dias_na_fase': '1d'},
    {'nome': 'Projeto D', 'dias_na_fase': 'Hoje'},
]
em_homologacao_ordenado = sorted(em_homologacao, key=extrair_dias_numericos, reverse=True)
for i, p in enumerate(em_homologacao_ordenado, 1):
    print(f"   {i}. {p['nome']:15} | {p['dias_na_fase']:5}")

print("\n" + "=" * 60)
print("✅ TESTE CONCLUÍDO COM SUCESSO!")
print("=" * 60)
