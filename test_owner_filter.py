"""
Teste de validação da FASE 1: Colunas normalizadas
Verifica se o filtro GP está usando owner_zpuid corretamente
"""
import os
from dotenv import load_dotenv
from database import Session, Project

load_dotenv()

# IDs dos GPs (mesmos usados em routes/api.py)
DONOS_PROJETO = {
    "Giovani Sousa": "2376502000000057291",
    "Willian Jesus": "2376502000000057285"
}

def test_owner_filter():
    """Testa o filtro de owner_zpuid"""
    print("\n" + "="*70)
    print("🧪 TESTE: Filtro por owner_zpuid")
    print("="*70)
    
    session = Session()
    try:
        # Teste 1: Contar total de projetos
        total = session.query(Project).count()
        print(f"\n[1/4] Total de projetos no banco: {total}")
        
        # Teste 2: Contar projetos do Giovani
        giovani_zpuid = DONOS_PROJETO["Giovani Sousa"]
        projetos_giovani = session.query(Project).filter(
            Project.owner_zpuid == str(giovani_zpuid)
        ).all()
        print(f"[2/4] Projetos do Giovani (zpuid={giovani_zpuid}): {len(projetos_giovani)}")
        
        # Teste 3: Contar projetos do Willian
        willian_zpuid = DONOS_PROJETO["Willian Jesus"]
        projetos_willian = session.query(Project).filter(
            Project.owner_zpuid == str(willian_zpuid)
        ).all()
        print(f"[3/4] Projetos do Willian (zpuid={willian_zpuid}): {len(projetos_willian)}")
        
        # Teste 4: Verificar se a soma bate
        soma = len(projetos_giovani) + len(projetos_willian)
        print(f"[4/4] Soma (Giovani + Willian): {soma}")
        
        print("\n" + "="*70)
        print("📊 RESULTADO")
        print("="*70)
        
        if soma == total:
            print("✅ SUCESSO! Todos os projetos têm owner_zpuid válido")
            print(f"   - {len(projetos_giovani)} projetos do Giovani ({len(projetos_giovani)*100//total}%)")
            print(f"   - {len(projetos_willian)} projetos do Willian ({len(projetos_willian)*100//total}%)")
        else:
            print(f"⚠️  ATENÇÃO! {total - soma} projetos sem owner_zpuid ou com owner diferente")
            
            # Listar projetos sem owner
            projetos_sem_owner = session.query(Project).filter(
                Project.owner_zpuid == None
            ).all()
            print(f"\n   Projetos sem owner_zpuid: {len(projetos_sem_owner)}")
            
            # Listar owners diferentes
            outros_owners = session.query(Project).filter(
                ~Project.owner_zpuid.in_([str(giovani_zpuid), str(willian_zpuid)])
            ).all()
            print(f"   Projetos com outros owners: {len(outros_owners)}")
            
            if outros_owners:
                print("\n   Outros owners encontrados:")
                for p in outros_owners[:5]:  # Mostra apenas 5
                    print(f"     - {p.id}: owner_zpuid={p.owner_zpuid}, owner_name={p.owner_name}")
        
        # Teste 5: Verificar algumas propriedades
        print("\n" + "="*70)
        print("🔍 AMOSTRA DE DADOS (3 projetos do Giovani)")
        print("="*70)
        
        for i, p in enumerate(projetos_giovani[:3], 1):
            print(f"\n[{i}] Projeto: {p.project_name}")
            print(f"    ID: {p.id}")
            print(f"    Owner ZPUID: {p.owner_zpuid}")
            print(f"    Owner Name: {p.owner_name}")
            print(f"    Client Name: {p.client_name}")
            print(f"    Status: {p.status_atual}")
        
        print("\n" + "="*70)
        print("✅ TESTE CONCLUÍDO!")
        print("="*70)
        
    finally:
        session.close()

if __name__ == '__main__':
    test_owner_filter()
