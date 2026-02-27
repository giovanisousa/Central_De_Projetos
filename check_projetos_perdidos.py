import json
import sqlite3

# Carregar fila
with open('sync_queue_projects.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Conectar ao banco
conn = sqlite3.connect('zoho_cache.db')
cursor = conn.cursor()

# Buscar IDs no banco
cursor.execute('SELECT id FROM projects')
ids_no_banco = {row[0] for row in cursor.fetchall()}

print("="*80)
print("PROJETOS MARCADOS COMO PROCESSADOS MAS NÃO ESTÃO NO BANCO:")
print("="*80)

processados_nao_salvos = []
for projeto in data['projects']:
    project_id = projeto['id']
    if project_id in data['processed'] and project_id not in ids_no_banco:
        processados_nao_salvos.append(projeto)

if processados_nao_salvos:
    print(f"\nTotal: {len(processados_nao_salvos)} projetos processados mas não salvos\n")
    for i, p in enumerate(processados_nao_salvos, 1):
        print(f"{i}. {p['nome']} (ID: {p['id']})")
else:
    print("\n✓ Todos os projetos processados estão no banco!")

print(f"\n{'='*80}")
print(f"RESUMO:")
print(f"{'='*80}")
print(f"Projetos na fila: {len(data['projects'])}")
print(f"Marcados como processados: {len(data['processed'])}")
print(f"Salvos no banco: {len(ids_no_banco)}")
print(f"Processados mas NÃO salvos: {len(processados_nao_salvos)}")
print(f"Diferença esperada: {len(data['processed']) - len(ids_no_banco)}")

conn.close()
