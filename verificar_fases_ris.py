import sqlite3

conn = sqlite3.connect('zoho_cache.db')
cursor = conn.cursor()

# Buscar todas as fases distintas
cursor.execute('SELECT DISTINCT nome FROM fases ORDER BY nome')
fases = cursor.fetchall()

print('=' * 70)
print('TODAS AS FASES DISTINTAS NO BANCO DE DADOS:')
print('=' * 70)
for f in fases:
    print(f'  {f[0]}')

print('\n' + '=' * 70)
print('FASES QUE CONTÊM "RIS":')
print('=' * 70)
fases_ris = [f for f in fases if 'RIS' in f[0].upper()]
for f in fases_ris:
    print(f'  {f[0]}')

print('\n' + '=' * 70)
print('FASES QUE CONTÊM "PACS":')
print('=' * 70)
fases_pacs = [f for f in fases if 'PACS' in f[0].upper()]
for f in fases_pacs:
    print(f'  {f[0]}')

print('\n' + '=' * 70)
print('ANÁLISE DE SOBREPOSIÇÃO:')
print('=' * 70)

# Verificar se há fases RIS que podem se sobrepor
print('\nFases RIS que podem causar sobreposição:')
implantacao_ris = [f for f in fases_ris if 'IMPLANTAÇÃO' in f[0].upper() or 'IMPLANTACAO' in f[0].upper()]
outras_ris = [f for f in fases_ris if 'IMPLANTAÇÃO' not in f[0].upper() and 'IMPLANTACAO' not in f[0].upper()]

print(f'\n  Fases de Implantação RIS ({len(implantacao_ris)}):')
for f in implantacao_ris:
    print(f'    - {f[0]}')

print(f'\n  Outras fases com RIS ({len(outras_ris)}):')
for f in outras_ris:
    print(f'    - {f[0]}')

if len(outras_ris) > 0:
    print('\n  ⚠️  ATENÇÃO: Há outras fases com "RIS" além da Implantação!')
    print('     Isso PODE causar sobreposição se não forem específicas.')
else:
    print('\n  ✅ OK: Apenas fases de Implantação contêm "RIS".')

# Verificar se há fases PACS que podem se sobrepor
print('\n\nFases PACS que podem causar sobreposição:')
implantacao_pacs = [f for f in fases_pacs if 'IMPLANTAÇÃO' in f[0].upper() or 'IMPLANTACAO' in f[0].upper()]
outras_pacs = [f for f in fases_pacs if 'IMPLANTAÇÃO' not in f[0].upper() and 'IMPLANTACAO' not in f[0].upper()]

print(f'\n  Fases de Implantação PACS ({len(implantacao_pacs)}):')
for f in implantacao_pacs:
    print(f'    - {f[0]}')

print(f'\n  Outras fases com PACS ({len(outras_pacs)}):')
for f in outras_pacs:
    print(f'    - {f[0]}')

if len(outras_pacs) > 0:
    print('\n  ⚠️  ATENÇÃO: Há outras fases com "PACS" além da Implantação!')
    print('     Isso PODE causar sobreposição se não forem específicas.')
else:
    print('\n  ✅ OK: Apenas fases de Implantação contêm "PACS".')

conn.close()
