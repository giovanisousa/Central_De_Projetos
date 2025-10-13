import sqlite3

# Simular a lógica do endpoint
projeto_id = '2376502000003539455'

conn = sqlite3.connect('zoho_cache.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT nome, percentual_conclusao 
    FROM fases 
    WHERE projeto_id = ?
""", (projeto_id,))

fases = cursor.fetchall()
conn.close()

# Inicializar resultado
resultado = {
    'NR': None,
    'AP': None,
    'IMP': None,
    'INT': None
}

print(f"Processando {len(fases)} fases...\n")

# Mapear fases para as barras
for fase in fases:
    nome_fase = (fase[0] or '').strip()
    percentual = fase[1] if fase[1] is not None else 0
    
    # Garantir que o percentual seja um número entre 0 e 100
    try:
        percentual = float(percentual)
        percentual = max(0, min(100, percentual))
    except (ValueError, TypeError):
        percentual = 0
    
    print(f"Fase: '{nome_fase}'")
    print(f"Percentual original: {percentual}")
    
    # Mapear para as categorias (verificações mais específicas primeiro)
    categoria_atribuida = None
    
    if 'Implantação RIS' in nome_fase:
        resultado['NR'] = round(percentual, 1)
        categoria_atribuida = 'NR'
    elif 'Implantação PACS' in nome_fase:
        resultado['AP'] = round(percentual, 1)
        categoria_atribuida = 'AP'
    elif 'Importação' in nome_fase or 'Importacao' in nome_fase:
        resultado['IMP'] = round(percentual, 1)
        categoria_atribuida = 'IMP'
    elif 'Integração' in nome_fase or 'Integracao' in nome_fase:
        resultado['INT'] = round(percentual, 1)
        categoria_atribuida = 'INT'
    
    print(f"Categoria atribuída: {categoria_atribuida}")
    print(f"Resultado atual: {resultado}")
    print('-' * 70)

print(f"\n\nResultado final:")
print(resultado)
