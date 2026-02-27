import json

with open('sync_queue_projects.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Buscar projeto 1118 - DoctorClin
print("="*60)
print("PROCURANDO PROJETO 1118 - DOCTORCLIN NA FILA:")
print("="*60)

found = None
for projeto in data['projects']:
    nome = projeto.get('nome', '')
    if '1118' in nome or 'DoctorClin' in nome.upper():
        found = projeto
        break

if found:
    print(f"✓ ENCONTRADO NA FILA:")
    print(f"  ID: {found['id']}")
    print(f"  Nome: {found['nome']}")
    
    # Verificar se foi processado
    if found['id'] in data['processed']:
        print(f"  Status: ✓ JÁ PROCESSADO")
    else:
        print(f"  Status: ⏳ AGUARDANDO PROCESSAMENTO")
else:
    print("✗ NÃO ENCONTRADO na fila")

print(f"\n{'='*60}")
print(f"ESTATÍSTICAS DA FILA:")
print(f"{'='*60}")
print(f"Total de projetos: {len(data['projects'])}")
print(f"Processados: {len(data['processed'])}")
print(f"Restantes: {len(data['projects']) - len(data['processed'])}")
