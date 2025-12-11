"""
Script para re-processar os 11 projetos que foram marcados como processados
mas não estão no banco de dados.
"""
import json
import sqlite3

# Carregar fila
print("Carregando arquivo de fila...")
with open('sync_queue_projects.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Conectar ao banco
conn = sqlite3.connect('zoho_cache.db')
cursor = conn.cursor()

# Buscar IDs no banco
cursor.execute('SELECT id FROM projects')
ids_no_banco = {row[0] for row in cursor.fetchall()}
conn.close()

print("\n" + "="*80)
print("ENCONTRANDO PROJETOS PROCESSADOS MAS NÃO SALVOS...")
print("="*80)

# Encontrar projetos processados mas não salvos
processados_nao_salvos = []
for projeto in data['projects']:
    project_id = projeto['id']
    if project_id in data['processed'] and project_id not in ids_no_banco:
        processados_nao_salvos.append(project_id)

if not processados_nao_salvos:
    print("\n✓ Não há projetos para reprocessar!")
    exit(0)

print(f"\nEncontrados {len(processados_nao_salvos)} projetos para reprocessar:")
for i, project_id in enumerate(processados_nao_salvos, 1):
    projeto_info = next((p for p in data['projects'] if p['id'] == project_id), None)
    nome = projeto_info['nome'] if projeto_info else 'N/A'
    print(f"  {i}. {nome[:70]} (ID: {project_id})")

print("\n" + "="*80)
print("REMOVENDO DA LISTA DE PROCESSADOS...")
print("="*80)

# Remover da lista de processados
novos_processados = [pid for pid in data['processed'] if pid not in processados_nao_salvos]
data['processed'] = novos_processados

# Salvar fila atualizada
print(f"\nRemovendo {len(processados_nao_salvos)} projetos da lista de processados...")
print(f"Total processados: {len(data['processed'])} (era {len(data['processed']) + len(processados_nao_salvos)})")

with open('sync_queue_projects.json.tmp', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

import os
os.replace('sync_queue_projects.json.tmp', 'sync_queue_projects.json')

print("\n✓ Fila atualizada com sucesso!")
print(f"\nAgora você pode executar 'python sync_local_completo.py' para reprocessar os projetos.")
print("O script vai tentar sincronizá-los novamente, e se falharem (404), não serão marcados como processados.")
