"""
Verificação de usos restantes de full_data_json
Identifica quais podem ser substituídos facilmente
"""
import re

print("\n" + "="*70)
print("🔍 ANÁLISE DE USOS RESTANTES DE full_data_json")
print("="*70)

usos_restantes = {
    "Linha 920-921 - /mover_projeto": {
        "codigo": "detalhes_zoho = json.loads(full_data_json) if full_data_json else {}",
        "uso": "Usado para múltiplas operações de movimentação",
        "complexidade": "⚠️ ALTA - precisa análise detalhada",
        "campos_usados": "Precisa investigação do que é extraído de detalhes_zoho",
        "acao": "Analisar linha por linha o que é usado"
    },
    "Linha 1829 - /iniciar_implantacao": {
        "codigo": "detalhes_zoho = json.loads(project_row.full_data_json)",
        "uso": "proj_name = detalhes_zoho.get('name', '') para extrair cliente",
        "complexidade": "✅ BAIXA - pode usar project_name/client_name",
        "campos_usados": "name (para extrair cliente)",
        "acao": "Substituir por project_row.project_name e project_row.client_name"
    },
    "Linha 2342 - /agendar_homologacao": {
        "codigo": "detalhes_zoho = json.loads(project_row.full_data_json)",
        "uso": "proj_name = detalhes_zoho.get('name', '') para extrair cliente",
        "complexidade": "✅ BAIXA - pode usar project_name/client_name",
        "campos_usados": "name (para extrair cliente)",
        "acao": "Substituir por project_row.project_name e project_row.client_name"
    },
    "Linha 2597 - /agendar_virada": {
        "codigo": "detalhes_zoho = json.loads(project_row.full_data_json)",
        "uso": "proj_name = detalhes_zoho.get('name', '') para extrair cliente",
        "complexidade": "✅ BAIXA - pode usar project_name/client_name",
        "campos_usados": "name (para extrair cliente)",
        "acao": "Substituir por project_row.project_name e project_row.client_name"
    },
    "Linha 2850 - /concluir_virada": {
        "codigo": "detalhes_zoho = json.loads(project_row.full_data_json)",
        "uso": "proj_name = detalhes_zoho.get('name', '') para extrair cliente",
        "complexidade": "✅ BAIXA - pode usar project_name/client_name",
        "campos_usados": "name (para extrair cliente)",
        "acao": "Substituir por project_row.project_name e project_row.client_name"
    }
}

print("\n📊 RESUMO:")
print(f"   Total de usos restantes: {len(usos_restantes)}")

baixa = sum(1 for u in usos_restantes.values() if "BAIXA" in u['complexidade'])
alta = sum(1 for u in usos_restantes.values() if "ALTA" in u['complexidade'])

print(f"   ✅ Complexidade BAIXA (fácil): {baixa}")
print(f"   ⚠️  Complexidade ALTA (precisa análise): {alta}")

print("\n" + "="*70)
print("✅ USOS FÁCEIS DE SUBSTITUIR (PRÓXIMA AÇÃO)")
print("="*70)

for endpoint, info in usos_restantes.items():
    if "BAIXA" in info['complexidade']:
        print(f"\n📍 {endpoint}")
        print(f"   Campos usados: {info['campos_usados']}")
        print(f"   Ação: {info['acao']}")

print("\n" + "="*70)
print("⚠️  USOS COMPLEXOS (ANÁLISE NECESSÁRIA)")
print("="*70)

for endpoint, info in usos_restantes.items():
    if "ALTA" in info['complexidade']:
        print(f"\n📍 {endpoint}")
        print(f"   Uso: {info['uso']}")
        print(f"   Ação: {info['acao']}")

print("\n" + "="*70)
print("💡 RECOMENDAÇÃO: ETAPA 2")
print("="*70)
print("\n1. Substituir os 4 endpoints fáceis (iniciar_implantacao, agendar_homologacao, agendar_virada, concluir_virada)")
print("2. Testar cada substituição")
print("3. Depois analisar /mover_projeto em profundidade")
print("\nEstimativa: 15-20 minutos para os 4 fáceis")
print()
