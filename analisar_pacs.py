import json

# Carregar arquivo
with open('todas_outras_tarefas.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Buscar tarefas com PACS
pacs_tasks = [item for item in data if 'pacs' in item['nome'].lower()]
print(f'Tarefas com PACS: {len(pacs_tasks)}')

for item in pacs_tasks[:15]:
    print(f"- {item['nome']} (milestone: {item['milestone']})")

# Buscar milestones que podem ser PACS
print("\nTodos os milestones únicos:")
milestones = set(item['milestone'] for item in data if item['milestone'])
for milestone in sorted(milestones):
    print(f"- {milestone}")