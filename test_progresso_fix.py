#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste para verificar o mapeamento correto das fases de progresso.
Testa especificamente o projeto 2376502000002326783 com "Implantação  RIS" (2 espaços).
"""

import sqlite3
import re

def testar_mapeamento_fases():
    """Simula a lógica do endpoint para verificar o mapeamento."""
    
    # Conectar ao banco
    conn = sqlite3.connect('zoho_cache.db')
    cursor = conn.cursor()
    
    # Buscar fases do projeto específico
    project_id = '2376502000002326783'
    cursor.execute("""
        SELECT nome, percentual_conclusao 
        FROM fases 
        WHERE projeto_id = ?
    """, (project_id,))
    
    fases = cursor.fetchall()
    conn.close()
    
    print(f"=== TESTE DE MAPEAMENTO DE FASES ===")
    print(f"Projeto ID: {project_id}\n")
    
    # Inicializar resultado
    resultado = {
        'NR': None,
        'AP': None,
        'IMP': None,
        'INT': None
    }
    
    print("Fases encontradas no banco:")
    for fase in fases:
        nome_fase = (fase[0] or '').strip()
        percentual = fase[1] if fase[1] is not None else 0
        
        # Garantir que o percentual seja um número entre 0 e 100
        try:
            percentual = float(percentual)
            percentual = max(0, min(100, percentual))
        except (ValueError, TypeError):
            percentual = 0
        
        # Normalizar o nome da fase
        nome_normalizado = re.sub(r'^\d+\s*-\s*', '', nome_fase)
        nome_normalizado = re.sub(r'\s+', ' ', nome_normalizado)
        nome_normalizado = nome_normalizado.lower()
        
        print(f"\n  Nome original: '{nome_fase}'")
        print(f"  Nome normalizado: '{nome_normalizado}'")
        print(f"  Percentual: {percentual}%")
        
        # Testar mapeamentos
        mapeado = False
        if 'implanta' in nome_normalizado and 'ris' in nome_normalizado:
            resultado['NR'] = round(percentual, 1)
            print(f"  ✅ MAPEADO -> NR (Implantação RIS)")
            mapeado = True
        elif 'implanta' in nome_normalizado and 'pacs' in nome_normalizado:
            resultado['AP'] = round(percentual, 1)
            print(f"  ✅ MAPEADO -> AP (Implantação PACS)")
            mapeado = True
        elif 'importa' in nome_normalizado:
            resultado['IMP'] = round(percentual, 1)
            print(f"  ✅ MAPEADO -> IMP (Importação)")
            mapeado = True
        elif 'integra' in nome_normalizado:
            resultado['INT'] = round(percentual, 1)
            print(f"  ✅ MAPEADO -> INT (Integração)")
            mapeado = True
        
        if not mapeado:
            print(f"  ⚠️  NÃO MAPEADO (fase ignorada)")
    
    print("\n" + "="*60)
    print("RESULTADO FINAL (o que será exibido no card):")
    print("="*60)
    for key, value in resultado.items():
        label = {
            'NR': 'Implantação RIS',
            'AP': 'Implantação PACS',
            'IMP': 'Importação',
            'INT': 'Integração'
        }[key]
        
        if value is not None:
            print(f"  {key} ({label}): {value}% ✅")
        else:
            print(f"  {key} ({label}): Não disponível ❌")
    
    print("\n" + "="*60)
    print("VERIFICAÇÃO FINAL:")
    print("="*60)
    
    # Verificar se "Implantação RIS" foi mapeada corretamente
    if resultado['NR'] == 74.0:
        print("✅ SUCESSO: Implantação RIS (74%) foi mapeada corretamente para NR!")
    else:
        print(f"❌ ERRO: Implantação RIS deveria ser 74%, mas NR = {resultado['NR']}")
    
    if resultado['AP'] == 68.0:
        print("✅ SUCESSO: Implantação PACS (68%) foi mapeada corretamente para AP!")
    else:
        print(f"❌ ERRO: Implantação PACS deveria ser 68%, mas AP = {resultado['AP']}")
    
    if resultado['IMP'] == 40.0:
        print("✅ SUCESSO: Importação (40%) foi mapeada corretamente para IMP!")
    else:
        print(f"❌ ERRO: Importação deveria ser 40%, mas IMP = {resultado['IMP']}")
    
    if resultado['INT'] == 100.0:
        print("✅ SUCESSO: Integração (100%) foi mapeada corretamente para INT!")
    else:
        print(f"❌ ERRO: Integração deveria ser 100%, mas INT = {resultado['INT']}")
    
    return resultado

if __name__ == '__main__':
    testar_mapeamento_fases()
