import sqlite3
import json

conn = sqlite3.connect('zoho_cache.db')
cursor = conn.cursor()

cursor.execute('SELECT id, nome, full_data_json FROM projects LIMIT 1')
row = cursor.fetchone()

if row:
    project_id = row[0]
    project_name = row[1]
    full_data = json.loads(row[2]) if row[2] else {}
    
    print(f"Projeto: {project_name} (ID: {project_id})")
    print(f"\nKeys no full_data: {list(full_data.keys())}")
    print("\n=== CUSTOM FIELDS DISPONÍVEIS ===\n")
    
    custom_fields = full_data.get('custom_fields', [])
    print(f"Total de custom fields: {len(custom_fields)}")
    
    if custom_fields:
        for field in custom_fields:
            label = field.get('label_name', 'N/A')
            column_name = field.get('column_name', 'N/A')
            value = field.get('value', 'N/A')
            print(f"  - {label} ({column_name}): {value}")
    else:
        print("  Nenhum custom field encontrado!")
        print(f"\n  Campos de primeiro nível que contêm 'data' ou 'homolog':")
        for key in full_data.keys():
            if 'data' in key.lower() or 'homolog' in key.lower():
                print(f"    - {key}: {full_data[key]}")

conn.close()
