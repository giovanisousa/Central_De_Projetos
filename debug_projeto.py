import sqlite3

# Consultar fases do projeto específico
conn = sqlite3.connect('zoho_cache.db')
cursor = conn.cursor()

projeto_id = '2376502000003539455'

print(f"Buscando fases do projeto {projeto_id}...")
cursor.execute('SELECT projeto_id, nome, percentual_conclusao FROM fases WHERE projeto_id = ?', (projeto_id,))
results = cursor.fetchall()

print(f'\nTotal de fases encontradas: {len(results)}\n')
for r in results:
    print(f'Projeto: {r[0]}')
    print(f'Fase: {r[1]}')
    print(f'Percentual: {r[2]}%')
    print('-' * 50)

conn.close()
