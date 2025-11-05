"""
Validação reversa para Falta Liberar Servidor Infra
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Project
import utils

# IDs dos 8 projetos corretos que você vê no Zoho com status "Aberto" + tag "Aguardando Infra"
# IMPORTANTE: Você precisa fornecer esses IDs corretos
print("="*100)
print("🔍 VALIDAÇÃO REVERSA: Falta Liberar Servidor Infra")
print("="*100)
print()
print("⚠️  ATENÇÃO: Você mencionou que no Zoho tem 8 projetos com:")
print("   - Status: Aberto")
print("   - Tag: Aguardando Infra")
print()
print("Mas o script encontrou 13 projetos. Vamos descobrir os 5 extras.")
print()

db_url = input("📝 Cole a URL do PostgreSQL do Railway: ").strip()

if not db_url:
    print("\n❌ URL do banco é obrigatória!")
    sys.exit(1)

# Conecta ao banco
print(f"\n💾 Conectando ao banco de dados...")
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

# Busca TODOS os projetos do banco
print(f"\n📊 Buscando todos os projetos do banco...")
all_projects = session.query(Project).all()

# Filtra projetos que aparecem em "Falta Liberar Servidor Infra"
print(f"\n🔍 Filtrando projetos classificados como 'Falta Liberar Servidor Infra'...")
projetos_banco_nesta_coluna = []

for project in all_projects:
    coluna_determinada = utils.determinar_coluna_projeto_from_db(project)
    if coluna_determinada == "Falta Liberar Servidor Infra":
        projetos_banco_nesta_coluna.append(project)

print(f"✅ Projetos no banco classificados como 'Falta Liberar Servidor Infra': {len(projetos_banco_nesta_coluna)}")

# Lista todos os projetos
print(f"\n{'='*100}")
print("📋 LISTA COMPLETA DE PROJETOS NESTA COLUNA")
print("="*100)
print()

for idx, project in enumerate(projetos_banco_nesta_coluna, 1):
    print(f"{idx}. {project.nome}")
    print(f"   ID: {project.id}")
    print(f"   status_id: {project.status_id}")
    print(f"   status_atual: {project.status_atual}")
    
    # Parse tags
    if project.tags:
        try:
            tags_parsed = json.loads(project.tags)
            tag_ids = [str(tag.get('id')) for tag in tags_parsed if isinstance(tag, dict)]
            tag_names = [tag.get('name', 'Sem nome') for tag in tags_parsed if isinstance(tag, dict)]
            print(f"   tags: {tag_names} (IDs: {tag_ids})")
        except:
            print(f"   tags: {project.tags[:100]}")
    else:
        print(f"   tags: (sem tags)")
    print()

session.close()

print("="*100)
print("📊 ANÁLISE")
print("="*100)
print(f"Total no banco: {len(projetos_banco_nesta_coluna)}")
print(f"Esperado (Zoho): 8")
print(f"Diferença: {len(projetos_banco_nesta_coluna) - 8} projetos extras")
print()
print("💡 Verifique na lista acima quais são os projetos extras e copie os IDs para sincronizar")
