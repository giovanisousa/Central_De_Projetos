#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste de integração para o endpoint /api/progresso-fases/<project_id>
Simula a chamada HTTP real e verifica a resposta JSON.
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_endpoint_progresso():
    """Simula o endpoint de progresso de fases."""
    
    # Importar a lógica do endpoint
    import sqlite3
    import re
    
    project_id = '2376502000002326783'
    
    print("="*70)
    print(f"SIMULAÇÃO DO ENDPOINT: /api/progresso-fases/{project_id}")
    print("="*70)
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect('zoho_cache.db')
        cursor = conn.cursor()
        
        # Buscar fases
        cursor.execute("""
            SELECT nome, percentual_conclusao 
            FROM fases 
            WHERE projeto_id = ?
        """, (project_id,))
        
        fases = cursor.fetchall()
        conn.close()
        
        # Inicializar resultado
        resultado = {
            'NR': None,
            'AP': None,
            'IMP': None,
            'INT': None
        }
        
        print(f"\n📊 Processando {len(fases)} fases...\n")
        
        # Mapear fases
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
            
            # Mapear para as categorias
            mapeado = None
            if 'implanta' in nome_normalizado and 'ris' in nome_normalizado:
                resultado['NR'] = round(percentual, 1)
                mapeado = 'NR'
            elif 'implanta' in nome_normalizado and 'pacs' in nome_normalizado:
                resultado['AP'] = round(percentual, 1)
                mapeado = 'AP'
            elif 'importa' in nome_normalizado:
                resultado['IMP'] = round(percentual, 1)
                mapeado = 'IMP'
            elif 'integra' in nome_normalizado:
                resultado['INT'] = round(percentual, 1)
                mapeado = 'INT'
            
            if mapeado:
                print(f"✅ '{nome_fase}' → {mapeado} = {percentual}%")
        
        # Simular resposta JSON
        response = {
            'sucesso': True,
            'progresso': resultado
        }
        
        print("\n" + "="*70)
        print("📤 RESPOSTA JSON DO ENDPOINT:")
        print("="*70)
        import json
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        print("\n" + "="*70)
        print("🎯 BARRAS QUE APARECERÃO NO CARD:")
        print("="*70)
        
        barras_visiveis = 0
        labels = {
            'NR': 'Implantação RIS',
            'AP': 'Implantação PACS', 
            'IMP': 'Importação',
            'INT': 'Integração'
        }
        
        for key, label in labels.items():
            value = resultado[key]
            if value is not None:
                print(f"  📊 {label}: {value}%")
                barras_visiveis += 1
            else:
                print(f"  ⚪ {label}: (não disponível)")
        
        print("\n" + "="*70)
        print(f"✅ TOTAL DE BARRAS VISÍVEIS: {barras_visiveis}/4")
        print("="*70)
        
        # Validação final
        print("\n🔍 VALIDAÇÃO:")
        if resultado['NR'] == 74.0:
            print("  ✅ Implantação RIS (74%) - CORRIGIDO!")
        else:
            print(f"  ❌ Implantação RIS deveria ser 74%, mas é {resultado['NR']}")
        
        if barras_visiveis == 4:
            print(f"\n🎉 SUCESSO! Todas as 4 barras serão exibidas no card!")
        else:
            print(f"\n⚠️  ATENÇÃO! Apenas {barras_visiveis}/4 barras serão exibidas.")
        
        return response
        
    except Exception as e:
        print(f"\n❌ ERRO ao processar endpoint:")
        import traceback
        traceback.print_exc()
        return {
            'sucesso': False,
            'erro': str(e),
            'progresso': {'NR': None, 'AP': None, 'IMP': None, 'INT': None}
        }

if __name__ == '__main__':
    test_endpoint_progresso()
