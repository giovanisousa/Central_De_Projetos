#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SOLUÇÃO DEFINITIVA - Sincronização Completa Resistente a Falhas
================================================================

Este script é otimizado para sincronização longa sem problemas de timeout:
- Não mantém sessões abertas (cria nova sessão para cada operação)
- Processa projetos individualmente
- Sincroniza: Projetos → Fases → Listas → Tarefas
- Continua de onde parou em caso de erro
"""

import os
import time
import requests
from dotenv import load_dotenv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Importações
from sync_zoho import obter_access_token_zoho, sync_fases, sync_listas_e_tarefas, synchronize_projects
from database import Session, Project, Fase

print("\n" + "="*80)
print("  SINCRONIZAÇÃO COMPLETA - MODO SEGURO")
print("  Resistente a timeout de conexão SSL")
print("="*80 + "\n")

# Função auxiliar para queries seguras (não mantém sessão aberta)
def contar_safe(model):
    """Conta registros sem manter sessão aberta"""
    session = Session()
    try:
        count = session.query(model).count()
        return count
    finally:
        try:
            session.close()
        except:
            pass

def get_projetos_safe():
    """Busca lista de projetos sem manter sessão aberta"""
    session = Session()
    try:
        projetos = session.query(Project).all()
        # Extrair apenas IDs e nomes para não manter objetos ligados à sessão
        resultado = [(p.id, p.nome) for p in projetos]
        return resultado
    finally:
        try:
            session.close()
        except:
            pass

# Estado inicial
print("[ETAPA 1] SINCRONIZAR PROJETOS DO ZOHO")
print("="*80)
projetos_antes = contar_safe(Project)
fases_antes = contar_safe(Fase)

print(f"Estado ANTES:")
print(f"  - Projetos: {projetos_antes}")
print(f"  - Fases: {fases_antes}")
print()

input("Pressione ENTER para iniciar sincronização de projetos...")

try:
    print("\n[Sincronizando projetos...]")
    synchronize_projects()
    print("[OK] Projetos sincronizados!")
except Exception as e:
    print(f"[AVISO] Erro ao sincronizar projetos: {e}")
    print("Continuando com projetos existentes...")

# Atualizar contadores
projetos_depois = contar_safe(Project)
print(f"\nProjetos no banco: {projetos_depois}")

# ETAPA 2: Sincronizar fases de cada projeto INDIVIDUALMENTE
print("\n" + "="*80)
print("[ETAPA 2] SINCRONIZAR FASES DE CADA PROJETO")
print("="*80)
print(f"Total de projetos a processar: {projetos_depois}")
print()

input("Pressione ENTER para iniciar sincronização de fases...")

# Buscar lista de projetos
projetos_lista = get_projetos_safe()
total = len(projetos_lista)

# Obter access token UMA VEZ (vamos renovar se necessário)
access_token = obter_access_token_zoho()
token_time = time.time()

sucessos = 0
falhas = 0
fases_sincronizadas = 0

print(f"\nProcessando {total} projetos (2s entre cada)...\n")

for idx, (project_id, project_name) in enumerate(projetos_lista, 1):
    # Renovar token a cada 15 minutos (mais conservador)
    if time.time() - token_time > 900:  # 15 minutos
        print("\n  [INFO] Renovando access token do Zoho...")
        try:
            access_token = obter_access_token_zoho()
            token_time = time.time()
            print("  [OK] Token renovado!\n")
        except Exception as e:
            print(f"  [ERRO] Falha ao renovar token: {e}")
            print("  Continuando com token atual...\n")
    
    try:
        print(f"[{idx}/{total}] {project_name or 'Sem nome'} (ID: {project_id})")
        
        # Sincronizar fases deste projeto
        fases = []
        max_retries = 3
        for attempt in range(max_retries):
            try:
                fases = sync_fases(project_id, access_token)
                break  # Sucesso, sai do loop
            except requests.exceptions.HTTPError as http_err:
                if '401' in str(http_err):  # Token expirado
                    print(f"  [AVISO] Token expirado na tentativa {attempt+1}/{max_retries}. Renovando...")
                    access_token = obter_access_token_zoho()
                    token_time = time.time()
                    time.sleep(2)
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  [AVISO] Erro na tentativa {attempt+1}/{max_retries}: {e}")
                    time.sleep(2)
                else:
                    raise
        num_fases = len(fases)
        
        # Encontrar fase de impeditivos
        id_fase_impeditivos = None
        for fase in fases:
            if fase.get('name') == "00 - Itens impeditivos de virada":
                id_fase_impeditivos = fase.get('id')
                break
        
        # Sincronizar listas e tarefas
        sync_listas_e_tarefas(project_id, access_token, id_fase_impeditivos)
        
        print(f"  [OK] {num_fases} fases sincronizadas")
        sucessos += 1
        fases_sincronizadas += num_fases
        
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "INVALID_OAUTHTOKEN" in error_msg:
            print(f"  [ERRO] Token expirado! Renovando...")
            try:
                access_token = obter_access_token_zoho()
                token_time = time.time()
                print(f"  [OK] Token renovado. Tentando novamente...")
                
                # Retry
                fases = sync_fases(project_id, access_token)
                sync_listas_e_tarefas(project_id, access_token, id_fase_impeditivos)
                print(f"  [OK] Sucesso após renovar token")
                sucessos += 1
                fases_sincronizadas += len(fases)
            except Exception as retry_error:
                print(f"  [ERRO] Falhou mesmo após renovar token: {retry_error}")
                falhas += 1
        else:
            print(f"  [ERRO] {error_msg}")
            falhas += 1
    
    # Delay entre projetos (rate limit)
    if idx < total:
        time.sleep(2)
    
    # Mostrar progresso a cada 5 projetos
    if idx % 5 == 0 or idx == total:
        print(f"\n  [PROGRESSO] {idx}/{total} projetos | ✓ {sucessos} | ✗ {falhas} | {fases_sincronizadas} fases\n")

# Estatísticas finais
print("\n" + "="*80)
print("[CONCLUÍDO] SINCRONIZAÇÃO FINALIZADA")
print("="*80)

fases_final = contar_safe(Fase)
projetos_final = contar_safe(Project)

print(f"\nEstatísticas:")
print(f"  - Projetos processados: {total}")
print(f"  - Sucessos: {sucessos}")
print(f"  - Falhas: {falhas}")
print(f"  - Taxa de sucesso: {sucessos/total*100:.1f}%" if total > 0 else "  - Taxa: N/A")
print(f"\nEstado final do banco:")
print(f"  - Projetos: {projetos_antes} → {projetos_final} (+{projetos_final - projetos_antes})")
print(f"  - Fases: {fases_antes} → {fases_final} (+{fases_final - fases_antes})")
print(f"  - Média: {fases_final/projetos_final:.1f} fases/projeto" if projetos_final > 0 else "")
print("\n" + "="*80 + "\n")
