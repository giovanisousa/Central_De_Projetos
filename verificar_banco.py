#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar estado atual do banco Neon
"""

import os
from dotenv import load_dotenv

load_dotenv()

from database import Session, Project, Fase

try:
    session = Session()
    
    # Contar projetos
    total_projetos = session.query(Project).count()
    total_fases = session.query(Fase).count()
    
    print("="*60)
    print("[STATUS] Estado atual do banco Neon:")
    print("="*60)
    print(f"Total de projetos: {total_projetos}")
    print(f"Total de fases: {total_fases}")
    
    if total_projetos > 0:
        print("\n[PROJETOS] Ultimos 10 projetos inseridos:")
        projetos = session.query(Project).order_by(Project.id.desc()).limit(10).all()
        for p in projetos:
            print(f"  - {p.nome} (ID: {p.id})")
    
    session.close()
    print("="*60)
    
except Exception as e:
    print(f"[ERRO] ao conectar no banco: {e}")
