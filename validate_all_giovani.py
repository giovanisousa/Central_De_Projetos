"""
Valida todas as colunas do mapeamento para o proprietário Giovani (zpuid)
Gera um resumo por coluna com quantos projetos incorretos e lista de IDs a sincronizar.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_column import validar_coluna

GIOVANI_ZPUID = '2376502000000057291'

def main():
    mapeamento_path = os.path.join(os.path.dirname(__file__), 'mapeamento_colunas.json')
    with open(mapeamento_path, 'r', encoding='utf-8') as f:
        mapeamento = json.load(f)

    db_url = input("📝 Cole a URL do PostgreSQL do Railway: ").strip()
    if not db_url:
        print("\n❌ URL do banco é obrigatória!")
        sys.exit(1)

    summary = {}
    all_incorrect_ids = []

    for coluna in mapeamento.keys():
        print('\n' + '='*80)
        print(f"Validando coluna: {coluna}")
        print('='*80)
        incorrect = validar_coluna(coluna, db_url, owner_zpuid=GIOVANI_ZPUID)
        summary[coluna] = len(incorrect)
        all_incorrect_ids.extend([p['id'] for p in incorrect])

    print('\n' + '='*80)
    print('RESUMO GERAL (filtro: Giovani)')
    print('='*80)
    for coluna, count in summary.items():
        print(f" - {coluna}: {count} incorretos")

    unique_ids = sorted(list(set(all_incorrect_ids)))
    print('\nTotal de IDs únicos que precisam sincronização:', len(unique_ids))
    if unique_ids:
        for _id in unique_ids:
            print('  -', _id)

if __name__ == '__main__':
    main()
