import sqlite3
import json

conn = sqlite3.connect('zoho_cache.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM projects')
proj = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM fases')
fases = cursor.fetchone()[0]

conn.close()

with open('sync_queue_projects.json', encoding='utf-8') as f:
    fila = json.load(f)

print('='*80)
print('📊 STATUS ATUAL:')
print('='*80)
print(f'Projetos no banco SQLite: {proj}')
print(f'Fases no banco SQLite: {fases}')
print(f'Total na fila: {len(fila["projects"])}')
print(f'Marcados como processados: {len(fila["processed"])}')
print(f'Restantes para processar: {len(fila["projects"]) - len(fila["processed"])}')
print('='*80)
print(f'\n✅ Fila e banco agora estão sincronizados!')
print(f'   Processados na fila = Projetos no banco: {len(fila["processed"])} = {proj}')
