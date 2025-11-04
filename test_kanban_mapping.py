"""
Script para testar mapeamento de projetos para colunas Kanban
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Project
import utils

# ✅ Conexão com Railway PostgreSQL (externa)
DATABASE_URL = input("Cole a URL do PostgreSQL do Railway: ").strip()

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("\n" + "="*80)
print("🧪 TESTE DE MAPEAMENTO KANBAN")
print("="*80)

# Projetos de teste
test_projects = [
    '2376502000002326783',  # Deve ser "Em Operação Assistida"
]

print("\n📋 Buscando projetos de teste no banco...")

for project_id in test_projects:
    project = session.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        print(f"\n❌ Projeto {project_id} não encontrado no banco")
        continue
    
    print(f"\n{'='*80}")
    print(f"🔍 Projeto: {project.nome}")
    print(f"   ID: {project.id}")
    print(f"   status_id: {project.status_id}")
    print(f"   status_atual: {project.status_atual}")
    print(f"   tags (primeiros 200 chars): {(project.tags or '')[:200]}")
    
    # Testa mapeamento
    coluna_kanban = utils.determinar_coluna_projeto_from_db(project)
    
    print(f"\n📍 Resultado do mapeamento:")
    print(f"   Coluna Kanban: {coluna_kanban}")
    print(f"   ✅ CORRETO!" if coluna_kanban == "Em Operação Assistida" else f"   ❌ INCORRETO! Esperado: 'Em Operação Assistida'")

# Agora busca TODOS os projetos "Em Operação Assistida" no Zoho
print(f"\n{'='*80}")
print("🔍 Buscando TODOS os projetos com status 'Operação Assistida' no banco...")

projects_oa = session.query(Project).filter(
    Project.status_id == '2376502000000020119'
).all()

print(f"\n📊 Total de projetos com status_id='2376502000000020119': {len(projects_oa)}")

for idx, project in enumerate(projects_oa[:10], 1):  # Mostra apenas os 10 primeiros
    coluna = utils.determinar_coluna_projeto_from_db(project)
    status_icon = "✅" if coluna == "Em Operação Assistida" else "❌"
    print(f"{status_icon} {idx}. {project.nome}")
    print(f"      status_atual: {project.status_atual}")
    print(f"      tags (primeiros 100 chars): {(project.tags or '')[:100]}")
    print(f"      -> Coluna Kanban: {coluna}")

# Projetos "Em Virada"
print(f"\n{'='*80}")
print("🔍 Buscando projetos 'Em Virada' (status_id=2376502000000020092 + tag=2376502000001228741)...")

projects_virada = session.query(Project).filter(
    Project.status_id == '2376502000000020092'
).all()

print(f"\n📊 Total de projetos com status_id='2376502000000020092': {len(projects_virada)}")

virada_corretos = 0
for project in projects_virada[:5]:  # Mostra apenas os 5 primeiros
    coluna = utils.determinar_coluna_projeto_from_db(project)
    
    # Verifica se tem a tag de virada
    import json
    tem_tag_virada = False
    if project.tags:
        try:
            tags_parsed = json.loads(project.tags)
            for tag in tags_parsed:
                if isinstance(tag, dict) and tag.get('id') == '2376502000001228741':
                    tem_tag_virada = True
                    break
        except:
            pass
    
    status_icon = "✅" if (tem_tag_virada and coluna == "Em Virada") or (not tem_tag_virada and coluna != "Em Virada") else "❌"
    print(f"{status_icon} {project.nome}")
    print(f"      status_atual: {project.status_atual}")
    print(f"      Tem tag virada: {tem_tag_virada}")
    print(f"      -> Coluna Kanban: {coluna}")
    
    if (tem_tag_virada and coluna == "Em Virada") or (not tem_tag_virada and coluna != "Em Virada"):
        virada_corretos += 1

print(f"\n📊 Projetos mapeados corretamente: {virada_corretos}/{min(5, len(projects_virada))}")

session.close()
print("\n" + "="*80)
print("✅ Teste concluído!")
print("="*80)
