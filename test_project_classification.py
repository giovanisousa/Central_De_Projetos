"""
Testa a classificação do projeto 2376502000003330185
após remover status "Aberto" do fallback
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Project
from utils import determinar_coluna_projeto_from_db

PROJECT_ID = '2376502000003330185'

db_url = input("📝 Cole a URL do PostgreSQL: ").strip()

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

project = session.query(Project).filter(Project.id == PROJECT_ID).first()

if not project:
    print(f"\n❌ Projeto {PROJECT_ID} não encontrado no banco!")
else:
    print(f"\n✅ Projeto encontrado: {project.nome}")
    print(f"   Status ID: {project.status_id}")
    print(f"   Status Atual: {project.status_atual}")
    print(f"   Tags: {project.tags}")
    
    coluna = determinar_coluna_projeto_from_db(project)
    print(f"\n📍 Coluna determinada: {coluna}")
    
    if coluna == "Status Desconhecido":
        print("   ✅ CORRETO - Projeto com status 'Aberto' + tag 'Implantação' vai para 'Status Desconhecido'")
    else:
        print(f"   ❌ INCORRETO - Esperava 'Status Desconhecido' mas obteve '{coluna}'")

session.close()
