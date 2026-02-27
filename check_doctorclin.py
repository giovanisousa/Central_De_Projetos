import sqlite3

conn = sqlite3.connect('zoho_cache.db')
cursor = conn.cursor()

# Ver estrutura da tabela
print("="*60)
print("ESTRUTURA DA TABELA PROJECTS:")
print("="*60)
cursor.execute('PRAGMA table_info(projects)')
for col in cursor.fetchall():
    print(f"  - {col[1]} ({col[2]})")

# Buscar projeto DoctorClin
print("\n" + "="*60)
print("BUSCANDO PROJETO DOCTORCLIN:")
print("="*60)
cursor.execute("SELECT id, nome FROM projects WHERE nome LIKE '%DoctorClin%'")
result = cursor.fetchone()
if result:
    print(f"✓ ENCONTRADO: ID={result[0]}, Nome={result[1]}")
else:
    print("✗ NÃO ENCONTRADO no banco")

# Buscar por código 1118
print("\n" + "="*60)
print("BUSCANDO POR CÓDIGO '1118':")
print("="*60)
cursor.execute("SELECT id, nome FROM projects WHERE nome LIKE '%1118%'")
results = cursor.fetchall()
if results:
    for r in results:
        print(f"✓ ID={r[0]}, Nome={r[1]}")
else:
    print("✗ Nenhum projeto com '1118' no nome")

# Total de projetos
print("\n" + "="*60)
print("ESTATÍSTICAS:")
print("="*60)
cursor.execute('SELECT COUNT(*) FROM projects')
total = cursor.fetchone()[0]
print(f"Total de projetos no banco: {total}")

cursor.execute('SELECT COUNT(*) FROM fases')
fases = cursor.fetchone()[0]
print(f"Total de fases no banco: {fases}")

# Últimos 10 projetos inseridos
print("\n" + "="*60)
print("ÚLTIMOS 10 PROJETOS INSERIDOS:")
print("="*60)
cursor.execute('SELECT id, nome FROM projects ORDER BY id DESC LIMIT 10')
for i, row in enumerate(cursor.fetchall(), 1):
    print(f"{i}. {row[1]} (ID: {row[0]})")

conn.close()
